# TASK — wave-9 / 04-vercel-frontend-deploy

> Self-contained brief. The worker needs NOTHING outside this file + the repo.

## Goal (one sentence)
Deploy the Next.js 15 frontend to **Vercel** wired to the live Render backend URL, so the full demo
path (login → dashboard → incident → AI summary → assign → timeline → analytics) works end-to-end in
production — the second half of the MANDATORY live deployment.

## Context (just enough)
- Wave: 9. Decision locked: **Vercel (frontend)**.
- **Depends on: wave-9/03-render-backend-deploy** (needs the backend HTTPS URL + CORS origin).
- Frontend lives in `src/frontend/` (Next.js 15 + React 19). API client: `src/frontend/src/lib/api.ts`;
  realtime: `src/frontend/src/lib/realtime.ts`; auth: `src/frontend/src/lib/auth.tsx`.
- Vercel builds from a subdirectory — set **Root Directory = `src/frontend`** in project settings.

## Write-set (you may ONLY create/edit these — FM-13)
- `src/frontend/vercel.json` (new — build config, headers if needed)
- `src/frontend/.env.example` (new/edit — document `NEXT_PUBLIC_API_BASE_URL`, `NEXT_PUBLIC_WS_URL`)
- `src/frontend/src/lib/api.ts` + `src/frontend/src/lib/realtime.ts` — ONLY to read the API base from
  `process.env.NEXT_PUBLIC_*` instead of any hardcoded `localhost` (surgical config change only)
- `src/frontend/next.config.ts` — ONLY if rewrites/headers needed for the API/CORS
- `docs/DEPLOYMENT.md` — append the Vercel section (coordinate; backend author owns the file top)

## Forbid-set (do NOT touch)
- Backend, tests, `render.yaml`
- Any component logic beyond swapping hardcoded URLs for env vars

## Blast radius
r3 (external deploy config; the live `vercel deploy` is the human's action). Config = auto.

## Steps
1. Grep the frontend for hardcoded `http://localhost` / `:8000` / `127.0.0.1` and route them through `NEXT_PUBLIC_API_BASE_URL` / `NEXT_PUBLIC_WS_URL`.
2. Write `vercel.json` (framework: nextjs; ensure SSR works; add security headers).
3. Document required Vercel env vars in `src/frontend/.env.example` and the DEPLOYMENT.md Vercel section (incl. Root Directory = `src/frontend`).
4. Confirm the CORS origin you'll use matches what wave-9/03 sets as `CORS_ORIGINS` on Render — note the exact value in your report so the orchestrator can cross-check.
5. Verify a production build succeeds locally against a dummy API base.

## Acceptance (must produce PROOF — FM-09)
- Command: `cd src/frontend && npm ci && NEXT_PUBLIC_API_BASE_URL=https://example.test npm run build`
- Expected: build completes with exit 0 (`✓ Compiled successfully`). Paste the tail of the build output.
- Command: `grep -rn "localhost:8000\|127.0.0.1:8000" src/frontend/src || echo "no hardcoded backend URLs"`
- Expected: prints `no hardcoded backend URLs`. Paste it.

## Guardrails to obey
- FM-07 no secrets (public env only; anything secret stays server-side) · FM-08 no redesign
- The demo path is SACRED — do not refactor components, only wire config.

## Report to
`work/reports/wave-9/04-vercel-frontend-deploy.report.md`
