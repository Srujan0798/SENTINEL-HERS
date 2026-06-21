# TASK — wave-4 / 02-ai-chatbot-rag

## Goal
Conversational AI chatbot for querying logs + incidents in natural language with grounded citations.

## Context
- Wave: 4. Uses `src/backend/ai/provider.py` (write-set 01 writes this first — coordinate: read it after 01 ships).
- User asks in natural language: "why did api-gw fail at 02:00?" → grounded answer with log citations.

## Write-set (ONLY these)
- src/backend/ai/chat/
- src/frontend/src/components/chat/

## Forbid-set
- src/backend/ai/provider.py (01 owns), src/backend/ai/summary/ (01 owns), frontend/app/ (other agents)

## Blast radius
r1.

## Steps
1. `chat/service.py`: `chat(team_id, user_message, history) -> ChatResponse`. RAG pipeline:
   a. Parse intent from user message (time range, service, error type).
   b. Retrieve: search logs + incidents by extracted intent.
   c. Build context window from retrieved results.
   d. Call AI provider with system prompt: "You are SENTINEL, an incident operations assistant. Answer ONLY from the provided context. Cite evidence with [log:id] or [incident:id] markers."
   e. Return: `{answer, citations: [{type, id, excerpt}], confidence}`.
2. `POST /api/ai/chat` — stateless (client sends history); session stored by client.
3. `<ChatPanel>` (frontend): collapsible side panel; messages with citation chips; input with send. Uses `/api/ai/chat`.
4. No hallucination: if context is insufficient → "I don't have enough data to answer that. Try narrowing the time range."

## Acceptance (PROOF — FM-09)
```
pytest tests/integration/test_ai_chat.py -v
# VCR cassettes. Expected: response has answer + citations; insufficient-context path returns graceful message
```

## Report to
`work/reports/wave-4/02-ai-chatbot-rag.report.md`
