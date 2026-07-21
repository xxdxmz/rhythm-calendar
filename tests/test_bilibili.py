import json
from pathlib import Path

import httpx
import pytest

from backend.bilibili import BilibiliClient, BilibiliRiskControlError

FIXTURE = Path(__file__).parent / "fixtures" / "arcaea_feed.json"


def test_fetch_parses_and_saves_raw_response(tmp_path: Path) -> None:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/feed/space"):
            assert request.url.params["host_mid"] == "404145357"
            return httpx.Response(200, json=payload)
        if request.url.path.endswith("/finger/spi"):
            return httpx.Response(200, json={"code": 0, "data": {"b_3": "visitor-3", "b_4": "visitor-4"}})
        return httpx.Response(200, text="<html></html>")

    client = BilibiliClient(raw_dir=tmp_path, transport=httpx.MockTransport(handler))
    dynamics = client.get_user_dynamic("404145357")

    assert [item.text for item in dynamics] == [
        "在3月9日开启的6.13版本中，七首歌曲将新增Beyond难度。",
        "Arcaea 新曲预告",
    ]
    assert dynamics[0].url.endswith("/1175351990658531334")
    assert len(list((tmp_path / "404145357").glob("*.json"))) == 1


def test_risk_control_is_not_treated_as_empty_feed(tmp_path: Path) -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(412, json={"code": -352, "message": "-352"})
    )
    client = BilibiliClient(raw_dir=tmp_path, transport=transport)

    with pytest.raises(BilibiliRiskControlError, match="mode=anonymous visitor"):
        client.get_user_dynamic("404145357")

    assert len(list((tmp_path / "404145357").glob("*.error.json"))) == 1


def test_dedicated_account_cookie_is_loaded_from_secret_file(tmp_path: Path) -> None:
    secret = tmp_path / "bilibili_cookie.txt"
    secret.write_text("SESSDATA=dedicated-secret; bili_jct=csrf-secret", encoding="utf-8")
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/feed/space"):
            seen["cookie"] = request.headers.get("cookie", "")
            return httpx.Response(200, json={"code": 0, "data": {"items": []}})
        if request.url.path.endswith("/finger/spi"):
            return httpx.Response(200, json={"code": 0, "data": {}})
        return httpx.Response(200, text="<html></html>")

    client = BilibiliClient(
        raw_dir=tmp_path / "raw",
        cookie_file=secret,
        transport=httpx.MockTransport(handler),
    )
    client.get_user_dynamic("404145357")

    assert client.authenticated is True
    assert "SESSDATA=dedicated-secret" in seen["cookie"]
    assert "bili_jct=csrf-secret" in seen["cookie"]
