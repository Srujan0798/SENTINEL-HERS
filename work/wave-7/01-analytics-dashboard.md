# TASK — wave-7 / 01-analytics-dashboard

## Goal
Analytics dashboard: deployment stability trends + incident frequency charts. Judges see this for System Design 25%.

## Context
- Wave: 7. Reads from all prior tables. Metrics MUST come from ONE source — Prometheus or DB aggregates, never hand-typed (FM-05).

## Write-set (ONLY these)
- src/backend/analytics/
- src/frontend/src/app/analytics/

## Forbid-set
- src/backend/ml/ (02 owns), src/backend/integrations/k8s/ (03 owns), other frontend pages

## Blast radius
r1.

## Steps
1. `analytics/`: 
   - `GET /api/analytics/incidents` — frequency by day/week/month; breakdown by severity + service.
   - `GET /api/analytics/deployments` — stability score (deployments with incidents / total deploys); MTTR per service.
   - `GET /api/analytics/sla` — SLA compliance rate (% resolved within SLO) per SEV level.
   - `GET /api/analytics/services` — health score per service over time.
   - All from DB aggregates (no hand-typed numbers — FM-05).
2. Frontend `/analytics` page:
   - Line chart: incident frequency over time (Recharts or similar).
   - Bar chart: deployment stability per service (green = no incident, red = incident).
   - KPI cards: MTTR, SLA compliance %, incident count this week vs last week.
   - Date range picker: last 7d / 30d / 90d.

## Acceptance (PROOF — FM-09)
```
cd src/frontend && npm run build
pytest tests/integration/test_analytics.py -v
# Expected: build succeeds; API returns well-structured time-series data
```

## Report to
`work/reports/wave-7/01-analytics-dashboard.report.md`
