"""Whole-system tests: the PLC runs the simulated house through real scenarios."""

from __future__ import annotations

import pytest

from haussim.plc import MIN_OFF_S, MIN_RUN_S, Plc
from haussim.process import Process
from haussim.sim import Simulator


def make(**process_kwargs) -> Simulator:
    process_kwargs.setdefault("seed", 7)
    return Simulator(Process(**process_kwargs))


def run(sim: Simulator, seconds: float, step: float = 5.0, watch=None) -> None:
    t = 0.0
    while t < seconds:
        sim.step(step)
        t += step
        if watch:
            watch(sim)


def test_winter_day_holds_room_near_setpoint():
    sim = make(outside_mean_c=-5.0)
    run(sim, 6 * 3600)  # warm up
    rooms = []
    run(sim, 24 * 3600, watch=lambda s: rooms.append((s.process.minute_of_day, s.process.room_c)))
    day = [r for m, r in rooms if 8 * 60 <= m < 22 * 60]
    assert min(day) > 19.8  # preheat brings the room back before 08:00
    assert max(day) < 22.0
    assert 20.3 < sum(day) / len(day) < 21.5
    assert sim.plc.starts < 3 * 30  # well under three starts per hour


def test_summer_never_starts_compressor():
    sim = make(outside_mean_c=24.0, room_c=23.0)  # coolest hour still above the 17 °C cut-off
    run(sim, 24 * 3600)
    assert sim.plc.starts == 0
    assert not sim.plc.heating


def test_evu_lock_stops_compressor_and_rod_at_once():
    sim = make(outside_mean_c=-15.0)
    run(sim, 2 * 3600)
    while not sim.process.hp_running:
        sim.step(5)
    sim.process.evu_lock = True
    sim.step(5)
    assert sim.plc.out.hp is False
    assert sim.plc.out.rod is False
    on_during_lock = []
    run(sim, 2 * 3600, watch=lambda s: on_during_lock.append(s.plc.out.hp or s.plc.out.rod))
    assert not any(on_during_lock)
    assert any(kind == "EVU" for _, kind, _ in sim.plc.events)


def test_taktsperre_and_minimum_run_time():
    sim = make(outside_mean_c=0.0)
    starts, stops = [], []
    prev = [False]

    def watch(s):
        now = s.plc.out.hp
        if now and not prev[0]:
            starts.append(s.process.clock_s)
        if prev[0] and not now:
            stops.append(s.process.clock_s)
        prev[0] = now

    run(sim, 24 * 3600, watch=watch)
    assert len(starts) > 5
    for start, stop in zip(starts, stops):
        assert stop - start >= MIN_RUN_S - 5
    for stop, next_start in zip(stops, starts[1:]):
        assert next_start - stop >= MIN_OFF_S - 5


def test_broken_compressor_latches_fault_and_rod_takes_over():
    sim = make(outside_mean_c=-5.0)
    run(sim, 3600)
    sim.process.hp_broken = True
    rooms = []
    run(sim, 12 * 3600, watch=lambda s: rooms.append(s.process.room_c))
    assert sim.plc.hp_fault
    assert sim.plc.alarms["HP_FB"].active
    assert sim.process.rod_w_now > 0 or any(k == "ALM" for _, k, _ in sim.plc.events)
    assert min(rooms[len(rooms) // 2:]) > 18.0  # the rod keeps the house warm


def test_seized_circulation_pump_stops_heat_sources():
    sim = make(outside_mean_c=-5.0)
    run(sim, 3600)
    sim.process.circ_broken = True
    run(sim, 600)
    assert sim.plc.circ_fault
    assert sim.plc.alarms["CIRC_FB"].active
    assert sim.plc.out.hp is False and sim.plc.out.rod is False


def test_broken_outside_sensor_uses_fallback_and_keeps_heating():
    sim = make(outside_mean_c=-5.0)
    run(sim, 3600)
    sim.process.outside_sensor_broken = True
    rooms = []
    run(sim, 12 * 3600, watch=lambda s: rooms.append(s.process.room_c))
    assert sim.plc.sensor_faults["outside"]
    assert sim.plc.alarms["S_OUT"].active
    assert sim.plc.heating
    assert min(rooms[len(rooms) // 2:]) > 19.0


def test_high_pressure_lockout_raises_alarm_and_resets_when_cool():
    sim = make(outside_mean_c=-5.0)
    run(sim, 600)
    sim.process.hp_lockout = True
    sim.step(5)
    assert sim.plc.alarms["HP_LOCK"].active
    assert sim.plc.out.hp is False
    assert not sim.plc.hp_fault  # the lockout explains the missing feedback
    sim.plc.reset_faults()
    sim.step(5)
    assert not sim.process.hp_lockout  # buffer is cool, so the switch resets


def test_open_window_drops_room_and_raises_flow_target():
    sim = make(outside_mean_c=-5.0)
    run(sim, 4 * 3600)
    before = sim.plc.flow_target
    sim.process.window_open = True
    run(sim, 4 * 3600)
    assert sim.process.room_c < 21.0
    assert sim.plc.flow_target > before


def test_standby_keeps_frost_protection():
    sim = make(outside_mean_c=-15.0, room_c=8.0, buffer_c=10.0)
    sim.plc.set_auto(False)
    temps = []
    run(sim, 12 * 3600, watch=lambda s: temps.append(s.process.room_c))
    assert any(kind == "ALM" and text.startswith("FROST") for _, kind, text in sim.plc.events)
    assert min(temps) > 6.0  # never far below the frost limit
    assert sim.plc.starts < 12 * 3  # hysteresis keeps it from chattering


def test_setpoints_are_all_or_nothing():
    plc = Plc()
    with pytest.raises(ValueError):
        plc.set_setpoints({"flow_min": 35.0, "flow_max": 34.0})
    assert plc.setpoints["flow_min"] == 25.0
    with pytest.raises(ValueError):
        plc.set_setpoints({"room_day": float("nan")})
    with pytest.raises(ValueError):
        plc.set_setpoints({"room_night": 23.0})  # above the day setpoint
    with pytest.raises(KeyError):
        plc.set_setpoints({"nope": 1.0})
    plc.set_setpoints({"room_day": 22.0, "curve_slope": 0.6})
    assert plc.setpoints["room_day"] == 22.0


def test_night_setback_window_wraps_midnight():
    sim = make(outside_mean_c=0.0, start_minute=23 * 60)
    sim.step(5)
    assert sim.plc.room_target == 19.0
    sim = make(outside_mean_c=0.0, start_minute=12 * 60)
    sim.step(5)
    assert sim.plc.room_target == 21.0


def test_energy_balance_and_cop_are_plausible():
    sim = make(outside_mean_c=-2.0)
    run(sim, 24 * 3600)
    s = sim.snapshot()
    assert 2.3 < s["spf"] < 4.5
    # Heat delivered roughly matches the house loss over a day.
    expected_kwh = 150 * (21 - (-2)) * 24 / 1000
    assert 0.6 * expected_kwh < s["heat_kwh"] < 1.3 * expected_kwh
