"""Plant log in SQLite: exact daily energy, months, resuming a log, seasons."""

from __future__ import annotations

import datetime as dt

import pytest

from haussim.cli import main
from haussim.history import Store
from haussim.process import Process
from haussim.sim import Simulator, climate_mean


def logged(days: float, every: float = 60.0, **kw) -> Simulator:
    sim = Simulator(Process(seed=2, outside_mean_c=kw.pop("outside", -2.0)), store=Store(), record_every_s=every, **kw)
    for _ in range(int(days * 1440)):
        sim.step(60)
    return sim


@pytest.mark.parametrize("every", [60.0, 900.0])
def test_daily_energy_adds_up_to_the_meter(every):
    sim = logged(3, every)
    days = sim.store.days()
    assert [d["day"] for d in days] == ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04"]
    total_heat = sum(d["heat_kwh"] for d in days)
    total_elec = sum(d["elec_kwh"] for d in days)
    # Up to one sample interval of energy can be after the last sample.
    slack = 7.5 * every / 3600 + 0.01
    assert sim.process.heat_kwh - slack <= total_heat <= sim.process.heat_kwh + 1e-6
    assert sim.process.elec_kwh - slack <= total_elec <= sim.process.elec_kwh + 1e-6
    full = days[1]  # a whole day
    assert 25 < full["heat_kwh"] < 90 and 2.0 < full["jaz"] < 4.5
    assert 5 < full["house_kwh"] < 9
    assert 19.5 < full["room_avg"] < 21.5


def test_months_are_the_sum_of_their_days():
    sim = logged(3)
    (month,) = sim.store.months()
    days = sim.store.days("2026-01")
    assert month["month"] == "2026-01" and month["days"] == len(days)
    assert month["heat_kwh"] == pytest.approx(sum(d["heat_kwh"] for d in days))
    assert month["jaz"] == pytest.approx(month["heat_kwh"] / month["elec_kwh"])


def test_day_detail_and_events():
    sim = Simulator(Process(seed=2), store=Store())
    for _ in range(300):
        sim.step(60)
    sim.process.evu_lock = True
    for _ in range(120):
        sim.step(60)
    detail = sim.store.report("day", "2026-01-01")
    assert len(detail["samples"]) >= 400 and len(detail["samples"][0]) == 7
    assert any(kind == "EVU" for _m, kind, _t in detail["events"])
    with pytest.raises(ValueError):
        sim.store.report("weeks")


def test_resume_continues_date_and_meters(tmp_path):
    path = tmp_path / "plant.db"
    store = Store(path)
    sim = Simulator(Process(seed=2), store=store)
    for _ in range(2 * 1440):
        sim.step(60)
    store.commit()
    heat = sim.process.heat_kwh
    store.close()

    store = Store(path)
    again = Simulator(Process(seed=3), store=store)
    again.resume(store.last())
    assert again.date == dt.date(2026, 1, 4)
    assert again.process.heat_kwh == pytest.approx(heat, abs=0.5)
    for _ in range(1440):
        again.step(60)
    days = store.days()
    assert days[-1]["day"] == "2026-01-05"
    assert all(d["heat_kwh"] >= 0 for d in days)  # meters never step backwards


def test_seasonal_weather_follows_the_calendar():
    assert climate_mean(15) == pytest.approx(0.7, abs=0.1)
    assert climate_mean(197) == pytest.approx(18.3, abs=0.2)
    sim = Simulator(Process(seed=2), seasonal=True, start_date=dt.date(2026, 7, 10), store=Store())
    for _ in range(2 * 1440):
        sim.step(60)
    day = sim.store.days()[1]
    assert day["outside"] > 10
    assert day["heat_kwh"] < 5  # summer: heating off


def test_cli_simulate_to_db_and_report(tmp_path, capsys):
    path = tmp_path / "y.db"
    main(["simulate", "--days", "2", "--seasonal", "--db", str(path), "--every", "900"])
    out = capsys.readouterr().out
    assert "2026-01" in out and "total" in out
    main(["report", str(path)])
    assert "2026-01" in capsys.readouterr().out
