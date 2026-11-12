"""Ties the house and the controller together.

All access goes through one lock, because the simulation loop and the
interfaces (HMI, Modbus) each run in their own thread.
"""

from __future__ import annotations

import datetime as dt_
import math
import random
import threading
from collections import deque

from .electrical import Board
from .plc import ALARM_TEXT, TRIP_TAGS, Inputs, Plc
from .process import Process

HISTORY_EVERY_S = 60.0  # one trend sample per simulated minute
HISTORY_LEN = 1440  # one simulated day
CIRC_PUMP_W = 45.0
MAX_DT = 5.0  # larger steps would let the feedback timers skip
START_DATE = dt_.date(2026, 1, 1)


def climate_mean(day_of_year: float) -> float:
    """Daily mean outside temperature over a German year, roughly the DWD
    1991-2020 normals: about 1 °C in mid-January, 18 °C in mid-July."""
    return 9.5 - 8.8 * math.cos(2 * math.pi * (day_of_year - 15) / 365.25)


class Simulator:
    def __init__(
        self,
        process: Process | None = None,
        plc: Plc | None = None,
        board: Board | None = None,
        *,
        start_date: dt_.date = START_DATE,
        seasonal: bool = False,
        store=None,
        record_every_s: float = 60.0,
        seed: int = 1,
    ) -> None:
        self.process = process or Process()
        self.plc = plc or Plc()
        self.board = board or Board.standard()
        self.start_date = start_date
        self.seasonal = seasonal  # outside mean follows the calendar plus day-to-day weather
        self.store = store
        self.record_every_s = record_every_s
        self.evu_s = 0.0
        self._rng = random.Random(seed)
        self._weather_day = -1
        self._weather_offset = 0.0
        self._next_record = self.process.clock_s
        self._events_seen = 0
        self.lock = threading.RLock()
        self.speed = 120.0
        self.paused = False
        self.history: deque[tuple] = deque(maxlen=HISTORY_LEN)
        self._next_sample = self.process.clock_s

    def step(self, dt: float) -> None:
        """Advance by dt simulated seconds, in slices the PLC can keep up with."""
        with self.lock:
            while dt > 1e-9:
                part = min(dt, MAX_DT)
                self._step(part)
                dt -= part

    @property
    def day_index(self) -> int:
        return int(self.process.clock_s // 86400)

    @property
    def date(self) -> dt_.date:
        return self.start_date + dt_.timedelta(days=self.day_index)

    def resume(self, last: dict) -> None:
        """Continue a stored plant log: next day, meters where they stopped."""
        self.start_date = dt_.date.fromisoformat(last["day"]) + dt_.timedelta(days=1)
        p = self.process
        p.heat_kwh, p.elec_kwh, p.rod_kwh = last["heat_kwh"], last["elec_kwh"], last["rod_kwh"]
        self.board.house_kwh = last["house_kwh"]
        self.plc.starts, self.plc.run_s, self.evu_s = int(last["starts"]), last["run_s"], last["evu_s"]
        self.board.hp_kwh = p.elec_kwh

    def _weather(self) -> None:
        day = self.day_index
        if day != self._weather_day:
            # Day-to-day weather: a cold snap or a mild spell lasts a few days.
            self._weather_offset = max(-8.0, min(8.0, 0.75 * self._weather_offset + self._rng.gauss(0, 2.2)))
            self._weather_day = day
        doy = self.date.timetuple().tm_yday + self.process.minute_of_day / 1440
        self.process.outside_mean_c = climate_mean(doy) + self._weather_offset

    def _record(self) -> None:
        p, plc, board = self.process, self.plc, self.board
        day, minute = self.date.isoformat(), int(p.minute_of_day)
        self.store.record({
            "day": day, "minute": minute,
            "outside": p.outside_c, "room": p.room_c, "buffer": p.buffer_c, "flow_target": plc.flow_target,
            "heat_w": p.hp_heat_w, "elec_w": p.hp_elec_w + p.rod_w_now,
            "house_w": sum(b.power_w for b in board.breakers.values() if b.rcd == "Q1"),
            "hp_on": int(p.hp_running), "rod_on": int(p.rod_w_now > 0), "evu": int(p.evu_lock),
            "heat_kwh": p.heat_kwh, "elec_kwh": p.elec_kwh, "rod_kwh": p.rod_kwh, "house_kwh": board.house_kwh,
            "starts": plc.starts, "run_s": plc.run_s, "evu_s": self.evu_s,
        })

    def _record_events(self) -> None:
        plc = self.plc
        new = plc.log_count - self._events_seen
        if new <= 0:
            return
        day, minute = self.date.isoformat(), int(self.process.minute_of_day)
        for _clock, kind, text in list(plc.events)[-min(new, len(plc.events)):]:
            self.store.event(day, minute, kind, text)
        self._events_seen = plc.log_count

    def _step(self, dt: float) -> None:
        p, plc, board = self.process, self.plc, self.board
        if self.seasonal:
            self._weather()
        p.hp_supply = board.energized("F7")
        p.rod_supply = board.energized("F8")
        p.circ_supply = board.energized("F6")
        out = plc.scan(
            Inputs(
                outside=p.outside_sensor,
                room=p.room_sensor,
                buffer=p.buffer_sensor,
                hp_running=p.hp_running,
                circ_running=p.circ_running,
                hp_lockout=p.hp_lockout,
                defrosting=p.defrosting,
                evu_lock=p.evu_lock,
                hp_supply=p.hp_supply,
                circ_supply=p.circ_supply,
                trips={dev: (board.rcd_tripped(dev) if dev in board.rcds else board.breaker_tripped(dev))
                       for dev in TRIP_TAGS},
            ),
            clock=p.clock_s,
            dt=dt,
        )
        if out.reset and p.reset_lockout():
            plc._log("OPR", "High-pressure switch reset")
        p.hp_cmd, p.circ_cmd, p.rod_cmd = out.hp, out.circ, out.rod
        p.step(dt)
        board.step(dt, p.minute_of_day, p.hp_elec_w, p.rod_w_now, CIRC_PUMP_W * p.circ)
        for kind, text in board.events:
            plc._log(kind, text)
        board.events.clear()
        if p.clock_s >= self._next_sample:
            self.history.append(
                (p.clock_s, p.outside_c, p.room_c, p.buffer_c, plc.flow_target, p.hp_heat_w, p.hp_elec_w + p.rod_w_now)
            )
            self._next_sample = p.clock_s + HISTORY_EVERY_S
        if p.evu_lock:
            self.evu_s += dt
        if self.store is not None:
            self._record_events()
            if p.clock_s >= self._next_record:
                self._record()
                self._next_record = p.clock_s + self.record_every_s

    def history_list(self) -> list[list[float]]:
        with self.lock:
            return [list(h) for h in self.history]

    def snapshot(self) -> dict:
        with self.lock:
            p, plc = self.process, self.plc
            return {
                "clock": p.clock_s,
                "date": self.date.isoformat(),
                "minute": p.minute_of_day,
                "outside": p.outside_sensor,
                "outside_damped": plc.outside_damped,
                "room": p.room_sensor,
                "buffer": p.buffer_sensor,
                "room_target": plc.room_target,
                "flow_target": plc.flow_target,
                "heating": plc.heating,
                "auto": plc.auto,
                "hp_cmd": plc.out.hp,
                "hp_running": p.hp_running,
                "compressor": p.compressor,
                "defrosting": p.defrosting,
                "circ_running": p.circ_running,
                "rod_on": p.rod_w_now > 0,
                "evu_lock": p.evu_lock,
                "hp_heat_w": p.hp_heat_w,
                "hp_elec_w": p.hp_elec_w,
                "rod_w": p.rod_w_now,
                "emitter_w": p.emitter_w,
                "cop": p.cop,
                "spf": p.heat_kwh / p.elec_kwh if p.elec_kwh > 0.01 else None,
                "heat_kwh": p.heat_kwh,
                "elec_kwh": p.elec_kwh,
                "starts": plc.starts,
                "run_s": plc.run_s,
                "taktsperre": plc.taktsperre_left(),
                "setpoints": dict(plc.setpoints),
                "alarms": [
                    {
                        "tag": a.tag,
                        "text": ALARM_TEXT[a.tag][0],
                        "text_de": ALARM_TEXT[a.tag][1],
                        "active": a.active,
                        "acked": a.acked,
                        "since": a.since,
                    }
                    for a in plc.alarms.values()
                    if a.shown
                ],
                "events": [list(e) for e in list(plc.events)[-30:]],
                "board": self.board.snapshot(),
                "sim": {
                    "speed": self.speed,
                    "paused": self.paused,
                    "outside_mean": p.outside_mean_c,
                    "seasonal": self.seasonal,
                    "recording": self.store is not None,
                    "hp_broken": p.hp_broken,
                    "circ_broken": p.circ_broken,
                    "window_open": p.window_open,
                    "outside_sensor_broken": p.outside_sensor_broken,
                    "short_circuit": self.board.short_circuit,
                    "overload": self.board.overload,
                    "insulation_fault": self.board.insulation_fault,
                },
            }
