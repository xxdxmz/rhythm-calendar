from contextlib import asynccontextmanager
import os

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from backend.scheduler.jobs import create_scheduler
from backend.storage import get_fetch_status, initialize_database, latest_dynamics as read_latest_dynamics


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    scheduler = create_scheduler()
    scheduler.start()
    app.state.scheduler = scheduler
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(title="Rhythm Calendar API", version="0.2.0", lifespan=lifespan)

allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/games")
def games() -> list[dict[str, object]]:
    return [{"id": 1, "name": "Arcaea", "display_name": "Arcaea", "enabled": True}]


@app.get("/api/dynamics/latest")
def latest_dynamics(limit: int = Query(default=10, ge=1, le=50)) -> list[dict[str, str]]:
    return latest_dynamics_from_cache(limit)


def latest_dynamics_from_cache(limit: int) -> list[dict[str, str]]:
    return read_latest_dynamics(limit)


@app.get("/api/dynamics/status")
def dynamics_status() -> dict[str, str | bool | None]:
    status = get_fetch_status()
    return {**status, "stale": bool(status["last_error"])}
