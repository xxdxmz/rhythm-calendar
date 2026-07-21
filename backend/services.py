from backend.bilibili import BilibiliError
from backend.fetchers.arcaea import fetch_arcaea_dynamics
from backend.storage import initialize_database, record_fetch_result, save_dynamics


def refresh_arcaea() -> int:
    """Refresh cached data; preserve old rows when the remote source fails."""
    initialize_database()
    try:
        items = fetch_arcaea_dynamics()
    except BilibiliError as exc:
        record_fetch_result(str(exc))
        raise
    save_dynamics(items)
    record_fetch_result(None)
    return len(items)
