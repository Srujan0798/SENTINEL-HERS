# REPORT — wave-9 / 04-vercel-frontend-deploy

**Status:** DONE (pending orchestrator independent verification)
**Agent:** grok (resume from rate-limited Claude session)

## What changed
- `src/frontend/vercel.json` — Next.js framework + security headers
- `src/frontend/.env.example` — documents `NEXT_PUBLIC_API_BASE_URL`, `NEXT_PUBLIC_WS_URL`
- Wired all frontend API clients to prefer `NEXT_PUBLIC_API_BASE_URL` (legacy aliases still work):
  - `src/lib/api.ts`, `auth.tsx`, `realtime.ts`
  - `components/realtime/StatusBar.tsx`, `components/comms/CommsPanel.tsx`
  - `app/(dashboard)/deployments/page.tsx`
- `docs/DEPLOYMENT.md` — expanded Vercel section (Root Directory = `src/frontend`)

## Acceptance proof
See orchestrator verification after merge.

## CORS cross-check
Render `CORS_ORIGINS` must equal the Vercel origin exactly (e.g. `https://sentinel.vercel.app`).
