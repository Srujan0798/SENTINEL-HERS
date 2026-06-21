# TASK — wave-4 / 03-auto-postmortem

## Goal
Auto-generate structured postmortem reports from resolved incident data. Judges love this for AI 20%.

## Context
- Wave: 4. Reads resolved incidents + timeline events + root causes (from 01). Uses `src/backend/ai/provider.py`.

## Write-set (ONLY these)
- src/backend/ai/postmortem/
- docs/operational/postmortem-template.md

## Forbid-set
- src/backend/ai/provider.py (01 owns), src/backend/ai/chat/ (02 owns)

## Blast radius
r1.

## Steps
1. `postmortem/service.py`: `generate_postmortem(incident_id) -> PostmortemReport`.
   Collects: incident metadata + full timeline events + root causes + assigned tasks + resolution.
   Prompt: generate structured postmortem with sections:
   - Executive summary (2 sentences)
   - Timeline (chronological with event sources)
   - Root cause analysis (top causes with evidence)
   - Impact assessment (services affected, duration, users impacted)
   - Resolution steps taken
   - Action items to prevent recurrence (5 specific items)
2. `POST /api/ai/incidents/{id}/postmortem` — generates + stores postmortem.
3. `GET /api/ai/incidents/{id}/postmortem` — fetch existing.
4. Store postmortem as Markdown in `messages` table with `author_type=ai`.
5. Document the postmortem template at `docs/operational/postmortem-template.md`.

## Acceptance (PROOF — FM-09)
```
pytest tests/integration/test_ai_postmortem.py -v
# VCR cassettes. Expected: postmortem has all 6 sections, non-empty, stored in DB
```

## Report to
`work/reports/wave-4/03-auto-postmortem.report.md`
