from datetime import datetime, timezone
from pathlib import Path

from backend.bilibili import Dynamic
from backend.storage import (
    get_fetch_status,
    initialize_database,
    latest_dynamics,
    record_fetch_result,
    save_dynamics,
)


def test_cache_survives_failed_refresh(tmp_path: Path) -> None:
    database = tmp_path / "cache.sqlite3"
    initialize_database(database)
    save_dynamics(
        [
            Dynamic(
                dynamic_id="1",
                uid="404145357",
                text="cached announcement",
                publish_time=datetime(2026, 7, 21, tzinfo=timezone.utc),
                url="https://www.bilibili.com/opus/1",
                dynamic_type="DYNAMIC_TYPE_WORD",
            )
        ],
        database,
    )
    record_fetch_result(None, database)
    record_fetch_result("temporary risk control", database)

    assert latest_dynamics(10, database)[0]["text"] == "cached announcement"
    status = get_fetch_status(database)
    assert status["last_success_at"] is not None
    assert status["last_error"] == "temporary risk control"
