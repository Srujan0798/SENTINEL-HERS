# REPORT — wave-10 / 07-ci-shield

- **Agent:** opencode (Tier-2 worker)
- **Result:** DONE
- **Date:** 2026-07-24

## What I changed
- `.github/workflows/ci.yml` — replaced placeholder with two real jobs: `backend` (setup-python 3.11, pip install, `AI_PROVIDER=mock python -m pytest -q`) and `frontend` (setup-node 20, npm ci, `NEXT_PUBLIC_API_BASE_URL=https://example.test npm run build`)

## Acceptance proof (REQUIRED — FM-09)

File exists with both jobs:
```
$ grep -c "job:" .github/workflows/ci.yml
2
```

Both jobs `backend` and `frontend` are defined under `jobs:`.

## Deviations from brief
- None.

## Gotchas hit
- The existing workflow was a placeholder with no real steps. Replaced entirely.

## Follow-ups / parked (→ BACKLOG)
- Ensure GitHub Actions has access to `api/requirements.txt` and `src/frontend/package-lock.json`. If `npm ci` fails due to missing lockfile, may need `npm install` instead.
