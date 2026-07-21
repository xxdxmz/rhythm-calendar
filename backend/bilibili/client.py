import json
import os
import time
from http.cookies import SimpleCookie
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from .models import Dynamic
from .parser import parse_dynamic_feed


class BilibiliError(RuntimeError):
    """Base error for an invalid Bilibili response."""


class BilibiliRiskControlError(BilibiliError):
    """Bilibili rejected an automated or anonymous request."""


class BilibiliClient:
    SPACE_FEED_URL = "https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/space"
    VISITOR_URL = "https://api.bilibili.com/x/frontend/finger/spi"

    def __init__(
        self,
        *,
        raw_dir: str | Path = "data/raw",
        cookie: str | None = None,
        cookie_file: str | Path | None = None,
        user_agent: str | None = None,
        timeout: float = 20.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.raw_dir = Path(raw_dir)
        self.account_cookie = self._read_account_cookie(cookie, cookie_file)
        self.user_agent = user_agent or os.getenv(
            "BILIBILI_USER_AGENT",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        )
        self.timeout = timeout
        self.transport = transport

    @staticmethod
    def _read_account_cookie(
        cookie: str | None, cookie_file: str | Path | None
    ) -> str:
        if cookie is not None:
            return cookie.strip()

        configured_file = cookie_file or os.getenv("BILIBILI_COOKIE_FILE", "")
        if configured_file:
            path = Path(configured_file)
            if path.is_file():
                return path.read_text(encoding="utf-8").strip()

        # Useful for hosting providers with encrypted environment secrets.
        return os.getenv("BILIBILI_COOKIE", "").strip()

    @property
    def authenticated(self) -> bool:
        return bool(self.account_cookie)

    def _install_account_cookies(self, client: httpx.Client) -> None:
        if not self.account_cookie:
            return
        parsed = SimpleCookie()
        try:
            parsed.load(self.account_cookie)
        except Exception as exc:
            raise BilibiliError("The configured Bilibili Cookie is malformed") from exc
        if not parsed:
            raise BilibiliError("The configured Bilibili Cookie is empty or malformed")
        for name, morsel in parsed.items():
            client.cookies.set(name, morsel.value, domain=".bilibili.com")

    def _headers(self, uid: str) -> dict[str, str]:
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Origin": "https://space.bilibili.com",
            "Referer": f"https://space.bilibili.com/{uid}/dynamic",
            "User-Agent": self.user_agent,
        }
        return headers

    def _initialize_visitor(self, client: httpx.Client, uid: str) -> None:
        """Create a logged-out Bilibili visitor session without account credentials."""
        # The space page sets buvid3/b_nut for ordinary logged-out visitors.
        client.get(f"https://space.bilibili.com/{uid}/dynamic")
        response = client.get(self.VISITOR_URL)
        if response.status_code != 200:
            return
        try:
            data = (response.json().get("data") or {})
        except ValueError:
            return
        if data.get("b_3"):
            client.cookies.set("buvid3", data["b_3"], domain=".bilibili.com")
        if data.get("b_4"):
            client.cookies.set("buvid4", data["b_4"], domain=".bilibili.com")
        if not client.cookies.get("b_nut"):
            client.cookies.set("b_nut", str(int(time.time())), domain=".bilibili.com")

    def _save_payload(self, uid: str, payload: Any, *, error: bool = False) -> Path:
        target_dir = self.raw_dir / str(uid)
        target_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
        suffix = ".error.json" if error else ".json"
        target = target_dir / f"{stamp}{suffix}"
        target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return target

    def get_user_dynamic(self, uid: str | int) -> list[Dynamic]:
        uid = str(uid)
        try:
            with httpx.Client(
                headers=self._headers(uid),
                timeout=self.timeout,
                follow_redirects=True,
                transport=self.transport,
            ) as client:
                self._install_account_cookies(client)
                self._initialize_visitor(client, uid)
                response = client.get(self.SPACE_FEED_URL, params={"host_mid": uid})
        except httpx.HTTPError as exc:
            raise BilibiliError(f"Bilibili request failed: {exc}") from exc

        try:
            payload = response.json()
        except ValueError as exc:
            payload = {"http_status": response.status_code, "body": response.text}
            saved = self._save_payload(uid, payload, error=True)
            raise BilibiliError(f"Bilibili returned non-JSON data; saved to {saved}") from exc

        code = payload.get("code")
        if response.status_code != 200 or code != 0:
            saved = self._save_payload(uid, payload, error=True)
            message = payload.get("message") or response.reason_phrase
            if response.status_code in {403, 412} or code in {-352, -412}:
                mode = "dedicated account" if self.authenticated else "anonymous visitor"
                raise BilibiliRiskControlError(
                    f"Bilibili risk control rejected the request ({response.status_code=}, "
                    f"code={code}, message={message!r}, mode={mode}). "
                    f"Raw response: {saved}"
                )
            raise BilibiliError(
                f"Bilibili API error ({response.status_code=}, code={code}, "
                f"message={message!r}); raw response: {saved}"
            )

        self._save_payload(uid, payload)
        return parse_dynamic_feed(payload, uid)
