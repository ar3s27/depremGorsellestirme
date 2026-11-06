"""SQLite deposu: depremler ve Telegram uyarı aboneleri.

Tek bağlantı ve kilit kullanılır; sorgular milisaniyeler sürer. Async kodda asyncio.to_thread ile,
FastAPI'de senkron route'larda (thread havuzu) çağrılır.
"""
from __future__ import annotations

import sqlite3
import threading
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path

from .models import Quake, from_iso, to_iso, utcnow

FIELDS = ("id", "time", "lat", "lon", "depth", "mag", "mag_type", "location", "province", "district", "country")

SCHEMA = """
CREATE TABLE IF NOT EXISTS quakes (
    id         TEXT PRIMARY KEY,
    time       TEXT NOT NULL,
    lat        REAL NOT NULL,
    lon        REAL NOT NULL,
    depth      REAL NOT NULL,
    mag        REAL NOT NULL,
    mag_type   TEXT NOT NULL,
    location   TEXT NOT NULL,
    province   TEXT,
    district   TEXT,
    country    TEXT,
    first_seen TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS quakes_time ON quakes (time);

CREATE TABLE IF NOT EXISTS subscribers (
    chat_id    INTEGER PRIMARY KEY,
    min_mag    REAL NOT NULL,
    created_at TEXT NOT NULL
);
"""


class Store:
    def __init__(self, path: str):
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._db = sqlite3.connect(path, check_same_thread=False, isolation_level=None)
        self._db.row_factory = sqlite3.Row
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.execute("PRAGMA synchronous=NORMAL")
        self._db.executescript(SCHEMA)

    def close(self) -> None:
        with self._lock:
            self._db.close()

    @staticmethod
    def _quake(row: sqlite3.Row) -> Quake:
        return Quake(**{name: row[name] for name in FIELDS})

    # ── depremler ────────────────────────────────────────────────────────

    def upsert(self, quakes: Iterable[Quake]) -> tuple[list[Quake], list[Quake]]:
        """Kayıtları ekler/günceller. (yeni, değişen) listelerini döndürür; aynı kalanlar sayılmaz."""
        new: list[Quake] = []
        changed: list[Quake] = []
        now = to_iso(utcnow())
        columns = ", ".join(FIELDS)
        marks = ", ".join("?" for _ in FIELDS)
        updates = ", ".join(f"{name} = ?" for name in FIELDS[1:])
        with self._lock:
            self._db.execute("BEGIN")
            try:
                for quake in quakes:
                    values = tuple(getattr(quake, name) for name in FIELDS)
                    row = self._db.execute("SELECT * FROM quakes WHERE id = ?", (quake.id,)).fetchone()
                    if row is None:
                        self._db.execute(
                            f"INSERT INTO quakes ({columns}, first_seen, updated_at) VALUES ({marks}, ?, ?)",
                            values + (now, now),
                        )
                        new.append(quake)
                    elif self._quake(row) != quake:
                        self._db.execute(
                            f"UPDATE quakes SET {updates}, updated_at = ? WHERE id = ?",
                            values[1:] + (now, quake.id),
                        )
                        changed.append(quake)
                self._db.execute("COMMIT")
            except BaseException:
                self._db.execute("ROLLBACK")
                raise
        return new, changed

    def recent(
        self,
        since: datetime,
        min_mag: float = 0.0,
        limit: int | None = None,
        until: datetime | None = None,
    ) -> list[Quake]:
        """since (dahil) sonrasındaki depremler, en yeniden eskiye."""
        sql = "SELECT * FROM quakes WHERE time >= ? AND mag >= ?"
        params: list = [to_iso(since), min_mag]
        if until is not None:
            sql += " AND time <= ?"
            params.append(to_iso(until))
        sql += " ORDER BY time DESC, id DESC"
        if limit is not None:
            sql += " LIMIT ?"
            params.append(limit)
        with self._lock:
            rows = self._db.execute(sql, params).fetchall()
        return [self._quake(row) for row in rows]

    def get(self, quake_id: str) -> Quake | None:
        with self._lock:
            row = self._db.execute("SELECT * FROM quakes WHERE id = ?", (quake_id,)).fetchone()
        return self._quake(row) if row else None

    def latest_time(self) -> datetime | None:
        with self._lock:
            value = self._db.execute("SELECT MAX(time) FROM quakes").fetchone()[0]
        return from_iso(value) if value else None

    def oldest_time(self) -> datetime | None:
        with self._lock:
            value = self._db.execute("SELECT MIN(time) FROM quakes").fetchone()[0]
        return from_iso(value) if value else None

    def count(self) -> int:
        with self._lock:
            return self._db.execute("SELECT COUNT(*) FROM quakes").fetchone()[0]

    # ── Telegram aboneleri ───────────────────────────────────────────────

    def subscribe(self, chat_id: int, min_mag: float) -> None:
        with self._lock:
            self._db.execute(
                "INSERT INTO subscribers (chat_id, min_mag, created_at) VALUES (?, ?, ?) "
                "ON CONFLICT (chat_id) DO UPDATE SET min_mag = excluded.min_mag",
                (chat_id, min_mag, to_iso(utcnow())),
            )

    def unsubscribe(self, chat_id: int) -> bool:
        with self._lock:
            return self._db.execute("DELETE FROM subscribers WHERE chat_id = ?", (chat_id,)).rowcount > 0

    def subscription(self, chat_id: int) -> float | None:
        with self._lock:
            row = self._db.execute("SELECT min_mag FROM subscribers WHERE chat_id = ?", (chat_id,)).fetchone()
        return row[0] if row else None

    def subscribers_for(self, mag: float) -> list[int]:
        with self._lock:
            rows = self._db.execute("SELECT chat_id FROM subscribers WHERE min_mag <= ?", (mag,)).fetchall()
        return [row[0] for row in rows]
