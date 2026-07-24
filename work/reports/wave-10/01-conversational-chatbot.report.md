# REPORT — wave-10 / 01-conversational-chatbot

- **Agent:** opencode (Tier-2 worker)
- **Result:** DONE
- **Date:** 2026-07-24

## What I changed
- `src/backend/ai/routes.py` — added `POST /api/ai/chat` endpoint with team-scoped RAG retrieval over incidents and logs; filters by `team_id` from the authenticated user; supports optional `incident_id` scoping
- `src/frontend/src/components/chat/ChatPanel.tsx` — already existed and wired to `/api/ai/chat`; no changes needed
- `tests/integration/test_ai_chat.py` — 6 tests: basic chat with answer+citations, incident-scoped chat, no-data fallback, auth required, cross-tenant no data leak, cross-tenant incident ID rejected

## Acceptance proof (REQUIRED — FM-09)

**Test suite (6/6 passing):**
```
$ python3 -m pytest tests/integration/test_ai_chat.py -v
...
test_ai_chat.py::TestChatEndpoint::test_chat_returns_answer_with_citations PASSED
test_ai_chat.py::TestChatEndpoint::test_chat_with_incident_id PASSED
test_ai_chat.py::TestChatEndpoint::test_chat_no_data_returns_fallback PASSED
test_ai_chat.py::TestChatEndpoint::test_chat_requires_auth PASSED
test_ai_chat.py::TestCrossTenantIsolation::test_cross_tenant_no_data_leak PASSED
test_ai_chat.py::TestCrossTenantIsolation::test_cross_tenant_incident_id_rejected PASSED
================== 6 passed in 10.12s ====================
```

**Sample Q&A (mock):**
```
POST /api/ai/chat {"question": "What incidents do we have?"}
→ {"answer": "[mock-ai] Response to: ...", "citations": [...], "confidence": 0.8}
```

**Cross-tenant proof** — Team B querying returns none of Team A's data (asserted in tests).

## Deviations from brief
- None. ChatPanel.tsx was already wired; no UI changes needed.

## Gotchas hit
- Existing `_fetch_logs()` utility filters by `incident_id`, not `team_id`. Added separate team-scoped query for non-incident-specific chat.
- Mock provider returns `[mock-ai] Response to: ...` for all inputs, which doesn't contain real citations. Tests validate structure, not content semantics.

## Follow-ups / parked (→ BACKLOG)
- None.
