=== E0 BASELINE 2026-07-25T15:56:15Z ===
--- healthz ---
{"status":"ok"}
HTTP 200
--- demo-status ---
{"ready":true,"demo_email":"demo@sentinel.io","incident_count":3,"sev1_count":1,"open_sev1_count":1,"resolved_count":1,"frontend":"https://sentinel-hers.vercel.app","login_hint":"demo@sentinel.io / Sentinel2026!"}--- CORS ---
200
--- login ---
token True
role {'id': '8b5a7c56-92f4-4d9a-95f0-f01e00a3cbaa', 'name': 'admin', 'permissions': ['*'], 'description': 'Full system access'}
keys ['access_token', 'refresh_token', 'token_type', 'expires_in', 'user']
--- unauth voice ---
HTTP 401
{"detail":"Not authenticated"}
--- unauth health ---
HTTP 401
{"detail":"Not authenticated"}
200 /api/incidents {"data":[{"id":"97441686-e20e-457d-81c4-d3dcba9f52b0","team_id":"b5849a81-41cf-4162-9fee-970b7a09442
200 /api/alerts [{"id":"0068f280-e169-4bb8-9a84-a03c486a0d41","team_id":"b5849a81-41cf-4162-9fee-970b7a09442c","inci
200 /api/integrations/deployments [{"id":"e1599b22-ab01-45ab-8460-d909887ddf12","service":"auth","environment":"production","version":
200 /api/sla [{"incident_id":"97441686-e20e-457d-81c4-d3dcba9f52b0","title":"Payment service cascade failure","se
200 /api/analytics/incidents/summary {"period_days":7,"total_incidents":3,"open_incidents":2,"resolved_incidents":1,"by_severity":{"SEV1"
SEV_OR_FIRST=97441686-e20e-457d-81c4-d3dcba9f52b0
AI summary 200 On July 25, 2026, at approximately 15:04 UTC, a cascade failure was detected within the payment service, leading to an incident classified as SEV1. This inciden
MOCK False
--- FE ---
login 200
