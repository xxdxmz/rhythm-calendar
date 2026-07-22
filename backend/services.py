from backend.bilibili import BilibiliError
from backend.accounts import ACCOUNTS
from backend.fetchers.accounts import fetch_account_dynamics
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


def refresh_all_accounts() -> dict[str, object]:
    """Refresh every configured account while preserving cache on partial failures."""
    initialize_database()
    successes: dict[str, int] = {}
    errors: dict[str, str] = {}
    for account in ACCOUNTS:
        try:
            items = fetch_account_dynamics(account)
            save_dynamics(items, game=account.display_name)
            record_fetch_result(None, source=account.source)
            successes[account.name] = len(items)
        except BilibiliError as exc:
            message = str(exc)
            record_fetch_result(message, source=account.source)
            errors[account.name] = message
    if not successes:
        raise BilibiliError("All configured Bilibili accounts failed to refresh")
    return {"successes": successes, "errors": errors}
