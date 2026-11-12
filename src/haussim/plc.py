"""The heating controller. `scan()` runs once per cycle, like OB1 on a real PLC.

Inputs:  outside, room and buffer temperature; compressor and circulation
         pump running feedback; heat pump fault and defrost contacts;
         EVU lock signal from the grid operator.
Outputs: compressor enable, circulation pump, heating rod, fault reset pulse.

Alarms follow the ISA-18.2 life cycle, as in tanksim: an alarm comes in
unacknowledged and leaves the list once it has cleared and been acknowledged.
"""

from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass, field

MIN_RUN_S = 6 * 60.0  # compressor minimum run time
MIN_OFF_S = 10 * 60.0  # Taktsperre: minimum off time between starts
HP_FEEDBACK_S = 90.0  # the compressor ramps for 60 s, so allow more than that
CIRC_FEEDBACK_S = 10.0
DAMPING_S = 3 * 3600.0  # time constant of the damped outside temperature
FALLBACK_OUTSIDE_C = 0.0  # used while the outside sensor is broken
ROOM_GAIN = 2.0  # K flow target per K the room is below setpoint
FROST_ROOM_C = 7.0
FROST_BUFFER_C = 8.0
FROST_RELEASE_K = 3.0  # frost protection ends this far above both limits
ALARM_DEADBAND_K = 0.5

SENSOR_RANGE = {"outside": (-40.0, 60.0), "room": (0.0, 40.0), "buffer": (0.0, 95.0)}

DEFAULT_SETPOINTS = {
    "room_day": 21.0,
    "room_night": 19.0,  # heat pumps with floor heating: keep the setback at about 2 K
    "night_from": 22 * 60.0,  # minute of day
    "night_to": 6 * 60.0,
    "preheat": 120.0,  # minutes the day setpoint starts early (floor heating reacts slowly)
    "curve_slope": 0.4,  # Heizkurve Steilheit
    "curve_shift": 0.0,  # Parallelverschiebung
    "flow_min": 25.0,
    "flow_max": 50.0,
    "hysteresis": 2.0,  # K above and below the flow target
    "summer_cutoff": 17.0,
    "bivalent": -12.0,  # below this the rod helps the heat pump
    "buffer_high": 60.0,  # alarm limit
    "room_low": 16.0,  # alarm limit
}

# (min, max) for each setpoint the operator may change.
SETPOINT_LIMITS = {
    "room_day": (10.0, 26.0),
    "room_night": (10.0, 26.0),
    "night_from": (0.0, 1439.0),
    "night_to": (0.0, 1439.0),
    "preheat": (0.0, 240.0),
    "curve_slope": (0.1, 2.0),
    "curve_shift": (-5.0, 5.0),
    "flow_min": (20.0, 40.0),
    "flow_max": (30.0, 60.0),
    "hysteresis": (0.5, 5.0),
    "summer_cutoff": (10.0, 22.0),
    "bivalent": (-20.0, 5.0),
    "buffer_high": (45.0, 70.0),
    "room_low": (5.0, 20.0),
}

