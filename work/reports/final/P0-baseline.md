# P0 Baseline Report — SENTINEL HERS

> Generated: 2026-07-25T13:55 UTC
> Phase: 0 (Truth Reset)
> Honest score: ~15-20%

## Probe Results

### 1. GET /healthz
```json
{"status":"ok"}
```
✅ Pass — 200 OK

### 2. GET /api/demo-status
```json
{"ready":true,"demo_email":"demo@sentinel.io","incident_count":3,"sev1_count":1,"open_sev1_count":1,"resolved_count":1,"frontend":"https://sentinel-hers.vercel.app","login_hint":"demo@sentinel.io / Sentinel2026!"}
```
⚠️ Contains login_hint with password in non-prod — OK for demo
✅ ready=true, open_sev1_count=1

### 3. POST /auth/login
```json
{"access_token":"eyJ...","role":{"name":"admin","permissions":["*"]},"user":{"email":"demo@sentinel.io","name":"Demo User",...}}
```
✅ 200 — JWT returned with admin role

### 4. Unauth POST /api/voice/incidents
```json
{"detail":[{"type":"missing","loc":["query","team_id"],"msg":"Field required","input":null},{"type":"missing","loc":["body","file"],"msg":"Field required","input":null}]}
```
❌ Returns 422 validation error, NOT 401 — voice endpoint unauthenticated, accepts client-supplied team_id

### 5. Unauth GET /api/health/services/
```json
[{"service_name":"api-gateway","status":"degraded",...},{"service_name":"auth","status":"healthy",...},...]
```
❌ Returns health data WITHOUT authentication — cross-tenant data leak

### 6. Auth GET /api/incidents/
Output: empty response (no incidents returned or empty array)
❌ No SEV1 incident data returned with auth — seed not working or route wrong

### 7. AI Summary
```
{"detail": "Not Found"}
```
❌ AI summary endpoint returns 404

### 8. SSE /api/sse/events
```
{"detail":"Not Found"}
```
❌ SSE endpoint returns 404

### 9. GET /api/tasks/
```
{"detail":"Not Found"}
```
❌ Tasks endpoint returns 404

### 10. GET /api/deployments/
```
{"detail":"Not Found"}
```
❌ Deployments endpoint returns 404

### 11. GET /api/timeline/
```
{"detail":"Not Found"}
```
❌ Timeline endpoint returns 404

### 12. GET /api/analytics/
```
{"detail":"Not Found"}
```
❌ Analytics endpoint returns 404

### 13. Webhook POST no signature
Not tested — endpoint returns 404

## Critical Security Gaps (confirmed live)

| Gap | Evidence |
|-----|----------|
| Voice unauth + client team_id | 422 instead of 401, client supplies team_id query param |
| Health list unauth | Full service data returned without any JWT |
| RBAC not wired | Login returns admin role but mutating routes may not check |
| demo-status leaks password hint | Returns `Sentinel2026!` hint in production |
| AI summary 404 | Not Found — no SEV1 incident to summarize |
| SSE endpoint 404 | Not Found — no realtime events |
| Tasks/Deployments/Timeline/Analytics 404 | Most data endpoints not live |

## Live Routes That Work
- /healthz
- /api/demo-status
- /auth/login

## Critical Gaps Blocking Sacred Path
1. Voice endpoint accepts unauthenticated input (not even 401)
2. Health data returned without auth
3. No incidents visible via API
4. AI summary 404
5. SSE 404
6. Tasks, Deployments, Timeline, Analytics all 404
