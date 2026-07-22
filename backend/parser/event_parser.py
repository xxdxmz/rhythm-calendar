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


def _date_from_match(match: re.Match[str], published: date) -> date | None:
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


def _extract_dates(text: str, published: date) -> list[tuple[re.Match[str], date]]:
    results: list[tuple[re.Match[str], date]] = []
    for match in DATE_PATTERN.finditer(text):
        candidate = _date_from_match(match, published)
        if candidate is not None:
            results.append((match, candidate))
    return results


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


def _sentence_at(text: str, position: int) -> str:
    boundaries = "\n。！？!?#"
    start = max((text.rfind(char, 0, position) for char in boundaries), default=-1) + 1
    ends = [text.find(char, position) for char in boundaries]
    valid_ends = [end for end in ends if end >= 0]
    end = min(valid_ends) if valid_ends else len(text)
    return text[start:end].strip()


def _build_event(
    dynamic: dict,
    *,
    event_date: date,
    event_type: str,
    title: str,
    index: int,
    event_end_date: date | None = None,
) -> dict:
    dynamic_id = str(dynamic["dynamic_id"])
    game = str(dynamic.get("game") or "Arcaea")
    event = {
        "id": f"event-{dynamic_id}-{index}",
        "game": game,
        "source_dynamic_id": dynamic_id,
        "title": title,
        "description": str(dynamic.get("text", "")).strip(),
        "event_type": event_type,
        "event_date": event_date.isoformat(),
        "url": dynamic.get("url", ""),
        "status": "AUTO_PARSED",
    }
    if event_end_date and event_end_date > event_date:
        event["event_end_date"] = event_end_date.isoformat()
    return event


def _parse_dynamic_events(dynamic: dict) -> list[dict]:
    text = str(dynamic.get("text", "")).strip()
    if not text:
        return []
    published = _publication_date(dynamic["publish_time"])
    matches = _extract_dates(text, published)
    if not matches:
        return []

    event_type = _event_type(text)
    # A “start 至 end” range is one event. Repeated mentions of its start date
    # are collapsed, so an activity announcement does not create three cards.
    range_pair: tuple[date, date] | None = None
    for current, following in zip(matches, matches[1:]):
        separator = text[current[0].end() : following[0].start()]
        if re.search(r"(?:至|到|—|-)", separator):
            range_pair = (current[1], following[1])
            break

    unique_dates: list[tuple[re.Match[str], date]] = []
    seen: set[date] = set()
    for match, candidate in matches:
        if candidate not in seen:
            unique_dates.append((match, candidate))
            seen.add(candidate)

    events: list[dict] = []
    for index, (match, candidate) in enumerate(unique_dates, start=1):
        if range_pair and candidate == range_pair[1]:
            continue
        context = _sentence_at(text, match.start())
        events.append(
            _build_event(
                dynamic,
                event_date=candidate,
                event_end_date=range_pair[1] if range_pair and candidate == range_pair[0] else None,
                event_type=event_type,
                title=(context or _title(text, event_type))[:80],
                index=index,
            )
        )
    return events


def parse_arcaea_event(dynamic: dict) -> dict | None:
    events = _parse_dynamic_events(dynamic)
    return events[0] if events else None


def parse_arcaea_events(dynamics: Iterable[dict]) -> list[dict]:
    events = [event for item in dynamics for event in _parse_dynamic_events(item)]
    return sorted(
        events,
        key=lambda event: (event["event_date"], event["source_dynamic_id"]),
        reverse=True,
    )


def parse_events(dynamics: Iterable[dict]) -> list[dict]:
    """Parse configured games with the shared date and keyword rules."""
    return parse_arcaea_events(dynamics)
