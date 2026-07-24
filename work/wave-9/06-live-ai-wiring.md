# TASK — wave-9 / 06-live-ai-wiring

> Self-contained brief. The worker needs NOTHING outside this file + the repo.

## Goal (one sentence)
Wire **real** Claude and Gemini providers into the AI layer via env keys, verify incident summary,
RAG chatbot, and auto-postmortem produce genuine LLM output live, while keeping the deterministic mock
fallback intact for tests and offline demos — maximizes the AI Integration axis (20% of the rubric).

## Context (just enough)
- Wave: 9. Decision locked: **real Claude/Gemini keys available.**
- **Depends on: wave-9/01-restore-logs-module** (`ai/routes.py` imports `logs.models`).
- Existing AI abstraction: `src/backend/ai/provider.py` (mock + Claude + Gemini), `src/backend/ai/routes.py`.
- The current default is the mock provider. Keys are provided as env vars — NEVER commit them.
- Latest models (per project AI guidance): default to the newest capable Claude model id
  (`claude-opus-4-8`) unless the user pins another; Gemini via `google-generativeai`.

## Write-set (you may ONLY create/edit these — FM-13)
- `src/backend/ai/provider.py` (provider selection by env; real API calls; robust fallback)
- `src/backend/ai/routes.py` (ONLY if wiring the provider selection requires it)
- `src/backend/ai/__init__.py`
- `.env.example` (document `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `AI_PROVIDER`, `AI_MODEL` — values REDACTED)
- `tests/integration/test_ai_summary.py` — ONLY if a test needs to assert the mock path still works when no key is set (do not delete coverage)

## Forbid-set (do NOT touch)
- Non-AI modules, deploy config, frontend
- Never hardcode a key. Never log a full key. Never send secrets to a worker sandbox.

## Blast radius
r2 (real network calls to paid APIs). Confirm behavior: default to mock when key absent; only call the
real API when a key is present. No unbounded/looping calls.

## Steps
1. Read `ai/provider.py` — understand the current provider interface (summary, rootcause, chat/RAG, postmortem).
2. Implement env-driven selection: `AI_PROVIDER=claude|gemini|mock` (default: `mock` if the chosen provider's key is missing — fail SAFE, not loud-crash, but LOG a clear warning that it fell back).
3. Real Claude path via `anthropic` SDK; real Gemini via `google-generativeai`. Handle timeouts + API errors explicitly (FM-11: surface, don't swallow — return a typed error the route can 502 on, with the mock as an explicit opt-in fallback, not a silent mask).
4. Keep all existing tests green using the mock provider (tests must NOT depend on a network/key).
5. Add `.env.example` entries with clear comments; confirm `.env` is gitignored.

## Acceptance (must produce PROOF — FM-09)
- Command (mock path, no keys — proves tests unaffected): `AI_PROVIDER=mock python -m pytest tests/integration/test_ai_summary.py -q`
- Expected: pass. Paste it.
- Command (real path — run ONLY with a key set in your shell; redact the key): a small script hitting the summary endpoint with `AI_PROVIDER=claude` and a seeded incident, printing the returned summary text. Paste the (non-secret) output showing a real, non-canned summary.
- Command: `grep -rn "sk-\|AIza" src/ | grep -v example || echo "no hardcoded keys"` → must print `no hardcoded keys`. Paste it.

## Guardrails to obey
- FM-07 no secrets in git · FM-11 fail loud on real errors (log the fallback) · FM-08 AI layer only
- Tests must pass with NO network access (mock default).

## Report to
`work/reports/wave-9/06-live-ai-wiring.report.md`
