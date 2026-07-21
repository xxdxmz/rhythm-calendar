"""Fetch Arcaea dynamics and export a frontend-friendly static snapshot."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from backend.services import refresh_arcaea
from backend.bilibili import BilibiliError
from backend.storage import get_fetch_status, initialize_database, latest_dynamics

GAMES = [{"id": 1, "name": "Arcaea", "display_name": "Arcaea", "enabled": True}]


def export_snapshot(
    output: Path,
    *,
    refresh: bool = True,
    limit: int = 50,
    fallback: Path | None = None,
) -> dict:
    initialize_database()
    if refresh:
        try:
            refresh_arcaea()
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
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "games": GAMES,
        "dynamics": latest_dynamics(limit),
        "status": {**status, "stale": bool(status["last_error"])},
    }
    if not payload["dynamics"]:
        raise RuntimeError("No dynamics are available; refusing to publish an empty snapshot")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=50)
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
