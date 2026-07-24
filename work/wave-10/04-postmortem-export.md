# TASK — wave-10 / 04-postmortem-export

> Self-contained brief. Brownie feature (rubric: AI/Automation 20% + UI/UX 10%).

## Goal (one sentence)
Turn the existing auto-postmortem generation into a one-click, exportable artifact: from a resolved
incident, generate an AI postmortem (timeline + root cause + impact + action items) and let the user
download it as Markdown (and PDF if feasible).

## Context
- Wave: 10. Depends on: wave-9 green (incl. live AI keys).
- Existing: auto-postmortem logic in `src/backend/ai/` (from wave-4/03 report), incident timeline in `src/backend/incidents/`.

## Write-set (FM-13)
- `src/backend/ai/` (postmortem generate + export endpoint)
- `src/frontend/src/app/(dashboard)/incidents/page.tsx` ("Generate postmortem" action + download)
- `tests/integration/test_postmortem.py` (new — structure assertions with mock provider)

## Forbid-set
- incidents/logs models internals, auth, deploy config

## Blast radius
r1 (r2 on real LLM). Postmortem must be generated from REAL incident data (provenance), never templated fiction.

## Steps
1. Endpoint: `POST /api/ai/postmortem/{incident_id}` → assembles timeline+logs+alerts → LLM → structured postmortem (sections: summary, timeline, root cause, impact, action items).
2. Export: `?format=md` returns Markdown attachment; PDF optional (note if skipped + why).
3. UI: button on a resolved incident → generate → preview → download.
4. Test with mock provider: assert all required sections present and reference the incident's real events.

## Acceptance (PROOF — FM-09)
- `python -m pytest tests/integration/test_postmortem.py -q` → pass. Paste it.
- Paste a generated postmortem (mock provider) for the seeded SEV1 showing all sections populated from real timeline data.

## Guardrails
- FM-09 grounded in real incident data · FM-11 fail loud if incident missing/not resolved.

## Report to
`work/reports/wave-10/04-postmortem-export.report.md`
