"""HMI commands. Shared by the HTTP server and the in-browser demo, so this
module must not import anything that needs sockets or threads."""

from __future__ import annotations

import math

from .sim import Simulator

# A house reacts over hours, so even the slowest useful speed is fast.
SPEEDS = (1, 60, 120, 600)
OUTSIDE_RANGE = (-20.0, 20.0)
FAULTS = {
    "hp": "hp_broken",
    "circ": "circ_broken",
    "window": "window_open",
    "outside_sensor": "outside_sensor_broken",
}


class CommandError(ValueError):
    pass


def _is_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _switch(value) -> bool:
    # bool("false") is True and a missing value would read as False, so a
    # switch takes JSON true or false and nothing else.
    if not isinstance(value, bool):
        raise CommandError("Value must be true or false")
    return value


def _apply_setpoints(sim: Simulator, value) -> None:
    if not isinstance(value, dict) or not value:
        raise CommandError("Setpoints must be an object of names and numbers")
    for name, number in value.items():
        if name not in sim.plc.setpoints:
            raise CommandError(f"Unknown setpoint {name!r}")
        if not _is_number(number):
            raise CommandError(f"{name} must be a number")
    try:
        sim.plc.set_setpoints(value)
    except ValueError as err:
        raise CommandError(str(err)) from None


def apply_command(sim: Simulator, body: dict) -> None:
    cmd = body.get("cmd")
    value = body.get("value")
    plc, p = sim.plc, sim.process
    with sim.lock:
        if cmd == "auto":
            plc.set_auto(_switch(value))
        elif cmd == "ack":
            plc.acknowledge()
        elif cmd == "reset":
            plc.reset_faults()
        elif cmd == "setpoints":
            _apply_setpoints(sim, value)
        elif cmd == "speed":
            if not _is_number(value) or value not in SPEEDS:
                raise CommandError(f"Speed must be one of {SPEEDS}")
            sim.speed = float(value)
        elif cmd == "pause":
            sim.paused = _switch(value)
        elif cmd == "evu":
            p.evu_lock = _switch(value)  # the grid operator's signal, not an operator control
        elif cmd == "outside":
            lo, hi = OUTSIDE_RANGE
            if not _is_number(value) or not lo <= value <= hi:
                raise CommandError(f"Outside mean must be between {lo:g} and {hi:g} °C")
            p.outside_mean_c = float(value)
        elif cmd == "fault":
            name = body.get("name")
            if name not in FAULTS:
                raise CommandError("Fault must be one of " + ", ".join(FAULTS))
            setattr(p, FAULTS[name], _switch(value))
        else:
            raise CommandError(f"Unknown command {cmd!r}")
