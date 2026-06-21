# TASK — wave-3 / 03-monitoring-ui

## Goal
Monitoring UI: live log stream viewer + service uptime sparklines. Judges see this for Real-Time criterion.

## Context
- Wave: 3. Uses design system components; realtime hook from `src/frontend/lib/realtime.ts`.

## Write-set (ONLY these)
- src/frontend/src/app/monitoring/
- src/frontend/src/components/health/

## Forbid-set
- src/frontend/src/components/ui/ (frozen), src/frontend/src/app/dashboard/ (wave-2 owns)

## Blast radius
r1.

## Steps
1. `/monitoring` page with two panels: Log Stream + Service Health grid.
2. `<LogStream>` — virtual-scroll log viewer, live via SSE `log.ingested` events; colour-coded by level (error=red, warn=amber, info=blue, debug=grey); filter by service + level.
3. `<ServiceHealthGrid>` — one card per service: status dot (green/amber/red), uptime %, latency sparkline (last 24h), last-check timestamp.
4. `<AlertBanner>` — sticky top bar showing count of open SEV1+SEV2 alerts; click drills to incident dashboard.
5. Realtime: `service.health_changed` → instant card update; `alert.created` → banner counter increments.

## Acceptance (PROOF — FM-09)
```
cd src/frontend && npm run build
# Expected: build succeeds; /monitoring page in output
```

## Report to
`work/reports/wave-3/03-monitoring-ui.report.md`
