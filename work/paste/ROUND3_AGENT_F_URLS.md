You are a Tier-2 worker on SENTINEL. Execute ONE docs-only task and STOP. No feature code.

# LAW
1. Write ONLY to the write-set below.
2. Do not invent metrics or fake uptime numbers.
3. Do not commit secrets. Demo password already documented is intentional.
4. Paste REAL proof (grep counts) in the report.

# TASK — paste live submission URLs

## Before you start
Human must replace these placeholders with real values, then give you this file:

- FRONTEND_URL = `__PASTE_VERCEL_URL_HERE__`   e.g. https://sentinel-xxx.vercel.app
- BACKEND_URL  = `__PASTE_RENDER_URL_HERE__`   e.g. https://sentinel-api-xxxx.onrender.com

If placeholders still say `__PASTE_...__`, report BLOCKED — do not invent URLs.

## Write-set ONLY
- `README.md` — top table: Live frontend + Live backend + health/OpenAPI rows
- `docs/SUBMISSION.md` — GitHub + Live Deployment fields if present
- `work/reports/wave-10/06-url-polish.report.md`

## Forbid-set
Everything else (no backend, no frontend code, no tests).

## Steps
1. Replace placeholder / "Set after deploy" live URL rows with FRONTEND_URL and BACKEND_URL.
2. Keep demo credentials and local quick-start intact.
3. Ensure both URLs use https://

## Acceptance
```bash
grep -n "vercel\|onrender\|https://" README.md | head -20
grep -c "https://" README.md   # must be ≥ 2
```
Paste outputs.

## Report path
`work/reports/wave-10/06-url-polish.report.md`

Then STOP.
