import os
import time
from collections.abc import Callable

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


def refresh_all_accounts(
    progress: Callable[[str], None] | None = None,
) -> dict[str, object]:
    """Refresh every configured account while preserving cache on partial failures."""
    initialize_database()
    successes: dict[str, int] = {}
    errors: dict[str, str] = {}
    delay_seconds = max(float(os.getenv("BILIBILI_ACCOUNT_DELAY_SECONDS", "2.5")), 0)
    for index, account in enumerate(ACCOUNTS):
        if progress:
            progress(f"[{index + 1}/{len(ACCOUNTS)}] 正在采集 {account.display_name}...")
        try:
            items = fetch_account_dynamics(account)
            save_dynamics(items, game=account.display_name)
            record_fetch_result(None, source=account.source)
            successes[account.name] = len(items)
            if progress:
                progress(
                    f"[{index + 1}/{len(ACCOUNTS)}] {account.display_name}：成功，"
                    f"获得 {len(items)} 条动态"
                )
        except BilibiliError as exc:
            message = str(exc)
            record_fetch_result(message, source=account.source)
            errors[account.name] = message
            if progress:
                progress(f"[{index + 1}/{len(ACCOUNTS)}] {account.display_name}：失败，保留缓存")
        if delay_seconds and index < len(ACCOUNTS) - 1:
            time.sleep(delay_seconds)
    if not successes:
        raise BilibiliError("All configured Bilibili accounts failed to refresh")
    return {"successes": successes, "errors": errors}
