from haussim.process import HIGH_PRESSURE_TRIP_C, OPEN_CIRCUIT_C, Process, outside_at


def test_outside_curve_coldest_early_morning():
    assert outside_at(5 * 60, -2, 5) == -7
    assert outside_at(17 * 60, -2, 5) == 3


def test_cop_falls_when_it_gets_colder():
    p = Process(seed=1)
    p.buffer_c = 35
    p.outside_c = 7
    warm = p.carnot_cop()
    p.outside_c = -10
    assert p.carnot_cop() < warm


def test_compressor_ramps_and_reports_running():
    p = Process(seed=1)
    p.hp_cmd = True
    p.step(20)
    assert not p.hp_running
    p.step(20)
    assert p.hp_running
    assert p.hp_heat_w > 0 and p.hp_elec_w > 0


def test_broken_sensor_reads_open_circuit():
    p = Process(seed=1)
    p.outside_sensor_broken = True
    assert p.outside_sensor == OPEN_CIRCUIT_C


def test_high_pressure_switch_trips_and_needs_cool_water():
    p = Process(seed=1, buffer_c=HIGH_PRESSURE_TRIP_C + 1)
    p.hp_cmd = True
    for _ in range(20):
        p.step(5)
    assert p.hp_lockout
    assert not p.reset_lockout()  # still hot
    p.buffer_c = 40
    assert p.reset_lockout()


def test_defrost_happens_when_cold_and_pulls_heat():
    p = Process(seed=1, outside_mean_c=-3, outside_swing_c=0)
    p.hp_cmd = True
    p.buffer_c = 30
    saw_defrost = False
    for _ in range(int(60 * 60 / 5)):
        p.step(5)
        p.buffer_c = 30  # hold the buffer so only the defrost logic matters
        if p.defrosting and p.hp_heat_w < 0:
            saw_defrost = True
    assert saw_defrost
