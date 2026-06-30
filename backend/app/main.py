import logging
import time
import uuid

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import (
    admin_players,
    auth,
    brackets,
    health,
    history,
    leaderboards,
    matches,
    players,
    points,
    predictions,
    ratings,
    registrations,
    teams,
    tournaments,
)
from app.core.config import settings
from app.core.errors import AppError, app_error_handler, http_error_handler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app.request")

if settings.jwt_secret_is_default:
    logging.getLogger("app").warning(
        "JWT_SECRET is the default value — set a strong JWT_SECRET in production."
    )

app = FastAPI(title="Table Tennis Tournament Platform", version="0.1.0")


@app.middleware("http")
async def request_context(request: Request, call_next):
    """Attach a request id, time the request, and emit a structured log line."""
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    request.state.request_id = request_id
    start = time.monotonic()
    response = await call_next(request)
    duration_ms = round((time.monotonic() - start) * 1000, 1)
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "%s %s -> %s %.1fms req=%s",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
        request_id,
    )
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
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
app.include_router(brackets.router, prefix=API_PREFIX)
app.include_router(ratings.router, prefix=API_PREFIX)
app.include_router(history.router, prefix=API_PREFIX)
app.include_router(registrations.router, prefix=API_PREFIX)
app.include_router(predictions.router, prefix=API_PREFIX)
app.include_router(points.router, prefix=API_PREFIX)


@app.get("/")
def root() -> dict:
    return {"service": "tt-tourney", "docs": "/docs", "health": f"{API_PREFIX}/health"}
