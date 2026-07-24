# TASK — wave-10 / 01-conversational-chatbot

> Self-contained brief. Brownie feature (rubric: AI Integration 20%). Harden + surface + prove.

## Goal (one sentence)
Ship a working **conversational AI chatbot** that answers natural-language questions over the team's
logs and incidents ("what caused the SEV1 last night?", "show errors from the payments service"),
backed by the existing RAG plumbing and reachable from the dashboard UI.

## Context
- Wave: 10 — Brownie & Rubric-Max. Depends on: wave-9 green (logs module + tests + live AI keys).
- Existing: `src/backend/ai/routes.py` (RAG bits), `src/frontend/src/components/chat/ChatPanel.tsx`.
- Retrieval source of truth: `logs.models.LogEntryModel` + `incidents.models` (team-scoped — RBAC!).

## Write-set (FM-13)
- `src/backend/ai/` (chat/RAG endpoint + retrieval over logs/incidents)
- `src/frontend/src/components/chat/ChatPanel.tsx` (wire to endpoint, streaming if available)
- `tests/integration/test_ai_chat.py` (new — retrieval + team-scoping test with mock provider)

## Forbid-set
- logs/incidents models (read-only consumer), auth/rbac internals, deploy config

## Blast radius
r1 (r2 only when hitting real LLM). Team-scope every query — a user must NEVER retrieve another team's logs (Security 15%).

## Steps
1. Confirm retrieval filters by `team_id` from the authed user (RBAC).
2. Endpoint: `POST /api/ai/chat` → {question} → retrieve top-k logs/incidents for that team → LLM answer with citations (which log/incident IDs).
3. Wire `ChatPanel.tsx` to it; show cited sources (provenance = judge candy).
4. Test with the mock provider: assert answer references only same-team data.

## Acceptance (PROOF — FM-09)
- `python -m pytest tests/integration/test_ai_chat.py -q` → pass. Paste it.
- Cross-tenant test: a user from team A asks about team B's incident → answer must NOT leak team B data. Paste the assertion output.
- Paste a real (redacted-key) sample Q&A with citations.

## Guardrails
- FM-07 no secrets · FM-11 fail loud · Security: strict team-scoping, no cross-tenant leak.

## Report to
`work/reports/wave-10/01-conversational-chatbot.report.md`
