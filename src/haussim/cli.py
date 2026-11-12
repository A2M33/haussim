"""Command line: `haussim run` opens the HMI, `haussim simulate` runs days
headless, `haussim report` prints the monthly figures from a plant log."""

from __future__ import annotations

import argparse
import datetime as dt
import sys
import threading
import time
import webbrowser

from . import __version__
from .commands import SPEEDS
from .history import Store
from .process import Process
from .sim import START_DATE, Simulator

TICK_S = 0.1
COMMIT_EVERY_S = 5.0


def _hhmm(clock_s: float) -> str:
    minute = int(clock_s // 60) % 1440
    return f"{minute // 60:02d}:{minute % 60:02d}"


def _num(value, digits=1, width=7) -> str:
    return f"{value:{width}.{digits}f}" if value is not None else " " * (width - 1) + "-"


def open_sim(args: argparse.Namespace, seed: int | None = None) -> tuple[Simulator, Store | None]:
    """A simulator, continuing the plant log in --db if it already has data."""
    store = Store(args.db) if args.db else None
    sim = Simulator(
        # A plant log counts calendar days, so it starts at midnight.
        Process(outside_mean_c=args.outside, seed=seed, start_minute=0 if store else 6 * 60),
        start_date=args.date,
        seasonal=args.seasonal,
        store=store,
        record_every_s=getattr(args, "every", 60.0),
    )
    last = store.last() if store else None
    if last:
        sim.resume(last)
    return sim, store


def run_loop(sim: Simulator, stop: threading.Event) -> None:
    last = time.monotonic()
    last_commit = last
    while not stop.wait(TICK_S):
        now = time.monotonic()
        real, last = min(now - last, 1.0), now
        if not sim.paused:
            sim.step(real * sim.speed)
        if sim.store is not None and now - last_commit >= COMMIT_EVERY_S:
            with sim.lock:
                sim.store.commit()
            last_commit = now


def cmd_run(args: argparse.Namespace) -> int:
    from .web import HmiServer  # sockets only when the HMI is wanted

    sim, store = open_sim(args)
    if store is None:  # the report page still works for this session
        sim.store = Store(":memory:")
    sim.speed = float(args.speed)
    try:
        hmi = HmiServer(sim, args.host, args.http_port)
    except OSError as err:
        print(f"Cannot open HMI port {args.http_port}: {err.strerror}. Try --http-port.", file=sys.stderr)
        return 1
    stop = threading.Event()
    threading.Thread(target=run_loop, args=(sim, stop), name="sim", daemon=True).start()
    hmi.start()

    shown_host = "localhost" if args.host in ("127.0.0.1", "0.0.0.0") else args.host
    url = f"http://{shown_host}:{args.http_port}/"
    print(f"haussim {__version__}")
    print(f"  HMI     {url}")
    print(f"  Speed   {args.speed}x simulated time")
    print(f"  Log     {args.db or 'in memory, gone when you stop'} from {sim.date}")
    print("Press Ctrl+C to stop.")
    if not args.no_browser:
        webbrowser.open(url)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
        hmi.shutdown()
        hmi.server_close()
        with sim.lock:
            sim.store.commit()
            sim.store.close()
    return 0


def print_months(store: Store) -> None:
    months = store.months()
    if not months:
        print("No data in this log yet.")
        return
    print("month    days  outside  heat kWh  elec kWh  rod kWh  house kWh   JAZ  starts  run h")
    total = {"heat_kwh": 0.0, "elec_kwh": 0.0, "rod_kwh": 0.0, "house_kwh": 0.0, "starts": 0, "run_s": 0.0}
    for m in months:
        print(
            f"{m['month']}  {m['days']:4d}  {_num(m['outside'])}  {_num(m['heat_kwh'], 0, 8)}  "
            f"{_num(m['elec_kwh'], 0, 8)}  {_num(m['rod_kwh'], 0, 7)}  {_num(m['house_kwh'], 0, 9)}  "
            f"{_num(m['jaz'], 2, 5)}  {int(m['starts']):6d}  {m['run_s'] / 3600:5.0f}"
        )
        for k in total:
            total[k] += m[k]
    jaz = total["heat_kwh"] / total["elec_kwh"] if total["elec_kwh"] > 0.05 else None
    print(
        f"total          {'':7}  {_num(total['heat_kwh'], 0, 8)}  {_num(total['elec_kwh'], 0, 8)}  "
        f"{_num(total['rod_kwh'], 0, 7)}  {_num(total['house_kwh'], 0, 9)}  {_num(jaz, 2, 5)}  "
        f"{int(total['starts']):6d}  {total['run_s'] / 3600:5.0f}"
    )


def cmd_simulate(args: argparse.Namespace) -> int:
    sim, store = open_sim(args, seed=1)
    windows = []
    for span in args.evu:
        start, end = span.split("-")
        windows.append(tuple(int(t[:2]) * 60 + int(t[3:]) for t in (start, end)))
    hourly = store is None
    if hourly:
        print("time   outside  room   buffer target  HP     rod  COP   kWh el  starts")
    hours = int(args.days * 24)
    for hour in range(hours):
        for i in range(60):
            minute = sim.process.minute_of_day
            sim.process.evu_lock = any(a <= minute < b for a, b in windows)
            # A log stops one second before midnight, so no empty next day appears.
            sim.step(59 if store and hour == hours - 1 and i == 59 else 60)
        if hourly:
            s = sim.snapshot()
            hp = "DEFR" if s["defrosting"] else ("RUN " if s["hp_running"] else ("EVU " if s["evu_lock"] else "off "))
            print(
                f"{_hhmm(s['clock'])}  {s['outside']:6.1f}  {s['room']:5.1f}  {s['buffer']:5.1f}  {s['flow_target']:5.1f}"
                f"   {hp}   {'on ' if s['rod_on'] else 'off'}  {s['cop']:4.1f}  {s['elec_kwh']:6.1f}  {s['starts']:5d}"
            )
        elif hour % 24 == 23:
            store.commit()
            print(f"\r{sim.date}", end="", file=sys.stderr, flush=True)
    if hourly:
        s = sim.snapshot()
        spf = f"{s['spf']:.2f}" if s["spf"] else "-"
        print(f"\nHeat {s['heat_kwh']:.1f} kWh, electricity {s['elec_kwh']:.1f} kWh, seasonal COP {spf}")
        for alarm in s["alarms"]:
            print(f"Alarm {alarm['tag']}: {alarm['text']}")
    else:
        store.commit()
        print(file=sys.stderr)
        print_months(store)
        store.close()
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    store = Store(args.db)
    print_months(store)
    store.close()
    return 0


def port_number(text: str) -> int:
    port = int(text)
    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError("port must be 1 to 65535")
    return port


def iso_date(text: str) -> dt.date:
    try:
        return dt.date.fromisoformat(text)
    except ValueError:
        raise argparse.ArgumentTypeError("use YYYY-MM-DD") from None


def _plant_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--outside", type=float, default=-2.0, help="mean outside temperature in °C (without --seasonal)")
    p.add_argument("--seasonal", action="store_true", help="outside temperature follows the calendar and the weather")
    p.add_argument("--date", type=iso_date, default=START_DATE, help="first plant day, YYYY-MM-DD (default 2026-01-01)")
    p.add_argument("--db", metavar="FILE", help="SQLite plant log; continues where an existing log ends")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="haussim", description=__doc__)
    parser.add_argument("--version", action="version", version=f"haussim {__version__}")
    sub = parser.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("run", help="run the house and open the browser HMI")
    run.add_argument("--host", default="127.0.0.1", help="address to listen on (default 127.0.0.1)")
    run.add_argument("--http-port", type=port_number, default=8080, help="HMI port (default 8080)")
    run.add_argument("--speed", type=int, choices=SPEEDS, default=120, help="simulated seconds per real second")
    run.add_argument("--no-browser", action="store_true", help="do not open a browser")
    _plant_args(run)
    run.set_defaults(func=cmd_run)

    sim = sub.add_parser("simulate", help="run headless; prints hours, or months when logging to --db")
    sim.add_argument("--days", type=float, default=1.0)
    sim.add_argument("--evu", action="append", default=[], metavar="HH:MM-HH:MM", help="grid operator lock window")
    sim.add_argument("--every", type=float, default=60.0, metavar="SECONDS", help="log a sample every N plant seconds")
    _plant_args(sim)
    sim.set_defaults(func=cmd_simulate)

    rep = sub.add_parser("report", help="print the monthly figures of a plant log")
    rep.add_argument("db", metavar="FILE")
    rep.set_defaults(func=cmd_report)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
