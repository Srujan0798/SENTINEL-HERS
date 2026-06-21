# TASK — wave-6 / 02-incident-comms

## Goal
Per-incident communication channel: realtime messages, @mentions, AI attribution.

## Context
- Wave: 6. Schema: `channels`, `messages` tables. Uses realtime hub for live message delivery.

## Write-set (ONLY these)
- src/backend/comms/
- src/frontend/src/components/comms/

## Forbid-set
- src/backend/tasks/, src/backend/sla/, src/frontend/src/app/dashboard/ (wave-2 owns)

## Blast radius
r1.

## Steps
1. `comms/`: auto-create a `Channel` when incident is created (incident lifecycle hook).
   - `GET /api/incidents/{id}/channel` — get channel info.
   - `POST /api/incidents/{id}/messages` — send message; fan-out via realtime hub (`channel.message` event).
   - `GET /api/incidents/{id}/messages` — paginated history.
   - @mention parsing: extract `@user` → notify that user_id via `mention.created` event.
   - AI messages: `author_type=ai` field on messages for AI-generated content (summaries/postmortems posted here).
2. `<CommsPanel>` (frontend): collapsible right panel on incident detail. Message list + input. Real-time via SSE `channel.message` event. @mention autocomplete from team members.

## Acceptance (PROOF — FM-09)
```
pytest tests/integration/test_comms.py -v
# Expected: channel auto-created with incident, messages stored + delivered via realtime
```

## Report to
`work/reports/wave-6/02-incident-comms.report.md`
