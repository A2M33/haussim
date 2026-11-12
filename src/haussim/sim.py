"""Ties the house and the controller together.

All access goes through one lock, because the simulation loop and the
interfaces (HMI, Modbus) each run in their own thread.
"""

from __future__ import annotations

import threading
from collections import deque

from .plc import ALARM_TEXT, Inputs, Plc
from .process import Process

HISTORY_EVERY_S = 60.0  # one trend sample per simulated minute
HISTORY_LEN = 1440  # one simulated day
MAX_DT = 5.0  # larger steps would let the feedback timers skip


class Simulator:
    def __init__(self, process: Process | None = None, plc: Plc | None = None) -> None:
        self.process = process or Process()
        self.plc = plc or Plc()
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

    def _step(self, dt: float) -> None:
        p, plc = self.process, self.plc
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
            ),
            clock=p.clock_s,
            dt=dt,
        )
        if out.reset and p.reset_lockout():
            plc._log("OPR", "High-pressure switch reset")
        p.hp_cmd, p.circ_cmd, p.rod_cmd = out.hp, out.circ, out.rod
        p.step(dt)
        if p.clock_s >= self._next_sample:
            self.history.append(
                (p.clock_s, p.outside_c, p.room_c, p.buffer_c, plc.flow_target, p.hp_heat_w, p.hp_elec_w + p.rod_w_now)
            )
            self._next_sample = p.clock_s + HISTORY_EVERY_S

    def history_list(self) -> list[list[float]]:
        with self.lock:
            return [list(h) for h in self.history]

    def snapshot(self) -> dict:
        with self.lock:
            p, plc = self.process, self.plc
            return {
                "clock": p.clock_s,
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
                "sim": {
                    "speed": self.speed,
                    "paused": self.paused,
                    "outside_mean": p.outside_mean_c,
                    "hp_broken": p.hp_broken,
                    "circ_broken": p.circ_broken,
                    "window_open": p.window_open,
                    "outside_sensor_broken": p.outside_sensor_broken,
                },
            }
