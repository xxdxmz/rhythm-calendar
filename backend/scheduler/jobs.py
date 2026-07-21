import logging
import os

from apscheduler.schedulers.background import BackgroundScheduler

from backend.bilibili import BilibiliError
from backend.services import refresh_arcaea

logger = logging.getLogger(__name__)


def refresh_arcaea_safely() -> None:
    try:
        count = refresh_arcaea()
        logger.info("Arcaea cache refreshed: %s dynamics", count)
    except BilibiliError as exc:
        logger.warning("Arcaea refresh failed; cached data remains available: %s", exc)


def create_scheduler() -> BackgroundScheduler:
    minutes = max(int(os.getenv("ARCAEA_FETCH_INTERVAL_MINUTES", "60")), 15)
    scheduler = BackgroundScheduler(timezone="Asia/Shanghai")
    scheduler.add_job(
        refresh_arcaea_safely,
        "interval",
        minutes=minutes,
        id="refresh_arcaea",
        max_instances=1,
        coalesce=True,
    )
    return scheduler
