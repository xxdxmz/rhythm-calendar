import json
import os
import re
import sys
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from playwright.sync_api import Browser, Page, Playwright, sync_playwright

from .client import BilibiliError
from .models import Dynamic
from .parser import parse_dynamic_feed


class BrowserDynamicClient:
    """Collect public dynamics through a real, logged-out browser session."""

    FEED_PATH = "/x/polymer/web-dynamic/v1/feed/space"
    CARD_SELECTOR = ".bili-dyn-list__item"
    TEXT_SELECTORS = (
        ".bili-dyn-content__orig__desc",
        ".dyn-card-opus__summary",
        ".bili-dyn-item__body",
    )

    def __init__(
        self,
        *,
        raw_dir: str | Path = "data/raw/browser",
        executable_path: str | Path | None = None,
        headless: bool | None = None,
        timeout_ms: int = 30_000,
    ) -> None:
        self.raw_dir = Path(raw_dir)
        discovered = Path(executable_path) if executable_path else self._discover_browser()
        self.executable_path = str(discovered) if discovered else None
        if headless is None:
            headless = os.getenv("BILIBILI_BROWSER_HEADLESS", "true").lower() not in {
                "0", "false", "no"
            }
        self.headless = headless
        self.timeout_ms = timeout_ms

    @staticmethod
    def _discover_browser() -> Path | None:
        configured = os.getenv("BILIBILI_BROWSER_EXECUTABLE", "")
        candidates = [
            Path(configured) if configured else None,
            Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
            Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
            Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
            Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
        ]
        for candidate in candidates:
            if candidate and candidate.is_file():
                return candidate
        if sys.platform != "win32":
            # Linux containers use the Chromium revision installed by Playwright.
            return None
        raise BilibiliError(
            "No Chromium browser found; set BILIBILI_BROWSER_EXECUTABLE"
        )

    @staticmethod
    def _clean_text(text: str) -> str:
        text = text.replace("\u200b", "").replace("\r", "").strip()
        return re.sub(r"(?:\n?\s*展开)\s*$", "", text).strip()

    def _save_result(
        self, uid: str, items: list[Dynamic], texts: list[str], feed: dict[str, Any]
    ) -> Path:
        target_dir = self.raw_dir / uid
        target_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
        target = target_dir / f"{stamp}.browser.json"
        target.write_text(
            json.dumps(
                {
                    "source": "anonymous_chromium_dom",
                    "uid": uid,
                    "feed": feed,
                    "items": [item.to_dict() for item in items],
                    "rendered_texts": texts,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        return target

    def _extract(self, page: Page) -> list[str]:
        page.wait_for_selector(self.CARD_SELECTOR, timeout=self.timeout_ms)
        cards = page.locator(self.CARD_SELECTOR)
        texts: list[str] = []
        for index in range(cards.count()):
            card = cards.nth(index)
            text = ""
            for selector in self.TEXT_SELECTORS:
                candidate = card.locator(selector)
                if candidate.count():
                    text = candidate.first.inner_text(timeout=self.timeout_ms)
                    if text.strip():
                        break
            texts.append(self._clean_text(text))
        return texts

    def get_user_dynamic(self, uid: str | int) -> list[Dynamic]:
        uid = str(uid)
        feed_payloads: list[dict[str, Any]] = []
        url = f"https://space.bilibili.com/{uid}/dynamic"

        try:
            with sync_playwright() as playwright:
                launch_options: dict[str, Any] = {"headless": self.headless}
                if self.executable_path:
                    launch_options["executable_path"] = self.executable_path
                browser = playwright.chromium.launch(**launch_options)
                try:
                    page = browser.new_page(locale="zh-CN")

                    def capture(response: Any) -> None:
                        if self.FEED_PATH not in response.url:
                            return
                        try:
                            payload = response.json()
                        except Exception:
                            return
                        if payload.get("code") == 0:
                            feed_payloads.append(payload)

                    page.on("response", capture)
                    page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)
                    rendered_texts = self._extract(page)
                finally:
                    browser.close()
        except BilibiliError:
            raise
        except Exception as exc:
            raise BilibiliError(f"Anonymous browser collection failed: {exc}") from exc

        if not feed_payloads:
            raise BilibiliError("Browser rendered the page but captured no valid dynamic feed")

        feed = feed_payloads[-1]
        items = parse_dynamic_feed(feed, uid)
        if len(rendered_texts) < len(items):
            raise BilibiliError(
                f"Browser rendered {len(rendered_texts)} cards for {len(items)} feed items"
            )

        completed = [
            replace(item, text=rendered_texts[index] or item.text)
            for index, item in enumerate(items)
        ]
        self._save_result(uid, completed, rendered_texts, feed)
        return completed
