"""The house's distribution board (Unterverteilung): main switch, two RCDs and
one miniature circuit breaker (MCB) per circuit.

Breakers trip like real ones:
- thermal (overload): a heat state follows (I/In)² with a 3 minute time
  constant and trips at 1.69 (1.3²). IEC 60898 asks for no trip at 1.13 In
  and a trip within an hour at 1.45 In; this model never trips at 1.13 In,
  takes about 5 minutes at 1.45 In and under a minute at 2.55 In.
- magnetic (short circuit): instantly at 5 × In for type B, 10 × In for C.
An RCD trips when the leakage current behind it reaches 70 % of its rated
30 mA (the standard demands a trip between 50 and 100 %).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

V_PHASE = 230.0
V_LINE = 400.0
MOTOR_PF = 0.95  # compressor inverter on the supply side
THERMAL_TAU_S = 180.0
THERMAL_TRIP = 1.69
MAGNETIC = {"B": 5.0, "C": 10.0}
RCD_TRIP_FRACTION = 0.7
SHORT_CIRCUIT_A = 600.0
OVERLOAD_W = 5000.0  # fan heater and kettle on one socket circuit
INSULATION_LEAK_A = 0.05  # 50 mA through a damaged heating element


@dataclass
class Breaker:
    id: str
    name: tuple[str, str]  # (German, English)
    rating_a: float
    char: str  # "B" or "C"
    phases: tuple[int, ...]  # 0..2 for L1..L3
    rcd: str
    closed: bool = True
    trip: str = ""  # "", "overload", "short"
    heat: float = 0.0
    current_a: float = 0.0
    power_w: float = 0.0

    def step(self, current_a: float, dt: float) -> None:
        self.current_a = current_a if self.closed else 0.0
        if self.closed and self.current_a >= MAGNETIC[self.char] * self.rating_a:
            # The magnetic release opens within milliseconds, before the bimetal warms.
            self.open("short")
            return
        k = self.current_a / self.rating_a
        self.heat += (k * k - self.heat) * min(1.0, dt / THERMAL_TAU_S)
        if self.closed and self.heat >= THERMAL_TRIP:
            self.open("overload")

    def open(self, reason: str) -> None:
        self.closed, self.trip = False, reason
        self.current_a = self.power_w = 0.0


@dataclass
class Rcd:
    id: str
    name: tuple[str, str]
    rated_ma: float = 30.0
    closed: bool = True
    trip: str = ""  # "", "leak", "test"
    leak_ma: float = 0.0


@dataclass
class Board:
    rcds: dict[str, Rcd] = field(default_factory=dict)
    breakers: dict[str, Breaker] = field(default_factory=dict)
    phase_a: list[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    house_kwh: float = 0.0
    hp_kwh: float = 0.0
    # simulator faults
    short_circuit: bool = False  # in the living room sockets (F2)
    overload: bool = False  # extra 5 kW on the kitchen sockets (F3)
    insulation_fault: bool = False  # washing machine heater to earth (F5)
    events: list = field(default_factory=list)  # (kind, text) since the last read

    @classmethod
    def standard(cls) -> "Board":
        b = cls()
        b.rcds = {
            "Q1": Rcd("Q1", ("FI Haushalt", "RCD household")),
            "Q2": Rcd("Q2", ("FI Wärmepumpe", "RCD heat pump")),
        }
        for br in (
            Breaker("F1", ("Licht", "Lighting"), 10, "B", (0,), "Q1"),
            Breaker("F2", ("Steckdosen Wohnen", "Sockets living"), 16, "B", (0,), "Q1"),
            Breaker("F3", ("Steckdosen Küche", "Sockets kitchen"), 16, "B", (1,), "Q1"),
            Breaker("F4", ("Herd", "Cooker"), 16, "B", (0, 1, 2), "Q1"),
            Breaker("F5", ("Waschmaschine", "Washing machine"), 16, "B", (2,), "Q1"),
            Breaker("F6", ("Heizkreispumpe", "Circulation pump"), 10, "B", (1,), "Q1"),
            Breaker("F7", ("Wärmepumpe", "Heat pump"), 16, "C", (0, 1, 2), "Q2"),
            Breaker("F8", ("Heizstab", "Heating rod"), 16, "B", (0, 1, 2), "Q2"),
        ):
            b.breakers[br.id] = br
        return b

    # What the house gets ----------------------------------------------------

    def energized(self, breaker_id: str) -> bool:
        br = self.breakers[breaker_id]
        return br.closed and self.rcds[br.rcd].closed

    def rcd_tripped(self, rcd_id: str) -> bool:
        return bool(self.rcds[rcd_id].trip)

    def breaker_tripped(self, breaker_id: str) -> bool:
        return bool(self.breakers[breaker_id].trip)

    # Operator --------------------------------------------------------------

    def switch(self, device_id: str, close: bool) -> None:
        dev = self.rcds.get(device_id) or self.breakers.get(device_id)
        if dev is None:
            raise KeyError(device_id)
        if close and not dev.closed:
            dev.closed, dev.trip = True, ""
            self.events.append(("OPR", f"{device_id} switched on"))
        elif not close and dev.closed:
            dev.closed = False
            self.events.append(("OPR", f"{device_id} switched off"))

    def test_rcd(self, rcd_id: str) -> None:
        rcd = self.rcds[rcd_id]
        if rcd.closed:
            rcd.closed, rcd.trip = False, "test"
            self.events.append(("OPR", f"{rcd_id} test button: tripped"))

    # Physics ------------------------------------------------------------------

    def step(self, dt: float, minute: float, hp_w: float, rod_w: float, circ_w: float) -> None:
        loads = household_w(minute)
        loads.update({"F6": circ_w, "F7": hp_w, "F8": rod_w})
        if self.overload:
            loads["F3"] += OVERLOAD_W
        self.phase_a = [0.0, 0.0, 0.0]
        for br in self.breakers.values():
            live = self.rcds[br.rcd].closed and br.closed
            watts = loads.get(br.id, 0.0) if live else 0.0
            if len(br.phases) == 3:
                pf = MOTOR_PF if br.id == "F7" else 1.0
                amps = watts / (math.sqrt(3) * V_LINE * pf)
            else:
                amps = watts / V_PHASE
            if live and br.id == "F2" and self.short_circuit:
                amps = SHORT_CIRCUIT_A
            br.power_w = watts if br.closed else 0.0
            was = br.closed
            br.step(amps, dt)
            if was and not br.closed:
                why = "short circuit" if br.trip == "short" else "overload"
                self.events.append(("ALM", f"{br.id} tripped: {why}"))
            if br.closed and live:
                for ph in br.phases:
                    self.phase_a[ph] += amps
                if br.rcd == "Q1":
                    self.house_kwh += watts * dt / 3.6e6
                else:
                    self.hp_kwh += watts * dt / 3.6e6

        for rcd in self.rcds.values():
            leak = 0.0
            if rcd.id == "Q1" and self.insulation_fault and rcd.closed and self.breakers["F5"].closed:
                leak = INSULATION_LEAK_A
            rcd.leak_ma = leak * 1000
            if rcd.closed and rcd.leak_ma >= RCD_TRIP_FRACTION * rcd.rated_ma:
                rcd.closed, rcd.trip = False, "leak"
                self.events.append(("ALM", f"{rcd.id} tripped: leakage {rcd.leak_ma:.0f} mA"))

    def snapshot(self) -> dict:
        return {
            "rcds": [
                {"id": r.id, "name": list(r.name), "rated_ma": r.rated_ma, "closed": r.closed, "trip": r.trip,
                 "leak_ma": r.leak_ma}
                for r in self.rcds.values()
            ],
            "breakers": [
                {"id": b.id, "name": list(b.name), "rating": f"{b.char}{b.rating_a:g}", "phases": len(b.phases),
                 "phase": b.phases[0] + 1, "rcd": b.rcd, "closed": b.closed, "trip": b.trip,
                 "current_a": b.current_a, "power_w": b.power_w, "heat": b.heat / THERMAL_TRIP}
                for b in self.breakers.values()
            ],
            "phase_a": list(self.phase_a),
            "house_kwh": self.house_kwh,
            "hp_kwh": self.hp_kwh,
        }


def _between(minute: float, start_h: float, end_h: float) -> bool:
    return start_h * 60 <= minute < end_h * 60


def household_w(minute: float) -> dict[str, float]:
    """A plain weekday for two people, in watts per circuit."""
    light = 220.0 if _between(minute, 6, 8) or _between(minute, 17, 23) else 15.0
    living = 60.0 + (180.0 if _between(minute, 19, 23) else 0.0)  # router, standby, TV in the evening
    fridge = 90.0 if int(minute) % 30 < 12 else 5.0  # compressor cycles
    kettle = 2000.0 if any(_between(minute, h, h + 0.05) for h in (6.5, 13, 18.5)) else 0.0
    cooker = 3000.0 if _between(minute, 12, 12.75) or _between(minute, 18.5, 19.25) else 0.0
    if _between(minute, 10, 10.33):
        washer = 2000.0  # heating the water
    elif _between(minute, 10.33, 11.5):
        washer = 250.0
    else:
        washer = 0.0
    return {"F1": light, "F2": living, "F3": fridge + kettle, "F4": cooker, "F5": washer}
