"""Command line. For now: run the house headless and print one line per hour."""

from __future__ import annotations

import argparse

from .process import Process
from .sim import Simulator


def _hhmm(clock_s: float) -> str:
    minute = int(clock_s // 60) % 1440
    return f"{minute // 60:02d}:{minute % 60:02d}"


def simulate(days: float, outside_mean: float, evu: list[str]) -> None:
    sim = Simulator(Process(outside_mean_c=outside_mean, seed=1))
    windows = []
    for span in evu:
        start, end = span.split("-")
        windows.append(tuple(int(t[:2]) * 60 + int(t[3:]) for t in (start, end)))
    print("time   outside  room   buffer target  HP     rod  COP   kWh el  starts")
    for hour in range(int(days * 24)):
        for _ in range(60):
            minute = sim.process.minute_of_day
            sim.process.evu_lock = any(a <= minute < b for a, b in windows)
            sim.step(60)
        s = sim.snapshot()
        hp = "DEFR" if s["defrosting"] else ("RUN " if s["hp_running"] else ("EVU " if s["evu_lock"] else "off "))
        print(
            f"{_hhmm(s['clock'])}  {s['outside']:6.1f}  {s['room']:5.1f}  {s['buffer']:5.1f}  {s['flow_target']:5.1f}"
            f"   {hp}   {'on ' if s['rod_on'] else 'off'}  {s['cop']:4.1f}  {s['elec_kwh']:6.1f}  {s['starts']:5d}"
        )
    s = sim.snapshot()
    spf = f"{s['spf']:.2f}" if s["spf"] else "-"
    print(f"\nHeat {s['heat_kwh']:.1f} kWh, electricity {s['elec_kwh']:.1f} kWh, seasonal COP {spf}")
    for alarm in s["alarms"]:
        print(f"Alarm {alarm['tag']}: {alarm['text']}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="haussim", description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    run = sub.add_parser("simulate", help="run headless and print one line per simulated hour")
    run.add_argument("--days", type=float, default=1.0)
    run.add_argument("--outside", type=float, default=-2.0, help="mean outside temperature in °C")
    run.add_argument("--evu", action="append", default=[], metavar="HH:MM-HH:MM", help="grid operator lock window")
    args = parser.parse_args(argv)
    if args.cmd == "simulate":
        simulate(args.days, args.outside, args.evu)


if __name__ == "__main__":
    main()
