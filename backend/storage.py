import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from backend.bilibili import Dynamic


def database_path() -> Path:
    return Path(os.getenv("RHYTHM_DATABASE_PATH", "data/rhythm_calendar.sqlite3"))


@contextmanager
def connect(path: str | Path | None = None) -> Iterator[sqlite3.Connection]:
    target = Path(path) if path else database_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(target)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def initialize_database(path: str | Path | None = None) -> None:
    with connect(path) as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS dynamics (
                dynamic_id TEXT PRIMARY KEY,
                game TEXT NOT NULL,
                uid TEXT NOT NULL,
                text TEXT NOT NULL,
                publish_time TEXT NOT NULL,
                url TEXT NOT NULL,
                dynamic_type TEXT NOT NULL,
                raw_json TEXT,
                fetched_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS fetch_status (
                source TEXT PRIMARY KEY,
                last_attempt_at TEXT NOT NULL,
                last_success_at TEXT,
                last_error TEXT
            );
            """
        )


def save_dynamics(items: list[Dynamic], path: str | Path | None = None) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with connect(path) as db:
        db.executemany(
            """
            INSERT INTO dynamics
                (dynamic_id, game, uid, text, publish_time, url, dynamic_type, raw_json, fetched_at)
            VALUES (?, 'Arcaea', ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(dynamic_id) DO UPDATE SET
                text=excluded.text, publish_time=excluded.publish_time,
                url=excluded.url, dynamic_type=excluded.dynamic_type,
                raw_json=excluded.raw_json, fetched_at=excluded.fetched_at
            """,
            [
                (
                    item.dynamic_id,
                    item.uid,
                    item.text,
                    item.publish_time.isoformat(),
                    item.url,
                    item.dynamic_type,
                    json.dumps(item.to_dict(), ensure_ascii=False),
                    now,
                )
                for item in items
            ],
        )


def record_fetch_result(error: str | None, path: str | Path | None = None) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with connect(path) as db:
        db.execute(
            """
            INSERT INTO fetch_status(source, last_attempt_at, last_success_at, last_error)
            VALUES ('arcaea_bilibili', ?, ?, ?)
            ON CONFLICT(source) DO UPDATE SET
                last_attempt_at=excluded.last_attempt_at,
                last_success_at=CASE WHEN excluded.last_error IS NULL
                    THEN excluded.last_success_at ELSE fetch_status.last_success_at END,
                last_error=excluded.last_error
            """,
            (now, now if error is None else None, error),
        )


def latest_dynamics(limit: int = 10, path: str | Path | None = None) -> list[dict[str, str]]:
    with connect(path) as db:
        rows = db.execute(
            """SELECT dynamic_id, game, uid, text, publish_time, url, dynamic_type, fetched_at
               FROM dynamics ORDER BY publish_time DESC LIMIT ?""",
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_fetch_status(path: str | Path | None = None) -> dict[str, str | None]:
    with connect(path) as db:
        row = db.execute(
            "SELECT last_attempt_at, last_success_at, last_error FROM fetch_status "
            "WHERE source='arcaea_bilibili'"
        ).fetchone()
    return dict(row) if row else {
        "last_attempt_at": None,
        "last_success_at": None,
        "last_error": None,
    }
