"""Distribution board: breaker curves, RCDs, and what a trip does to the heating."""

from __future__ import annotations

import pytest

from haussim.commands import apply_command
from haussim.electrical import Board, Breaker
from haussim.process import Process
from haussim.sim import Simulator


def time_to_trip(multiple: float, char: str = "B", limit_s: float = 7200.0, dt: float = 0.5) -> float | None:
    br = Breaker("F", ("", ""), 16, char, (0,), "Q1")
    t = 0.0
    while t < limit_s:
        br.step(multiple * 16, dt)
        t += dt
        if not br.closed:
            return t
    return None


def test_breaker_follows_iec_60898():
    assert time_to_trip(1.13) is None  # must hold for an hour, holds for two
    t145 = time_to_trip(1.45)
    assert t145 is not None and 60 < t145 < 3600
    t255 = time_to_trip(2.55)
    assert t255 is not None and 1 < t255 < 60
    assert time_to_trip(5.0, "B") <= 0.5  # magnetic, instant
    assert time_to_trip(5.0, "C") > 1  # type C rides through a motor start
    assert time_to_trip(10.0, "C") <= 0.5


def make(outside=-5.0) -> Simulator:
    return Simulator(Process(outside_mean_c=outside, seed=3))


def run(sim: Simulator, seconds: float, step: float = 5.0) -> None:
    for _ in range(int(seconds / step)):
        sim.step(step)


def alarms(sim: Simulator) -> set[str]:
    return {a["tag"] for a in sim.snapshot()["alarms"] if a["active"]}


def test_normal_winter_day_trips_nothing():
    sim = make(-10.0)
    peak = 0.0
    for _ in range(24 * 60):
        sim.step(60)
        peak = max(peak, *sim.board.phase_a)
    b = sim.snapshot()["board"]
    assert all(br["closed"] for br in b["breakers"]) and all(r["closed"] for r in b["rcds"])
    assert peak < 35  # main fuse
    assert 3 < b["house_kwh"] < 12
    assert b["hp_kwh"] == pytest.approx(sim.process.elec_kwh, rel=0.02)


def test_short_circuit_trips_instantly_and_again_on_reclose():
    sim = make()
    apply_command(sim, {"cmd": "fault", "name": "short", "value": True})
    sim.step(1)
    f2 = sim.board.breakers["F2"]
    assert not f2.closed and f2.trip == "short"
    apply_command(sim, {"cmd": "switch", "device": "F2", "value": True})
    sim.step(1)
    assert not f2.closed  # fault still there
    apply_command(sim, {"cmd": "fault", "name": "short", "value": False})
    apply_command(sim, {"cmd": "switch", "device": "F2", "value": True})
    run(sim, 600)
    assert f2.closed and f2.trip == ""
    assert sim.board.breakers["F1"].closed  # neighbours unaffected


def test_overload_trips_after_minutes():
    sim = make()
    sim.process.clock_s = 3 * 3600  # no kettle or cooker at this time
    apply_command(sim, {"cmd": "fault", "name": "overload", "value": True})
    t = 0
    while sim.board.breakers["F3"].closed and t < 3600:
        sim.step(5)
        t += 5
    assert sim.board.breakers["F3"].trip == "overload"
    assert 120 < t < 1200


def test_insulation_fault_trips_rcd_and_stops_the_heating_circuit():
    sim = make()
    run(sim, 2 * 3600)
    assert sim.process.circ_running
    apply_command(sim, {"cmd": "fault", "name": "insulation", "value": True})
    run(sim, 60)
    q1 = sim.board.rcds["Q1"]
    assert not q1.closed and q1.trip == "leak"
    assert not sim.process.circ_running and not sim.process.hp_running
    active = alarms(sim)
    assert "Q1_TRIP" in active and "CIRC_FB" not in active  # the PLC knows why the pump stopped

    # Reclosing with the faulty appliance still connected trips again at once.
    apply_command(sim, {"cmd": "switch", "device": "Q1", "value": True})
    sim.step(1)
    assert not q1.closed
    # The electrician's way: switch the breakers off, find the faulty circuit.
    apply_command(sim, {"cmd": "switch", "device": "F5", "value": False})
    apply_command(sim, {"cmd": "switch", "device": "Q1", "value": True})
    run(sim, 600)
    assert q1.closed and sim.process.circ_running
    assert "Q1_TRIP" not in alarms(sim)


def test_heat_pump_breaker_trip_lets_the_rod_take_over():
    sim = make(-8.0)
    run(sim, 3 * 3600)
    sim.board.breakers["F7"].open("overload")
    run(sim, 2 * 3600)
    active = alarms(sim)
    assert "F7_TRIP" in active and "HP_FB" not in active
    assert not sim.process.hp_running
    assert sim.process.room_c > 19.5  # the 6 kW rod keeps the house warm
    apply_command(sim, {"cmd": "switch", "device": "F7", "value": True})
    ran = False
    for _ in range(720):  # one hour
        sim.step(5)
        ran = ran or sim.process.hp_running
    assert ran and "F7_TRIP" not in alarms(sim)


def test_rcd_test_button():
    sim = make()
    apply_command(sim, {"cmd": "rcd_test", "device": "Q2"})
    sim.step(5)
    assert sim.board.rcds["Q2"].trip == "test" and "Q2_TRIP" in alarms(sim)
    assert any("test button" in e[2] for e in sim.snapshot()["events"])
    apply_command(sim, {"cmd": "switch", "device": "Q2", "value": True})
    sim.step(5)
    assert "Q2_TRIP" not in alarms(sim)


def test_manual_switch_off_is_no_alarm():
    sim = make()
    apply_command(sim, {"cmd": "switch", "device": "F7", "value": False})
    run(sim, 600)
    assert not alarms(sim) & {"F7_TRIP", "HP_FB"}


def test_board_commands_refuse_bad_input():
    from haussim.commands import CommandError

    sim = make()
    for body in (
        {"cmd": "switch", "device": "F99", "value": True},
        {"cmd": "switch", "device": "F1", "value": "on"},
        {"cmd": "rcd_test", "device": "F1"},
        {"cmd": "fault", "name": "fire", "value": True},
    ):
        with pytest.raises(CommandError):
            apply_command(sim, body)


def test_standard_board_layout():
    b = Board.standard()
    assert list(b.rcds) == ["Q1", "Q2"]
    assert {br.rcd for br in b.breakers.values() if br.id in ("F7", "F8")} == {"Q2"}
    assert b.breakers["F7"].char == "C"  # compressor inrush
