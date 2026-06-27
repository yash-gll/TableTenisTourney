import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import (
    admin_players,
    auth,
    health,
    leaderboards,
    matches,
    players,
    teams,
    tournaments,
)
from app.core.config import settings
from app.core.errors import AppError, app_error_handler, http_error_handler

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Table Tennis Tournament Platform", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(AppError, app_error_handler)  # type: ignore[arg-type]
app.add_exception_handler(HTTPException, http_error_handler)  # type: ignore[arg-type]

API_PREFIX = "/api/v1"
app.include_router(health.router, prefix=API_PREFIX)
app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(players.router, prefix=API_PREFIX)
app.include_router(admin_players.router, prefix=API_PREFIX)
app.include_router(tournaments.router, prefix=API_PREFIX)
app.include_router(teams.router, prefix=API_PREFIX)
app.include_router(matches.router, prefix=API_PREFIX)
app.include_router(leaderboards.router, prefix=API_PREFIX)


@app.get("/")
def root() -> dict:
    return {"service": "tt-tourney", "docs": "/docs", "health": f"{API_PREFIX}/health"}
