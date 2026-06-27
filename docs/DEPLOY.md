# Deployment — free tier

## Recommended path: Render + Neon + Vercel

Deploys straight from GitHub with minimal CLI. Config lives in `render.yaml`
(backend) and `frontend/vercel.json` (SPA routing).

**0. Push to GitHub** (Render & Vercel deploy from the repo).

**1. Database — Neon** ([neon.tech](https://neon.tech))
- Create a project; copy the connection string and make it the SQLAlchemy form:
  `postgresql+psycopg://USER:PASSWORD@HOST/dbname?sslmode=require`

**2. Backend — Render** ([render.com](https://render.com))
- New + → **Blueprint** → select your repo (it reads `render.yaml`).
- After it creates `tt-tourney-backend`, set the `sync:false` env vars:
  - `DATABASE_URL` = the Neon string from step 1
  - `FRONTEND_URL` / `CORS_ORIGINS` = your Vercel URL (fill in after step 3, then redeploy)
- Migrations run automatically on deploy (`alembic upgrade head` in the start command).
- Note the service URL, e.g. `https://tt-tourney-backend.onrender.com`.
- Seed an admin from the Render **Shell** tab:
  `python -m app.cli.seed_admin --email you@example.com --password 'StrongPass1'`
  (and optionally `python -m app.cli.seed_players --count 10`).

**3. Frontend — Vercel** ([vercel.com](https://vercel.com))
- New Project → import the repo. Set **Root Directory = `frontend`**
  (build `npm run build`, output `dist` — auto-detected for Vite).
- Add env var `VITE_API_URL = https://tt-tourney-backend.onrender.com/api/v1`.
- Deploy → you get `https://<project>.vercel.app`.

**4. Wire the two together**
- Back in Render, set `FRONTEND_URL` and `CORS_ORIGINS` to the Vercel URL and
  redeploy. Done — open the Vercel URL on your phone and "Add to Home Screen".

> Render's free backend sleeps after ~15 min idle; the first request then takes
> ~30–50s to wake. Fine for personal use.

---

## Alternative: Cloud Run + Neon + Firebase

Target stack (all have free tiers):

- **Postgres** → [Neon](https://neon.tech) (free)
- **Backend (FastAPI)** → Google **Cloud Run** (scales to zero, free tier)
- **Frontend (React PWA)** → **Firebase Hosting** (free)

> Firebase is used here only to **host the frontend**. Auth and email stay in the
> app (custom JWT, verification/reset links logged). Cloud Storage / Firebase email
> can be added later if image uploads or real email are introduced.

---

## 1. Database — Neon

1. Create a project at neon.tech and copy the connection string.
2. Convert it to the SQLAlchemy/psycopg form and require SSL:

   ```
   postgresql+psycopg://USER:PASSWORD@HOST/dbname?sslmode=require
   ```

3. Run migrations against it (from your machine, with the backend venv):

   ```bash
   cd backend
   DATABASE_URL="postgresql+psycopg://...?sslmode=require" alembic upgrade head
   ```

   Re-run this step whenever you add a new migration. (The container does **not**
   migrate on startup, to avoid races on Cloud Run cold starts.)

4. Seed an admin:

   ```bash
   DATABASE_URL="postgresql+psycopg://...?sslmode=require" \
     python -m app.cli.seed_admin --email you@example.com --password 'StrongPass1'
   ```

---

## 2. Backend — Cloud Run

```bash
cd backend
gcloud run deploy tt-backend \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "DATABASE_URL=postgresql+psycopg://...?sslmode=require" \
  --set-env-vars "JWT_SECRET=$(openssl rand -hex 32)" \
  --set-env-vars "FRONTEND_URL=https://YOUR_PROJECT.web.app" \
  --set-env-vars "CORS_ORIGINS=https://YOUR_PROJECT.web.app,https://YOUR_PROJECT.firebaseapp.com" \
  --set-env-vars "RATE_LIMIT_ENABLED=true" \
  --set-env-vars "LOG_VERIFICATION_LINKS=false"
```

- Cloud Run sets `PORT` (8080); the container already honors it.
- Note the service URL it prints (e.g. `https://tt-backend-xxxx-uc.a.run.app`).
- For a personal project, consider `--max-instances 1` to bound cost.

---

## 3. Frontend — Firebase Hosting

```bash
cd frontend
# 1. Point at the deployed backend and build:
echo "VITE_API_URL=https://tt-backend-xxxx-uc.a.run.app/api/v1" > .env.production
npm install
npm run build

# 2. Set your project id in .firebaserc (replace YOUR_FIREBASE_PROJECT_ID), then:
npx firebase-tools login
npx firebase-tools deploy --only hosting
```

The site is served at `https://YOUR_PROJECT.web.app`. `firebase.json` already
rewrites all routes to `index.html` (SPA) and sets cache headers for the service
worker and hashed assets.

---

## 4. Wire-up checklist

- [ ] Backend `CORS_ORIGINS` includes the Firebase Hosting domain(s).
- [ ] Frontend built with `VITE_API_URL` = Cloud Run URL + `/api/v1`.
- [ ] `FRONTEND_URL` on the backend matches the hosting domain (used in the
      verification/reset links printed to logs).
- [ ] Migrations applied to Neon; admin seeded.

## Verifying

```bash
curl https://tt-backend-xxxx-uc.a.run.app/api/v1/health   # {"status":"ok","db":"ok"}
```

Then open the hosting URL on a phone, register, and "Add to Home Screen" to
install the PWA.
