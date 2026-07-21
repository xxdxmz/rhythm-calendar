from datetime import datetime, timezone

from backend.bilibili import Dynamic
from backend.fetchers.arcaea import fetch_arcaea_dynamics


def dynamic(dynamic_id: str, text: str) -> Dynamic:
    return Dynamic(
        dynamic_id=dynamic_id,
        uid="404145357",
        text=text,
        publish_time=datetime(2026, 7, int(dynamic_id), tzinfo=timezone.utc),
        url=f"https://www.bilibili.com/opus/{dynamic_id}",
        dynamic_type="DYNAMIC_TYPE_DRAW",
    )


def test_empty_api_text_triggers_browser_fallback() -> None:
    class ApiClient:
        def get_user_dynamic(self, uid: str) -> list[Dynamic]:
            return [dynamic("1", "")]

    class BrowserClient:
        def get_user_dynamic(self, uid: str) -> list[Dynamic]:
            return [dynamic("2", "rendered"), dynamic("1", "completed")]

    result = fetch_arcaea_dynamics(ApiClient(), BrowserClient())  # type: ignore[arg-type]

    assert [item.text for item in result] == ["rendered", "completed"]
