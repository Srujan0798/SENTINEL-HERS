You are a Tier-2 worker on SENTINEL (METIS Hard — AI-native engineering ops platform).
Execute ONE self-contained task and STOP. Do not plan other waves. Do not push or deploy.

# LAW
1. Build ONLY what this brief asks. Write ONLY to the write-set. Never touch the forbid-set.
2. Do NOT redesign architecture or expand scope.
3. Fail loud. Prefer `AI_PROVIDER=mock` for tests.
4. Run acceptance commands. Paste REAL terminal output in your report. No proof = not done.
5. Write report to the exact path below.
6. If blocked: report BLOCKED with one specific question — do not guess.
7. **ONLY RUN AFTER Agent A (chat) is merged.** Both touch `src/backend/ai/`. If chat work is not merged, STOP and report BLOCKED.
8. Prefer editing `src/backend/ai/postmortem/` + route wiring; do not break chat endpoints.
9. Postmortem must use REAL incident timeline/logs/alerts — no fictional template text (FM-09).
10. Repo root: SENTINEL-HERS. No secrets.

# TASK — wave-10 / 04-postmortem-export

## Goal (one sentence)
One-click exportable AI postmortem from an incident: timeline + root cause + impact + action items,
downloadable as Markdown (PDF optional).

## Context
- Existing: `src/backend/ai/postmortem/`, incident timeline APIs, incidents UI.

## Write-set (ONLY these paths)
- `src/backend/ai/` — postmortem generate + export (prefer `ai/postmortem/` + routes; do not regress chat)
- `src/frontend/src/app/(dashboard)/incidents/page.tsx` ("Generate postmortem" + download)
- `tests/integration/test_postmortem.py` (new — structure assertions with mock provider)
- `work/reports/wave-10/04-postmortem-export.report.md`

## Forbid-set
- incidents/logs model internals, auth, deploy config
- do not gut chat RAG (Agent A)

## Blast radius
r1. Fail loud if incident missing. If "must be resolved" is product rule, document and enforce clearly.

## Steps
1. `POST /api/ai/postmortem/{incident_id}` (or existing route if present) → assemble timeline+logs+alerts → LLM → sections: summary, timeline, root cause, impact, action items.
2. Export: `?format=md` Markdown attachment; PDF optional (note if skipped).
3. UI: button → generate → preview → download.
4. Mock-provider tests: required sections present and reference real events.

## Acceptance (PROOF required)
- `AI_PROVIDER=mock python -m pytest tests/integration/test_postmortem.py -q` → pass. Paste output.
- Paste generated postmortem (mock) showing all sections grounded in real timeline data.

## Report path
`work/reports/wave-10/04-postmortem-export.report.md`

### Report template
```
# REPORT — wave-10 / 04-postmortem-export
- **Agent:** <name>
- **Result:** DONE | PARTIAL | BLOCKED
- **Date:** <YYYY-MM-DD>
## What I changed
## Acceptance proof (REQUIRED)
```
$ command
output
```
## Sample postmortem (mock)
## Deviations / Gotchas / Follow-ups
```

Then STOP.