ALARM_TEXT = {
    "HP_LOCK": ("Heat pump high-pressure switch tripped", "Wärmepumpe Hochdruckstörung"),
    "HP_FB": ("Compressor did not follow its command", "Verdichter folgt dem Befehl nicht"),
    "CIRC_FB": ("Circulation pump did not follow its command", "Heizkreispumpe folgt dem Befehl nicht"),
    "S_OUT": ("Outside sensor broken, using 0 °C", "Außenfühler defekt, Ersatzwert 0 °C"),
    "S_ROOM": ("Room sensor broken", "Raumfühler defekt"),
    "S_BUF": ("Buffer sensor broken, heat sources off", "Pufferfühler defekt, Wärmeerzeuger aus"),
    "BUF_HIGH": ("Buffer temperature high", "Puffertemperatur zu hoch"),
    "ROOM_LOW": ("Room temperature low", "Raumtemperatur zu niedrig"),
    "FROST": ("Frost protection active", "Frostschutz aktiv"),
    # Fault signal contacts (Fehlersignalkontakte) in the distribution board
    "Q1_TRIP": ("RCD Q1 household tripped, circulation pump has no power", "FI Q1 Haushalt ausgelöst, Heizkreispumpe ohne Spannung"),
    "Q2_TRIP": ("RCD Q2 heat pump tripped", "FI Q2 Wärmepumpe ausgelöst"),
    "F6_TRIP": ("Breaker F6 circulation pump tripped", "LS F6 Heizkreispumpe ausgelöst"),
    "F7_TRIP": ("Breaker F7 heat pump tripped", "LS F7 Wärmepumpe ausgelöst"),
    "F8_TRIP": ("Breaker F8 heating rod tripped", "LS F8 Heizstab ausgelöst"),
}
TRIP_TAGS = ("Q1", "Q2", "F6", "F7", "F8")


@dataclass
class Alarm:
    tag: str
    active: bool = False
    acked: bool = True
    since: float = 0.0

    @property
    def shown(self) -> bool:
        return self.active or not self.acked


@dataclass
class Inputs:
    outside: float
    room: float
    buffer: float
    hp_running: bool
    circ_running: bool
    hp_lockout: bool
    defrosting: bool
    evu_lock: bool
    hp_supply: bool = True  # compressor breaker and its RCD closed
    circ_supply: bool = True
    trips: dict = field(default_factory=dict)  # device id -> tripped, from the fault signal contacts


@dataclass
class Outputs:
    hp: bool = False
    circ: bool = False
    rod: bool = False
    reset: bool = False  # one-scan pulse to the heat pump's fault reset input


