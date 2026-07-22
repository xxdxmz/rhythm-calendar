from backend.parser import parse_arcaea_event, parse_arcaea_events


def dynamic(text: str, publish_time: str = "2026-06-23T00:00:00+00:00") -> dict:
    return {
        "dynamic_id": "123",
        "text": text,
        "publish_time": publish_time,
        "url": "https://www.bilibili.com/opus/123",
    }


def test_extracts_pack_release_date() -> None:
    event = parse_arcaea_event(
        dynamic("Arcaea v6.15版本将迎来全新曲包。\n6月25日起开放获取。")
    )
    assert event is not None
    assert event["event_date"] == "2026-06-25"
    assert event["event_type"] == "PACK_RELEASE"


def test_classifies_song_without_version_keyword() -> None:
    event = parse_arcaea_event(dynamic("全新单曲将于6月25日加入回忆档案馆。"))
    assert event is not None
    assert event["event_type"] == "SONG_ADD"


def test_rolls_january_into_next_year() -> None:
    event = parse_arcaea_event(
        dynamic("新曲包将于1月2日上线", "2026-12-28T00:00:00+00:00")
    )
    assert event is not None
    assert event["event_date"] == "2027-01-02"


def test_ignores_announcement_without_date() -> None:
    assert parse_arcaea_event(dynamic("全新内容即将到来")) is None


def test_results_are_sorted_by_event_date() -> None:
    first = dynamic("单曲将于6月25日加入")
    second = {**dynamic("单曲将于6月28日加入"), "dynamic_id": "456"}
    assert [item["event_date"] for item in parse_arcaea_events([first, second])] == [
        "2026-06-28",
        "2026-06-25",
    ]
