"""Fetch configured music-game dynamics and export a static snapshot."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from backend.services import refresh_all_accounts
from backend.bilibili import BilibiliError
from backend.storage import get_fetch_status, initialize_database, latest_dynamics
from backend.parser import parse_events
from backend.accounts import GAMES

def export_snapshot(
    output: Path,
    *,
    refresh: bool = True,
    limit: int = 200,
    fallback: Path | None = None,
) -> dict:
    initialize_database()
    if refresh:
        try:
            refresh_all_accounts()
        except BilibiliError as exc:
            if fallback is None or not fallback.exists():
                raise
            payload = json.loads(fallback.read_text(encoding="utf-8"))
            payload["status"] = {
                **payload.get("status", {}),
                "last_attempt_at": datetime.now(timezone.utc).isoformat(),
                "last_error": f"Cloud collection unavailable: {exc}",
                "stale": True,
            }
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            print(
                f"Collection failed; published {len(payload.get('dynamics', []))} "
                "cached dynamics as stale data"
            )
            return payload
    status = get_fetch_status()
    dynamics = latest_dynamics(limit)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "games": GAMES,
        "dynamics": dynamics,
        "events": parse_events(dynamics),
        "status": status,
    }
    if not payload["dynamics"]:
        raise RuntimeError("No dynamics are available; refusing to publish an empty snapshot")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=200)
    parser.add_argument("--from-cache", action="store_true")
    parser.add_argument(
        "--fallback",
        type=Path,
        help="Publish this existing snapshot as stale data if collection is blocked",
    )
    args = parser.parse_args()
    payload = export_snapshot(
        args.output,
        refresh=not args.from_cache,
        limit=args.limit,
        fallback=args.fallback,
    )
    print(f"Exported {len(payload['dynamics'])} dynamics to {args.output}")


if __name__ == "__main__":
    main()