@dataclass
class Plc:
    auto: bool = True  # False = standby: frost protection only
    setpoints: dict[str, float] = field(default_factory=lambda: dict(DEFAULT_SETPOINTS))
    out: Outputs = field(default_factory=Outputs)
    clock: float = 0.0
    hp_fault: bool = False
    circ_fault: bool = False
    sensor_faults: dict[str, bool] = field(default_factory=lambda: dict.fromkeys(SENSOR_RANGE, False))
    starts: int = 0
    run_s: float = 0.0
    outside_damped: float | None = None
    room_target: float = 0.0
    flow_target: float = 0.0
    heating: bool = False  # heating season and demand
    alarms: dict[str, Alarm] = field(default_factory=lambda: {t: Alarm(t) for t in ALARM_TEXT})
    events: deque = field(default_factory=lambda: deque(maxlen=200))

    def __post_init__(self) -> None:
        self._on_since = 0.0
        self._off_since = -MIN_OFF_S
        self._hp_mismatch = 0.0
        self._circ_mismatch = 0.0
        self._reset_request = False
        self._evu_was = False
        self._frost = False

    # Operator commands -------------------------------------------------------

    def set_auto(self, auto: bool) -> None:
        if auto != self.auto:
            self.auto = auto
            self._log("OPR", "Mode set to " + ("auto" if auto else "standby"))

    def set_setpoints(self, changes: dict[str, float]) -> None:
        """Apply several setpoints at once; all or nothing."""
        for name in changes:
            if name not in self.setpoints:
                raise KeyError(name)
        trial = dict(self.setpoints)
        for name, raw in changes.items():
            value = float(raw)
            lo, hi = SETPOINT_LIMITS[name]
            if not (math.isfinite(value) and lo <= value <= hi):
                raise ValueError(f"{name} must lie between {lo:g} and {hi:g}")
            trial[name] = value
        if trial["flow_min"] >= trial["flow_max"]:
            raise ValueError(
                f"Minimum flow ({trial['flow_min']:g} °C) must be below maximum flow ({trial['flow_max']:g} °C)"
            )
        if trial["room_night"] > trial["room_day"]:
            raise ValueError("Night setpoint must not be above the day setpoint")
        changed = [k for k in trial if trial[k] != self.setpoints[k]]
        self.setpoints = trial
        for name in changed:
            self._log("OPR", f"{name} set to {trial[name]:g}")

    def acknowledge(self) -> None:
        pending = [a for a in self.alarms.values() if not a.acked]
        for alarm in pending:
            alarm.acked = True
        if pending:
            self._log("ACK", "Acknowledged " + ", ".join(a.tag for a in pending))

    def reset_faults(self) -> None:
        self._reset_request = True
        if self.hp_fault or self.circ_fault or any(self.sensor_faults.values()):
            self.hp_fault = self.circ_fault = False
            self.sensor_faults = dict.fromkeys(SENSOR_RANGE, False)
            self._hp_mismatch = self._circ_mismatch = 0.0
        self._log("OPR", "Faults reset")

    # Scan cycle ----------------------------------------------------------------

    def scan(self, i: Inputs, *, clock: float, dt: float) -> Outputs:
        self.clock = clock
        sp = self.setpoints
        out = Outputs(reset=self._reset_request)
        self._reset_request = False

        self._check_sensors(i)
        outside = FALLBACK_OUTSIDE_C if self.sensor_faults["outside"] else i.outside
        if self.outside_damped is None:
            self.outside_damped = outside
        self.outside_damped += (outside - self.outside_damped) * min(1.0, dt / DAMPING_S)

        minute = (clock / 60.0) % 1440
        night_end = (sp["night_to"] - sp["preheat"]) % 1440
        night = sp["preheat"] < _span(sp["night_from"], sp["night_to"]) and _in_window(minute, sp["night_from"], night_end)
        self.room_target = sp["room_night"] if night else sp["room_day"]
        room_ok = not self.sensor_faults["room"]
        buffer_ok = not self.sensor_faults["buffer"]

        # Heating curve.
        flow = self.room_target + sp["curve_shift"] + sp["curve_slope"] * (self.room_target - self.outside_damped)
        if room_ok:
            flow += ROOM_GAIN * max(0.0, self.room_target - i.room)
        self.flow_target = max(sp["flow_min"], min(sp["flow_max"], flow))

        # Frost protection with hysteresis, so it does not chatter at the limit.
        if (room_ok and i.room < FROST_ROOM_C) or (buffer_ok and i.buffer < FROST_BUFFER_C):
            self._frost = True
        elif (not room_ok or i.room > FROST_ROOM_C + FROST_RELEASE_K) and (
            not buffer_ok or i.buffer > FROST_BUFFER_C + FROST_RELEASE_K
        ):
            self._frost = False
        frost = self._frost
        season = self.outside_damped < sp["summer_cutoff"]
        self.heating = (self.auto and season) or frost
        if frost:
            self.flow_target = max(self.flow_target, sp["flow_min"])

        out.circ = self.heating
        self._check_feedback(i, dt)

        # Compressor: two-point control on the buffer with timers and locks.
        hyst = sp["hysteresis"]
        want = self.out.hp
        if self.heating and buffer_ok:
            if i.buffer <= self.flow_target - hyst:
                want = True
            elif i.buffer >= self.flow_target + hyst:
                want = False
        else:
            want = False
        if self.out.hp and not want and clock - self._on_since < MIN_RUN_S and self.heating and buffer_ok:
            want = True  # minimum run time; faults and locks below still win
        if not self.out.hp and want and clock - self._off_since < MIN_OFF_S:
            want = False  # Taktsperre
        blocked = (i.evu_lock or i.hp_lockout or self.hp_fault or not buffer_ok or self.circ_fault
                   or not i.hp_supply or not i.circ_supply)
        if blocked:
            want = False
        if want and not self.out.hp:
            self.starts += 1
            self._on_since = clock
        if not want and self.out.hp:
            self._off_since = clock
        out.hp = want

        # Heating rod: backup when the heat pump is unavailable, help below the bivalent point.
        hp_unavailable = i.hp_lockout or self.hp_fault or not i.hp_supply
        rod_need = self.heating and buffer_ok and not self.circ_fault and i.circ_supply and not i.evu_lock
        cold = self.outside_damped < sp["bivalent"]
        if rod_need and (hp_unavailable or cold) and i.buffer <= self.flow_target - hyst - 1:
            out.rod = True
        elif rod_need and self.out.rod and i.buffer < self.flow_target:
            out.rod = True
        else:
            out.rod = False

        if i.evu_lock != self._evu_was:
            self._log("EVU", "Grid operator lock " + ("on" if i.evu_lock else "off"))
            self._evu_was = i.evu_lock

        self._update_alarms(i, frost)
        if i.hp_running:
            self.run_s += dt
        self.out = out
        return out

    def taktsperre_left(self) -> float:
        if self.out.hp:
            return 0.0
        return max(0.0, MIN_OFF_S - (self.clock - self._off_since))

    # Internals -------------------------------------------------------------------

    def _check_sensors(self, i: Inputs) -> None:
        for name, value in (("outside", i.outside), ("room", i.room), ("buffer", i.buffer)):
            lo, hi = SENSOR_RANGE[name]
            if not self.sensor_faults[name] and not (lo <= value <= hi):
                self.sensor_faults[name] = True

    def _check_feedback(self, i: Inputs, dt: float) -> None:
        # Compressor: a lockout explains a missing feedback, so it is not a second fault.
        if self.out.hp != i.hp_running and not i.hp_lockout and i.hp_supply:
            self._hp_mismatch += dt
            if self._hp_mismatch >= HP_FEEDBACK_S:
                self.hp_fault = True
        else:
            self._hp_mismatch = 0.0
        if self.out.circ != i.circ_running and i.circ_supply:
            self._circ_mismatch += dt
            if self._circ_mismatch >= CIRC_FEEDBACK_S:
                self.circ_fault = True
        else:
            self._circ_mismatch = 0.0

    def _update_alarms(self, i: Inputs, frost: bool) -> None:
        sp, db, a = self.setpoints, ALARM_DEADBAND_K, self.alarms
        conditions = {
            "HP_LOCK": i.hp_lockout,
            "HP_FB": self.hp_fault,
            "CIRC_FB": self.circ_fault,
            "S_OUT": self.sensor_faults["outside"],
            "S_ROOM": self.sensor_faults["room"],
            "S_BUF": self.sensor_faults["buffer"],
            "BUF_HIGH": not self.sensor_faults["buffer"]
            and _band(a["BUF_HIGH"].active, i.buffer >= sp["buffer_high"], i.buffer < sp["buffer_high"] - db),
            "ROOM_LOW": self.auto
            and not self.sensor_faults["room"]
            and _band(a["ROOM_LOW"].active, i.room <= sp["room_low"], i.room > sp["room_low"] + db),
            "FROST": frost,
            **{f"{dev}_TRIP": bool(i.trips.get(dev)) for dev in TRIP_TAGS},
        }
        for tag, active in conditions.items():
            alarm = a[tag]
            if active and not alarm.active:
                alarm.active, alarm.acked, alarm.since = True, False, self.clock
                self._log("ALM", f"{tag}: {ALARM_TEXT[tag][0]}")
            elif not active and alarm.active:
                alarm.active = False
                self._log("RTN", f"{tag}: back to normal")

    def _log(self, kind: str, text: str) -> None:
        self.events.append((self.clock, kind, text))


def _in_window(minute: float, start: float, end: float) -> bool:
    """True if minute lies in [start, end), wrapping past midnight."""
    if start <= end:
        return start <= minute < end
    return minute >= start or minute < end


def _span(start: float, end: float) -> float:
    """Length in minutes of the window [start, end), wrapping past midnight."""
    return (end - start) % 1440


def _band(was_active: bool, trip: bool, clear: bool) -> bool:
    """Alarm with a deadband so sensor noise cannot make it chatter."""
    if was_active:
        return not clear
    return trip
