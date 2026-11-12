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
BOARD_FAULTS = {"short": "short_circuit", "overload": "overload", "insulation": "insulation_fault"}


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


def _flush_board_events(sim: Simulator) -> None:
    for kind, text in sim.board.events:
        sim.plc._log(kind, text)
    sim.board.events.clear()


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
            if name in FAULTS:
                setattr(p, FAULTS[name], _switch(value))
            elif name in BOARD_FAULTS:
                setattr(sim.board, BOARD_FAULTS[name], _switch(value))
            else:
                raise CommandError("Fault must be one of " + ", ".join([*FAULTS, *BOARD_FAULTS]))
        elif cmd == "switch":
            device = body.get("device")
            if device not in sim.board.rcds and device not in sim.board.breakers:
                raise CommandError(f"Unknown device {device!r}")
            sim.board.switch(device, _switch(value))
            _flush_board_events(sim)
        elif cmd == "rcd_test":
            device = body.get("device")
            if device not in sim.board.rcds:
                raise CommandError(f"{device!r} is not an RCD")
            sim.board.test_rcd(device)
            _flush_board_events(sim)
        else:
            raise CommandError(f"Unknown command {cmd!r}")
