# TASK — wave-2 / 03-dashboard-ui

## Goal
Live incident dashboard UI — severity colour-coded board with triage drag, powered by the SSE realtime stream.

## Context
- Wave: 2. Uses design system from `src/frontend/src/components/ui/` (badge, card, table, button).
- Auth hook from `src/frontend/lib/auth.ts`; realtime hook from `src/frontend/lib/realtime.ts`.

## Write-set (ONLY these)
- src/frontend/src/app/dashboard/
- src/frontend/src/components/incident/

## Forbid-set
- src/frontend/src/components/ui/ (design system frozen), lib/auth.ts, lib/realtime.ts

## Blast radius
r1.

## Steps
1. `/dashboard` page: incident board with columns per triage state (detected/triaging/investigating/mitigating/resolved).
2. `<IncidentCard>` shows: title, SEV badge (SEV1=red SEV2=orange SEV3=amber SEV4=blue), status, assignee, age.
3. `<IncidentList>` sortable by severity + last updated; filterable by status.
4. Live updates: `useRealtimeStream` → on `incident.updated` / `incident.created` → optimistic update to list.
5. Click-through to incident detail page `/dashboard/[id]` (stub OK for now — full detail in wave-6).
6. Responsive, dark theme, ops-console aesthetic (no light mode needed).

## Acceptance (PROOF — FM-09)
```
cd src/frontend && npm run build
# Expected: build succeeds with zero type errors; dashboard page exists in output
```

## Report to
`work/reports/wave-2/03-dashboard-ui.report.md`
