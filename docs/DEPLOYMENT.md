# SENTINEL — Deployment Guide

Production topology (decision locked):

- **Backend** → Render (FastAPI, Docker) + managed **PostgreSQL** + managed **Redis (Key Value)**
- **Frontend** → Vercel (Next.js)

The backend is deployed as a **Render Blueprint** from [`render.yaml`](../render.yaml).
No secret is ever stored in git — all keys are set in the Render dashboard (FM-07).

---

## 1. Backend on Render — click-path

### Prerequisites
- Repo pushed to GitHub/GitLab (Render deploys from the connected repo).
- An Anthropic API key (required for the AI demo path). A Gemini key is optional.

### Steps
1. **Render Dashboard → New → Blueprint.**
2. Connect this repository. Render detects [`render.yaml`](../render.yaml) at the repo root.
3. Review the plan. It provisions three resources:
   - `sentinel-postgres` — managed PostgreSQL 16
   - `sentinel-redis` — managed Key Value (Redis)
   - `sentinel-api` — web service built from `Dockerfile.api`
4. Click **Apply**. Render creates the DB + Key Value first, then builds the image.
5. **Set the dashboard-only secrets** (`sync: false` vars — see table below):
   `sentinel-api` → **Environment** → add `ANTHROPIC_API_KEY` (and optionally `GEMINI_API_KEY`),
   plus `CORS_ORIGINS` (temporarily `*` until the frontend URL is known — see step 8).
6. **Deploy.** On each deploy Render runs the **pre-deploy** step
   (`./deployment/render/release.sh`): it applies DB migrations, then seeds the demo
   dataset **once** (idempotent — a redeploy will NOT duplicate the SEV1 incident).
7. When the service is **live**, verify:
   - `https://sentinel-api.onrender.com/healthz` → `{"status":"ok"}`
   - `https://sentinel-api.onrender.com/metrics` → Prometheus text
   - `https://sentinel-api.onrender.com/api/docs` → OpenAPI UI
   (Your exact hostname is shown in the Render dashboard.)
8. **After the frontend is deployed (section 2)**, come back and set
   `CORS_ORIGINS` to the real Vercel URL (e.g. `https://sentinel.vercel.app`) and redeploy.

### Demo login (seeded)
- URL: your Vercel frontend, pointed at the Render API
- Email: `demo@sentinel.io`
- Password: `Sentinel2026!`

---

## 2. Frontend on Vercel — click-path

1. **Vercel → Add New → Project**, import the same repo, root = the Next.js app.
2. Set env var `NEXT_PUBLIC_API_URL = https://sentinel-api.onrender.com` (your Render URL).
3. Deploy. Note the resulting URL (e.g. `https://sentinel.vercel.app`).
4. Go back to Render → `sentinel-api` → set `CORS_ORIGINS` to that URL → redeploy.

---

## 3. Environment variables

| Variable | Where set | Source / value | Secret? |
|---|---|---|---|
| `PORT` | render.yaml | `8000` (Render injects the real port; app binds `0.0.0.0:$PORT`) | no |
| `DATABASE_URL` | render.yaml | `fromDatabase: sentinel-postgres` (injected) | managed |
| `REDIS_URL` | render.yaml | `fromService: sentinel-redis` (injected) | managed |
| `JWT_SECRET` | render.yaml | `generateValue: true` (Render-generated) | **generated** |
| `JWT_REFRESH_SECRET` | render.yaml | `generateValue: true` (Render-generated) | **generated** |
| `AI_PROVIDER` | render.yaml | `claude` | no |
| `ANTHROPIC_API_KEY` | **dashboard** | `sync: false` — set by hand | **secret** |
| `GEMINI_API_KEY` | **dashboard** | `sync: false` — set by hand (optional) | **secret** |
| `GITHUB_WEBHOOK_SECRET` | **dashboard** | `sync: false` — optional | **secret** |
| `GITLAB_WEBHOOK_SECRET` | **dashboard** | `sync: false` — optional | **secret** |
| `CORS_ORIGINS` | **dashboard** | `sync: false` — set to the Vercel URL after frontend deploy | no |
| `NEXT_PUBLIC_API_URL` | Vercel | the Render API URL | no |

**No API key or secret is hardcoded anywhere.** Every secret is either
Render-generated (`generateValue`) or dashboard-only (`sync: false`).

---

## 4. Release / seed behaviour

`preDeployCommand: ./deployment/render/release.sh` runs before each promotion:

1. Applies DB migrations (`api.startup.run_migrations` — `create_all`, idempotent).
2. Boots a short-lived local uvicorn against the same managed Postgres.
3. **Idempotency guard:** logs in as the demo user and checks for existing incidents.
   If found, seeding is **skipped** — redeploys never duplicate the SEV1 incident.
   Otherwise it runs `python scripts/seed_demo.py`.

Migration failure aborts the release (fail loud, FM-11). A seed failure is logged
loudly but is non-fatal (demo data is best-effort on top of a healthy app).

---

## 5. Rollback

**Roll back a bad deploy (Render):**
1. `sentinel-api` → **Events** (or **Deploys**) tab.
2. Find the last known-good deploy → **⋯ → Rollback / Redeploy**.
3. Render redeploys that image. The pre-deploy seed guard makes this safe —
   existing demo data is detected and not re-seeded.

**Roll back a config/secret change:** edit the env var back in the dashboard and
trigger **Manual Deploy → Deploy latest commit**.

**Roll back the database:** managed PostgreSQL supports point-in-time restore from
the `sentinel-postgres` → **Recovery** tab (paid plans). On the free plan, treat the
seed as the recovery baseline — it re-establishes the demo dataset on a fresh DB.

**Frontend (Vercel):** Deployments → pick a previous deployment → **Promote to Production**.

---

## 6. Known follow-ups (outside this task's write-set)

- `scripts/seed_demo.py` is not itself idempotent for incidents; the guard lives in
  `release.sh`. Recommended: add an "existing demo team" guard inside the script.
- `scripts/seed_demo.py` imports `requests`, which is not in `api/requirements.txt`.
  `release.sh` installs it at release time; add `requests` to requirements to remove that.
- `api/main.py` currently hardcodes CORS `allow_origins` to localhost. It must be
  updated to read the `CORS_ORIGINS` env var for the Vercel origin to be accepted.
