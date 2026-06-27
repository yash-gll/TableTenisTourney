# 🏓 Table Tennis Tournament Platform

A web application for running team-based table tennis tournaments. This repository
implements **Phases 0–7** (the full MVP) of the project plan:

- **0 Foundation**, **1 Auth & approval**, **2 Tournaments & teams**
- **3 Group schedule & scoring** — single round-robin (circle method), match
  lifecycle, server-side score validation, completion/correction, optimistic locking
- **4 Leaderboard** — wins → point-difference → head-to-head / mini-table ranking
  with tie explanations and top-four qualification
- **5 Qualifier bracket** — QF1/QF2/QF3/Final with winner-loser propagation and
  safe downstream reset on corrections
- **6 Ratings** — Elo with stage-based K, placement bonuses, an append-only rating
  ledger, and replay after corrections
- **7 History & finalization** — finalize (placement bonuses + snapshots +
  results record), reopen, and a public tournament history

All business rules (winner determination, ranking, propagation, ratings) are
enforced server-side; the frontend is mobile-first and installable as a PWA.

## Stack

- **Backend:** Python 3.12, FastAPI, SQLAlchemy 2, Alembic, PostgreSQL, Argon2id, JWT
- **Frontend:** React + TypeScript, Vite, Tailwind CSS, TanStack Query, React Hook Form + Zod
- **Infra:** Docker Compose (PostgreSQL + backend + frontend), GitHub Actions CI

It is a **modular monolith** — a single backend service organized into modules
(`api`, `services`, `db`, `schemas`, `core`).

## Project decisions (this build)

This is a personal project, so a few production concerns from the plan are
intentionally simplified:

| Area | Decision |
|------|----------|
| Email delivery | **No email service.** Verification & password-reset links are printed to the **backend logs**. You can also verify a user by setting `email_verified_at` directly in the DB. |
| Profile pictures | **No image upload.** Avatars are rendered client-side from the player's initials. |
| Auth tokens | **Bearer JWT in `localStorage`** (access + refresh via the `Authorization` header). No cookies/CSRF. |
| UI | **Mobile-first, installable PWA** (service worker + manifest). Designed for phone use (~99% of traffic). |
| Match rules (later phase) | Single doubles game to 11, `11-10` allowed (no win-by-two), admin builds all teams. |

> **Firebase note:** Firebase is used only to **host the frontend** (see
> [docs/DEPLOY.md](docs/DEPLOY.md)). Data stays in Postgres and email stays as
> logged links — Firebase Storage / email can be added later if needed.

## Quick start (Docker)

```bash
cp backend/.env.example backend/.env        # optional; compose sets sane defaults
docker compose up --build
```

- Backend API: <http://localhost:8000> (docs at `/docs`)
- Frontend: <http://localhost:5173>
- Postgres: `localhost:5432` (`tt` / `tt`)

Migrations run automatically on backend start (`alembic upgrade head`).

### Create an administrator

```bash
docker compose exec backend python -m app.cli.seed_admin \
  --email admin@example.com --password adminpass1 --display-name "Site Admin"
```

## Local development (without Docker)

### Backend

```bash
cd backend
python3.12 -m venv .venv && source .venv/bin/activate
pip install ".[dev]"
cp .env.example .env                         # point DATABASE_URL at your Postgres
alembic upgrade head
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

## Running tests

The backend test suite defaults to **in-memory SQLite** (no services needed):

```bash
cd backend
pytest            # 18 tests: auth, approval, authorization, health
ruff check app    # lint
mypy app          # type check
```

To run tests against real Postgres (as CI does):

```bash
TEST_DATABASE_URL=postgresql+psycopg://tt:tt@localhost:5432/tt_test pytest
```

The frontend:

```bash
cd frontend
npm run typecheck
npm run build
```

## End-to-end walkthrough

1. Register a player at <http://localhost:5173/register>.
2. The verification link is printed in the backend logs:
   `docker compose logs backend | grep "EMAIL VERIFICATION"`.
   Open it (or set `email_verified_at` in the DB) to verify.
3. Sign in as the admin → **Admin** → see the pending player → **Approve**.
4. Sign in as the player → dashboard shows **Approved** status with an initials avatar.
5. Reject / suspend / restore from the admin screen — each writes an `audit_logs` row.

## Repository layout

```
backend/      FastAPI app, SQLAlchemy models, Alembic migrations, pytest suite
frontend/     Vite + React + TS app
docker-compose.yml
docs/API.md   REST API reference for the implemented endpoints
```

## Production hardening (Phase 8)

- **Rate limiting**: per-IP limits on auth endpoints (`login` 10/min, `register`/
  `forgot`/`reset` 5/min) — returns `429 RATE_LIMITED`. In-memory (per process);
  for multi-instance production swap the store in `app/core/ratelimit.py` for Redis.
- **Request correlation & logs**: every response carries an `X-Request-ID`; each
  request logs `method path -> status duration req=<id>`, and errors echo the id.
- **Security**: Argon2id passwords; tokens stored hashed; bearer JWT; deny-by-default
  authorization; emails never exposed publicly; backend decides winners/ranks.
  Set a strong `JWT_SECRET` (the app warns on the default) and
  `LOG_VERIFICATION_LINKS=false` in production (those links carry raw tokens).
- **Accessibility**: labelled inputs, aria-labelled icon controls, `aria-current`
  nav, large touch targets, `dvh`/safe-area layout.
- **E2E**: Playwright scaffold in `frontend/e2e/`. With both servers running:
  `cd frontend && npm run e2e:install && npm run test:e2e`.

## Backups

- **Production (Neon)**: automatic daily backups + point-in-time restore on the
  free tier — no setup needed.
- **Local / manual**: `pg_dump tt > backup.sql` (restore: `psql tt < backup.sql`).

## Deployment (free tier)

Backend on **Cloud Run**, Postgres on **Neon**, frontend PWA on **Firebase
Hosting** — all free tier. Step-by-step guide: [docs/DEPLOY.md](docs/DEPLOY.md).

## Documentation

- [docs/API.md](docs/API.md) — REST API reference (Phase 0 & 1)
- [docs/DEPLOY.md](docs/DEPLOY.md) — free-tier deployment guide
- The product/engineering specification lives in the project plan and is the source of truth.
