"""Rule-based event extraction for Arcaea announcements."""
from __future__ import annotations

import re
from datetime import date, datetime
from typing import Iterable


DATE_PATTERN = re.compile(
    r"(?:(?P<year>20\d{2})\s*年\s*)?"
    r"(?P<month>1[0-2]|0?[1-9])\s*月\s*"
    r"(?P<day>3[01]|[12]\d|0?[1-9])\s*日"
)

TYPE_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("COLLABORATION", ("联动", "合作", "collaboration", "collab")),
    ("MAINTENANCE", ("维护", "停机", "maintenance")),
    ("PACK_RELEASE", ("曲包", "pack", "chapter", "主线剧情")),
    ("SONG_ADD", ("新曲", "单曲", "曲目", "加入世界模式", "world extend")),
    ("VERSION_UPDATE", ("版本", "更新公告", "version", "update")),
    ("EVENT", ("活动", "限时", "返场", "地图")),
)


def _publication_date(value: str | datetime) -> date:
    if isinstance(value, datetime):
        return value.date()
    return datetime.fromisoformat(value.replace("Z", "+00:00")).date()


def _extract_date(text: str, published: date) -> date | None:
    match = DATE_PATTERN.search(text)
    if not match:
        return None
    year = int(match.group("year")) if match.group("year") else published.year
    month = int(match.group("month"))
    day = int(match.group("day"))
    try:
        candidate = date(year, month, day)
    except ValueError:
        return None

    # Around New Year, an undated January announcement made in December usually
    # refers to next year, while a December date mentioned in January is recent.
    if not match.group("year"):
        if published.month == 12 and month == 1:
            candidate = candidate.replace(year=year + 1)
        elif published.month == 1 and month == 12:
            candidate = candidate.replace(year=year - 1)
    return candidate


def _event_type(text: str) -> str:
    normalized = text.casefold()
    for event_type, keywords in TYPE_RULES:
        if any(keyword in normalized for keyword in keywords):
            return event_type
    return "EVENT"


def _title(text: str, event_type: str) -> str:
    first_line = next((line.strip() for line in text.splitlines() if line.strip()), "")
    if first_line:
        return first_line[:80]
    return {
        "VERSION_UPDATE": "Arcaea 版本更新",
        "PACK_RELEASE": "Arcaea 曲包更新",
        "SONG_ADD": "Arcaea 新曲更新",
        "COLLABORATION": "Arcaea 联动",
        "MAINTENANCE": "Arcaea 维护",
    }.get(event_type, "Arcaea 活动")


def parse_arcaea_event(dynamic: dict) -> dict | None:
    text = str(dynamic.get("text", "")).strip()
    if not text:
        return None
    published = _publication_date(dynamic["publish_time"])
    event_date = _extract_date(text, published)
    if event_date is None:
        return None
    event_type = _event_type(text)
    dynamic_id = str(dynamic["dynamic_id"])
    return {
        "id": f"arcaea-{dynamic_id}",
        "game": "Arcaea",
        "source_dynamic_id": dynamic_id,
        "title": _title(text, event_type),
        "description": text,
        "event_type": event_type,
        "event_date": event_date.isoformat(),
        "url": dynamic.get("url", ""),
        "status": "AUTO_PARSED",
    }


def parse_arcaea_events(dynamics: Iterable[dict]) -> list[dict]:
    events = [parse_arcaea_event(item) for item in dynamics]
    return sorted(
        (event for event in events if event is not None),
        key=lambda event: (event["event_date"], event["source_dynamic_id"]),
        reverse=True,
    )
