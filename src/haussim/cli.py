"""Command line: `haussim run` opens the HMI, `haussim simulate` prints a day."""

from __future__ import annotations

import argparse
import sys
import threading
import time
import webbrowser

from . import __version__
from .commands import SPEEDS
from .process import Process
from .sim import Simulator

TICK_S = 0.1


def _hhmm(clock_s: float) -> str:
    minute = int(clock_s // 60) % 1440
    return f"{minute // 60:02d}:{minute % 60:02d}"


def run_loop(sim: Simulator, stop: threading.Event) -> None:
    last = time.monotonic()
    while not stop.wait(TICK_S):
        now = time.monotonic()
        real, last = min(now - last, 1.0), now
        if not sim.paused:
            sim.step(real * sim.speed)


def cmd_run(args: argparse.Namespace) -> int:
    from .web import HmiServer  # sockets only when the HMI is wanted

    sim = Simulator(Process(outside_mean_c=args.outside))
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
    return 0


def cmd_simulate(args: argparse.Namespace) -> int:
    sim = Simulator(Process(outside_mean_c=args.outside, seed=1))
    windows = []
    for span in args.evu:
        start, end = span.split("-")
        windows.append(tuple(int(t[:2]) * 60 + int(t[3:]) for t in (start, end)))
    print("time   outside  room   buffer target  HP     rod  COP   kWh el  starts")
    for _hour in range(int(args.days * 24)):
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
    return 0


def port_number(text: str) -> int:
    port = int(text)
    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError("port must be 1 to 65535")
    return port


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="haussim", description=__doc__)
    parser.add_argument("--version", action="version", version=f"haussim {__version__}")
    sub = parser.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("run", help="run the house and open the browser HMI")
    run.add_argument("--host", default="127.0.0.1", help="address to listen on (default 127.0.0.1)")
    run.add_argument("--http-port", type=port_number, default=8080, help="HMI port (default 8080)")
    run.add_argument("--speed", type=int, choices=SPEEDS, default=120, help="simulated seconds per real second")
    run.add_argument("--outside", type=float, default=-2.0, help="mean outside temperature in °C")
    run.add_argument("--no-browser", action="store_true", help="do not open a browser")
    run.set_defaults(func=cmd_run)

    sim = sub.add_parser("simulate", help="run headless and print one line per simulated hour")
    sim.add_argument("--days", type=float, default=1.0)
    sim.add_argument("--outside", type=float, default=-2.0, help="mean outside temperature in °C")
    sim.add_argument("--evu", action="append", default=[], metavar="HH:MM-HH:MM", help="grid operator lock window")
    sim.set_defaults(func=cmd_simulate)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
