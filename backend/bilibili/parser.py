from datetime import datetime, timezone
from typing import Any

from .models import Dynamic


def _text_from_item(item: dict[str, Any]) -> str:
    modules = item.get("modules") or {}
    module_dynamic = modules.get("module_dynamic") or {}
    major = module_dynamic.get("major") or {}

    description = module_dynamic.get("desc") or {}
    text = description.get("text") or ""
    if text:
        return text.strip()

    # 视频投稿动态的正文可能为空，此时使用投稿标题，避免丢失公告信息。
    for kind in ("archive", "article", "opus", "draw"):
        payload = major.get(kind) or {}
        candidate = payload.get("title") or payload.get("desc") or payload.get("summary", {}).get("text")
        if candidate:
            return str(candidate).strip()
    return ""


def parse_dynamic_item(item: dict[str, Any], uid: str) -> Dynamic:
    dynamic_id = str(item.get("id_str") or item.get("id") or "")
    if not dynamic_id:
        raise ValueError("dynamic item does not contain an id")

    author = (item.get("modules") or {}).get("module_author") or {}
    timestamp = int(author.get("pub_ts") or 0)
    published = datetime.fromtimestamp(timestamp, tz=timezone.utc)

    return Dynamic(
        dynamic_id=dynamic_id,
        uid=str(uid),
        text=_text_from_item(item),
        publish_time=published,
        url=f"https://www.bilibili.com/opus/{dynamic_id}",
        dynamic_type=str(item.get("type") or "UNKNOWN"),
    )


def parse_dynamic_feed(payload: dict[str, Any], uid: str) -> list[Dynamic]:
    items = ((payload.get("data") or {}).get("items") or [])
    return [parse_dynamic_item(item, uid) for item in items]
