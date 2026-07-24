You are a Tier-2 worker on SENTINEL (METIS Hard — AI-native engineering ops platform).
Execute ONE self-contained task and STOP. Do not plan other waves. Do not push or deploy.

# LAW
1. Build ONLY what this brief asks. Write ONLY to the write-set. Never touch the forbid-set.
2. Do NOT redesign architecture or expand scope.
3. Fail loud. Prefer `AI_PROVIDER=mock` for tests (deterministic).
4. Run acceptance commands. Paste REAL terminal output in your report. No proof = not done.
5. Write report to the exact path below.
6. If blocked: report BLOCKED with one specific question — do not guess.
7. **SECURITY:** every retrieval MUST filter by authenticated user's `team_id`. Cross-tenant leak = FAIL.
8. Do NOT start until Round-1 tasks (anomaly/containers/voice) are merged if you share the branch —
   your write-set is `src/backend/ai/` (chat only). Avoid editing postmortem modules if present;
   prefer `src/backend/ai/chat/` + routes wiring only.
9. Repo root: SENTINEL-HERS. No secrets in code.

# TASK — wave-10 / 01-conversational-chatbot

## Goal (one sentence)
Ship a working **conversational AI chatbot** that answers natural-language questions over the team's
logs and incidents, with citations, reachable from the dashboard UI.

## Context
- Existing: `src/backend/ai/routes.py`, `src/backend/ai/chat/`, `src/frontend/src/components/chat/ChatPanel.tsx`.
- Retrieval: team-scoped logs + incidents only.

## Write-set (ONLY these paths)
- `src/backend/ai/` — chat/RAG endpoint + retrieval (prefer `ai/chat/` + route registration; minimize conflict with postmortem)
- `src/frontend/src/components/chat/ChatPanel.tsx`
- `tests/integration/test_ai_chat.py` (new — retrieval + team-scoping with mock provider)
- `work/reports/wave-10/01-conversational-chatbot.report.md`

## Forbid-set
- logs/incidents models (read-only consumer), auth/rbac internals, deploy config
- do not rewrite entire AI provider stack; use existing provider abstraction
- do not implement postmortem export (Agent D)

## Blast radius
r1. Team-scope every query.

## Steps
1. Confirm retrieval filters by `team_id` from authed user.
2. Endpoint: `POST /api/ai/chat` → {question} → top-k logs/incidents for that team → LLM answer + citations (IDs).
3. Wire `ChatPanel.tsx`; show cited sources.
4. Tests with mock provider: same-team data only; cross-tenant must not leak.

## Acceptance (PROOF required)
- `AI_PROVIDER=mock python -m pytest tests/integration/test_ai_chat.py -q` → pass. Paste output.
- Cross-tenant test assertion output (team A cannot see team B).
- Sample Q&A with citations (keys redacted).

## Report path
`work/reports/wave-10/01-conversational-chatbot.report.md`

### Report template
```
# REPORT — wave-10 / 01-conversational-chatbot
- **Agent:** <name>
- **Result:** DONE | PARTIAL | BLOCKED
- **Date:** <YYYY-MM-DD>
## What I changed
## Acceptance proof (REQUIRED)
```
$ command
output
```
## Cross-tenant proof
## Sample Q&A
## Deviations / Gotchas / Follow-ups
```

Then STOP.
