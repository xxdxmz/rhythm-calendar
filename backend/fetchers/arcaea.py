import argparse
import sys

from backend.bilibili import (
    BilibiliClient,
    BilibiliError,
    BrowserDynamicClient,
    Dynamic,
)
from backend.storage import initialize_database, latest_dynamics, record_fetch_result, save_dynamics

ARCAEA_BILIBILI_UID = "404145357"


def fetch_arcaea_dynamics(
    client: BilibiliClient | None = None,
    browser_client: BrowserDynamicClient | None = None,
) -> list[Dynamic]:
    api_client = client or BilibiliClient(raw_dir="data/raw/arcaea")
    try:
        items = api_client.get_user_dynamic(ARCAEA_BILIBILI_UID)
    except BilibiliError as api_error:
        try:
            items = (browser_client or BrowserDynamicClient(
                raw_dir="data/raw/arcaea/browser"
            )).get_user_dynamic(ARCAEA_BILIBILI_UID)
        except BilibiliError as browser_error:
            raise BilibiliError(
                f"API collection failed: {api_error}; browser fallback failed: {browser_error}"
            ) from browser_error
    else:
        if any(not item.text.strip() for item in items):
            items = (browser_client or BrowserDynamicClient(
                raw_dir="data/raw/arcaea/browser"
            )).get_user_dynamic(ARCAEA_BILIBILI_UID)
    return sorted(items, key=lambda item: item.publish_time, reverse=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch Arcaea official Bilibili dynamics")
    parser.add_argument("--limit", type=int, default=10, help="number of texts to print")
    args = parser.parse_args()
    initialize_database()

    try:
        dynamics = fetch_arcaea_dynamics()
    except BilibiliError as exc:
        print(f"Fetch failed: {exc}", file=sys.stderr)
        record_fetch_result(str(exc))
        cached = latest_dynamics(args.limit)
        if not cached:
            return 1
        print("Using stale cached data:", file=sys.stderr)
        for index, item in enumerate(cached, start=1):
            print(f"[{index}] {item['publish_time']} {item['url']}")
            print(item["text"] or "（无文字内容）")
            print()
        return 0

    save_dynamics(dynamics)
    record_fetch_result(None)

    for index, dynamic in enumerate(dynamics[: max(args.limit, 0)], start=1):
        text = dynamic.text.replace("\r", "").strip() or "（无文字内容）"
        print(f"[{index}] {dynamic.publish_time.astimezone().isoformat()} {dynamic.url}")
        print(text)
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
