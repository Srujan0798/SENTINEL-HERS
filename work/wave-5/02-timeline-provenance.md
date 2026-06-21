# TASK — wave-5 / 02-timeline-provenance

## Goal
Incident timeline with full event provenance — every event carries source, actor, ts, payload_ref. Immutable.

## Context
- Wave: 5. Schema: `timeline_events` table with `source, actor, ts` provenance columns (already in migration).
- Reads incidents + deployments + commits + log alerts to build rich timeline.

## Write-set (ONLY these)
- src/backend/timeline/
- src/frontend/src/components/timeline/

## Forbid-set
- src/backend/integrations/ (01 owns), src/backend/incidents/ (wave-2 owns)

## Blast radius
r1.

## Steps
1. SQLAlchemy model for `TimelineEvent` (already in schema — just the ORM model here).
2. `timeline/service.py`: `add_event(incident_id, event_type, source, actor_id, payload)` — append-only, never mutate.
3. `GET /api/incidents/{id}/timeline` — returns chronological events with full provenance.
4. Integration hooks: incidents module calls `add_event` on every state change; VCS integration calls on deploy/commit link.
5. `<IncidentTimeline>` (frontend) — vertical timeline, each event shows: type icon, actor avatar, source badge, timestamp, expandable payload. 
6. Provenance sources: `incident_update | log_alert | deployment | commit | ai_analysis | manual`.

## Acceptance (PROOF — FM-09)
```
pytest tests/integration/test_timeline.py -v
# Expected: events append-only (update rejected), provenance fields non-null, ordering correct
```

## Report to
`work/reports/wave-5/02-timeline-provenance.report.md`
