"""Build the GitHub Pages demo: the HMI, the Python sources it runs in the
browser with Pyodide, and a simulated sample year for the report view.

    python tools/build_site.py site                 # simulates the year (about 4 minutes)
    python tools/build_site.py site --year year.db  # reuses a year simulated before
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACKAGE = ROOT / "src" / "haussim"
MODULES = ["__init__", "process", "electrical", "plc", "sim", "commands", "history"]  # keep in sync with hmi.js
YEAR_ARGS = ["simulate", "--days", "365", "--seasonal", "--date", "2026-01-01", "--every", "900"]


def main(out: Path, year: Path | None) -> None:
    # Read the year first: it may sit inside the folder that is emptied next.
    year_bytes = year.read_bytes() if year else None
    # Empty the folder rather than delete it, so a preview server running
    # inside it (python -m http.server) survives a rebuild.
    out.mkdir(parents=True, exist_ok=True)
    for child in out.iterdir():
        shutil.rmtree(child) if child.is_dir() else child.unlink()
    shutil.copytree(PACKAGE / "static", out, dirs_exist_ok=True)
    index = out / "index.html"
    html = index.read_text(encoding="utf-8")
    index.write_text(html.replace('<html lang="de">', '<html lang="de" data-demo>', 1), encoding="utf-8")
    py = out / "py" / "haussim"
    py.mkdir(parents=True)
    for name in MODULES:
        shutil.copy(PACKAGE / f"{name}.py", py)
    if year_bytes:
        (out / "year.db").write_bytes(year_bytes)
    else:
        subprocess.run(
            [sys.executable, "-m", "haussim.cli", *YEAR_ARGS, "--db", str((out / "year.db").resolve())],
            cwd=ROOT / "src",
            check=True,
        )
    (out / ".nojekyll").touch()
    print(f"Built {out}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("out", nargs="?", default="site", type=Path)
    parser.add_argument("--year", type=Path, help="copy this plant log instead of simulating a year")
    args = parser.parse_args()
    main(args.out, args.year)
