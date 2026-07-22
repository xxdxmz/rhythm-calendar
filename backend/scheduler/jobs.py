import logging
import os

from apscheduler.schedulers.background import BackgroundScheduler

from backend.bilibili import BilibiliError
from backend.services import refresh_all_accounts

logger = logging.getLogger(__name__)


def refresh_accounts_safely() -> None:
    try:
        result = refresh_all_accounts()
        logger.info("Music-game caches refreshed: %s", result)
    except BilibiliError as exc:
        logger.warning("Account refresh failed; cached data remains available: %s", exc)


def create_scheduler() -> BackgroundScheduler:
    minutes = max(int(os.getenv("ARCAEA_FETCH_INTERVAL_MINUTES", "60")), 15)
    scheduler = BackgroundScheduler(timezone="Asia/Shanghai")
    scheduler.add_job(
        refresh_accounts_safely,
        "interval",
        minutes=minutes,
        id="refresh_accounts",
        max_instances=1,
        coalesce=True,
    )
    return scheduler
