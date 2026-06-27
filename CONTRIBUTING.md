# Contributing

Welcome! This guide gets you from clone → running locally → shipping a change.

## TL;DR

- **You develop against your own local Postgres**, never the production (Neon) DB.
- Change the schema by editing models + adding an **Alembic migration**, committed
  with your code. Migrations run automatically on deploy.
- Work on a **branch → PR → merge to `main`**. Merging to `main` auto-deploys to
  production (Render + Vercel), so don't push straight to `main`.

## Prerequisites

- Python **3.12** (`brew install python@3.12`)
- Node **20+** (`brew install node`)
- PostgreSQL **16** (`brew install postgresql@16 && brew services start postgresql@16`)

## Local setup

```bash
git clone https://github.com/yash-gll/TableTenisTourney.git
cd TableTenisTourney

# --- backend ---
cd backend
python3.12 -m venv .venv && source .venv/bin/activate
pip install ".[dev]"
createdb tt                                  # your own local database
cp .env.example .env
# edit .env: DATABASE_URL=postgresql+psycopg://<your-mac-user>@localhost:5432/tt
alembic upgrade head                         # build the schema
python -m app.cli.seed_admin --email admin@example.com --password 'AdminPass1'
python -m app.cli.seed_players --count 10    # optional test players
uvicorn app.main:app --reload                # http://localhost:8000/docs

# --- frontend (second terminal) ---
cd frontend
npm install
cp .env.example .env                         # VITE_API_URL=http://localhost:8000/api/v1
npm run dev                                  # http://localhost:5173
```

## Before you push

```bash
# backend
cd backend && ruff check app && mypy app && pytest      # all must pass
# frontend
cd frontend && npm run typecheck && npm run build
```

## Changing the database schema (migrations)

We use Alembic; **every schema change needs a migration committed with the code.**

1. Edit the model(s) in `backend/app/db/models/`.
2. Create a migration file in `backend/migrations/versions/`. Two options:
   - **Hand-write** it (recommended for consistency) — copy the newest file in
     `versions/`, bump `revision`/`down_revision`, and write `upgrade()`/
     `downgrade()` using the Postgres types the others use
     (`postgresql.UUID`, `JSONB`, `ENUM`).
   - Or **autogenerate** a draft, then review/trim it:
     `alembic revision --autogenerate -m "add X"` (note: because models use
     portable column types, autogenerate can emit spurious type changes — review
     before committing).
3. Apply it locally and make sure it round-trips:
   ```bash
   alembic upgrade head
   alembic downgrade -1 && alembic upgrade head   # sanity-check downgrade
   ```
4. Add a test if behavior changed, run the full gate, and commit the model + the
   migration together.

On deploy, Render runs `alembic upgrade head` (via `backend/start.sh`) against
Neon, so your migration is applied to production automatically. **Never edit the
production schema by hand** — always through a migration.

## Branching & deploys

- Branch off `main`, open a PR, get it reviewed, then merge.
- `main` is the production branch: a merge triggers Render (backend) and Vercel
  (frontend) to redeploy. Keep `main` green.
- Migrations are forward-only in practice; coordinate before changing or removing
  an existing migration.

## Database access

- **Local dev:** your own Postgres; your `.env` is gitignored — never commit it.
- **Production (Neon):** the connection string lives only in Render's env vars.
  If someone needs to inspect prod, invite them to the **Neon project** (Neon
  dashboard → Settings → collaborators) rather than sharing the raw string.
- Secrets (`JWT_SECRET`, `DATABASE_URL`) live in Render/Vercel env settings, never
  in the repo.

## Project layout

```
backend/   FastAPI + SQLAlchemy + Alembic (app/, migrations/, tests/)
frontend/  Vite + React + TS (src/, e2e/)
docs/      API.md, DEPLOY.md
```
See `README.md` for the feature overview and `docs/API.md` for endpoints.
