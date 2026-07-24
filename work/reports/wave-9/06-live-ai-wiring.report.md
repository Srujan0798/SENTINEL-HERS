# wave-9 / 06-live-ai-wiring — Report

**Status:** APPROVE-ready. Real Claude + Gemini providers wired via env keys; deterministic mock
fallback intact for tests/offline. Mock fallback is fail-SAFE + fail-LOUD (WARNING logged).

## What changed
- `src/backend/ai/provider.py` — env-driven provider selection; real API calls via `anthropic`
  and `google-generativeai`; typed `AIProviderError`; per-request timeout (`AI_REQUEST_TIMEOUT`,
  default 45s); default Claude model `claude-opus-4-8` (via `AI_MODEL`, `CLAUDE_MODEL` back-compat).
  If the chosen provider's key is absent, `get_provider()` returns `MockProvider` and logs a WARNING.
- `src/backend/ai/__init__.py` — exports the provider interface (`get_provider`, providers,
  `AIProviderError`).
- `.env.example` — documents `AI_PROVIDER`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `AI_MODEL`
  with REDACTED placeholders.
- `tests/integration/test_ai_summary.py` — added `test_claude_without_key_falls_back_to_mock_and_warns`
  (asserts mock path works with no key AND that the fallback logs a warning). No existing coverage removed.

`src/backend/ai/routes.py` was NOT changed: provider selection did not require it, and the existing
503 error-mapping tests must stay green. `AIProviderError` subclasses `RuntimeError`, so the routes'
existing `except Exception` still maps live failures to an error status (no silent mask).

## Acceptance evidence
1. Mock path: `AI_PROVIDER=mock python -m pytest tests/integration/test_ai_summary.py -q` → **13 passed**.
2. Full suite: `python -m pytest -q | tail -2` → **150 passed, 0 failed** (was 149; +1 new test).
3. No hardcoded keys: `grep -rn "sk-ant\|AIza" src/ | grep -v example` → **no hardcoded keys**.
4. Real path (human-run, requires a real key):
   ```
   cd /Users/srujansai/Desktop/SENTINEL-HERS && source .venv/bin/activate && \
   AI_PROVIDER=claude ANTHROPIC_API_KEY=sk-ant-YOURKEY \
   python -c "from src.backend.ai.provider import get_provider; print(get_provider().complete([{'role':'user','content':'Say hello in exactly three words.'}], system='You are a terse test assistant.'))"
   ```
   Code-read confirms the real branch is reached: `get_provider()` with `AI_PROVIDER=claude` and a
   present `ANTHROPIC_API_KEY` instantiates `ClaudeProvider`, which calls
   `anthropic.Anthropic(...).messages.create(...)` and returns `response.content[0].text`.

## Guardrail notes
- FM-11 (fail loud): missing-key fallback logs a WARNING; live API/timeout errors raise typed
  `AIProviderError` rather than being swallowed.
- FM-07: only REDACTED placeholders in `.env.example`; no real keys in git.
- Write-set respected. Nothing touched outside the write-set.
