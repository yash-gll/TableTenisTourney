#!/usr/bin/env sh
# Production start: apply migrations, then serve on $PORT (Render/Cloud Run set it).
set -e
echo "Running database migrations…"
alembic upgrade head
echo "Starting server on port ${PORT:-8000}…"
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
