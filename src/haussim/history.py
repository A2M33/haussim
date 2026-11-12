"""Plant history in SQLite (standard library, no server).

One row per sample. The energy, start and run-time columns are meter
readings that only count up, so a day's energy is the last reading of the day
minus the last reading of the day before. That stays exact whether a sample
is taken every minute or every 15 minutes.
"""

from __future__ import annotations

import sqlite3
import threading
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS samples (
    day        TEXT    NOT NULL,  -- ISO date of the plant clock
    minute     INTEGER NOT NULL,  -- minute of the day
    outside    REAL, room REAL, buffer REAL, flow_target REAL,
    heat_w     REAL,              -- heat pump output, negative while defrosting
    elec_w     REAL,              -- heat pump and rod input
    house_w    REAL,              -- household circuits
    hp_on      INTEGER, rod_on INTEGER, evu INTEGER,
    heat_kwh   REAL, elec_kwh REAL, rod_kwh REAL, house_kwh REAL,  -- meters
    starts     INTEGER, run_s REAL, evu_s REAL,                    -- counters
    PRIMARY KEY (day, minute)
);
CREATE TABLE IF NOT EXISTS events (
    day TEXT NOT NULL, minute INTEGER NOT NULL, kind TEXT NOT NULL, text TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS events_day ON events(day);
"""
METERS = ("heat_kwh", "elec_kwh", "rod_kwh", "house_kwh", "starts", "run_s", "evu_s")

# Per day: the last meter readings, and the day before's last readings.
_DAYS = """
WITH last AS (
    SELECT s.* FROM samples s
    JOIN (SELECT day, MAX(minute) AS m FROM samples GROUP BY day) x ON s.day = x.day AND s.minute = x.m
),
first AS (
    SELECT s.* FROM samples s
    JOIN (SELECT day, MIN(minute) AS m FROM samples GROUP BY day) x ON s.day = x.day AND s.minute = x.m
),
stats AS (
    SELECT day, AVG(outside) AS outside, MIN(room) AS room_min, AVG(room) AS room_avg FROM samples GROUP BY day
),
d AS (
    SELECT l.day,
        {deltas}
    FROM last l JOIN first f ON f.day = l.day
)
SELECT d.*, stats.outside, stats.room_min, stats.room_avg FROM d JOIN stats ON stats.day = d.day
"""


def _delta(col: str) -> str:
    # The first day has no day before it, so it starts from its own first reading.
    return f"l.{col} - COALESCE(LAG(l.{col}) OVER (ORDER BY l.day), f.{col}) AS {col}"


class Store:
    def __init__(self, path: str | Path = ":memory:") -> None:
        self.path = str(path)
        self.lock = threading.Lock()
        self.db = sqlite3.connect(self.path, check_same_thread=False)
        self.db.executescript(SCHEMA)

    def close(self) -> None:
        with self.lock:
            self.db.close()

    # Writing -------------------------------------------------------------------

    def last(self) -> dict | None:
        """The newest sample, to continue a plant log where it ended."""
        with self.lock:
            cur = self.db.execute("SELECT * FROM samples ORDER BY day DESC, minute DESC LIMIT 1")
            row = cur.fetchone()
            return dict(zip([c[0] for c in cur.description], row)) if row else None

    def record(self, sample: dict) -> None:
        cols = list(sample)
        with self.lock:
            self.db.execute(
                f"INSERT OR REPLACE INTO samples ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})",
                [sample[c] for c in cols],
            )

    def event(self, day: str, minute: int, kind: str, text: str) -> None:
        with self.lock:
            self.db.execute("INSERT INTO events VALUES (?, ?, ?, ?)", (day, minute, kind, text))

    def commit(self) -> None:
        with self.lock:
            self.db.commit()

    # Reports -------------------------------------------------------------------

    def _rows(self, sql: str, args=()) -> list[dict]:
        with self.lock:
            cur = self.db.execute(sql, args)
            names = [c[0] for c in cur.description]
            return [dict(zip(names, r)) for r in cur.fetchall()]

    def days(self, month: str | None = None) -> list[dict]:
        sql = _DAYS.format(deltas=",\n        ".join(_delta(c) for c in METERS))
        rows = self._rows(sql + " ORDER BY d.day")
        if month:
            rows = [r for r in rows if r["day"].startswith(month)]
        for r in rows:
            r["jaz"] = r["heat_kwh"] / r["elec_kwh"] if r["elec_kwh"] > 0.05 else None
        return rows

    def months(self) -> list[dict]:
        out: dict[str, dict] = {}
        for d in self.days():
            m = out.setdefault(d["day"][:7], {"month": d["day"][:7], "days": 0, "outside": 0.0, "room_min": None,
                                             **dict.fromkeys(METERS, 0.0)})
            m["days"] += 1
            m["outside"] += d["outside"]
            m["room_min"] = d["room_min"] if m["room_min"] is None else min(m["room_min"], d["room_min"])
            for c in METERS:
                m[c] += d[c]
        for m in out.values():
            m["outside"] /= m["days"]
            m["jaz"] = m["heat_kwh"] / m["elec_kwh"] if m["elec_kwh"] > 0.05 else None
        return list(out.values())

    def day_samples(self, day: str) -> list[list]:
        with self.lock:
            return [
                list(r)
                for r in self.db.execute(
                    "SELECT minute, outside, room, buffer, flow_target, heat_w, elec_w FROM samples "
                    "WHERE day = ? ORDER BY minute",
                    (day,),
                )
            ]

    def day_events(self, day: str) -> list[list]:
        with self.lock:
            return [list(r) for r in self.db.execute(
                "SELECT minute, kind, text FROM events WHERE day = ? ORDER BY rowid", (day,))]

    def report(self, what: str, arg: str | None = None):
        """The one entry point the HTTP server and the browser demo share."""
        if what == "months":
            return self.months()
        if what == "days":
            return self.days(arg)
        if what == "day":
            return {"samples": self.day_samples(arg or ""), "events": self.day_events(arg or "")}
        raise ValueError("what must be months, days or day")
