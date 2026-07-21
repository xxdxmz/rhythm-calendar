"""Fetch Arcaea dynamics and export a frontend-friendly static snapshot."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from backend.services import refresh_arcaea
from backend.storage import get_fetch_status, initialize_database, latest_dynamics

GAMES = [{"id": 1, "name": "Arcaea", "display_name": "Arcaea", "enabled": True}]


def export_snapshot(output: Path, *, refresh: bool = True, limit: int = 50) -> dict:
    initialize_database()
    if refresh:
        refresh_arcaea()
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
    args = parser.parse_args()
    payload = export_snapshot(args.output, refresh=not args.from_cache, limit=args.limit)
    print(f"Exported {len(payload['dynamics'])} dynamics to {args.output}")


if __name__ == "__main__":
    main()
