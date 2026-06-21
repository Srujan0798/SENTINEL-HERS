# Wave 4 / Task 01 — AI Summary + Root-Cause Analysis

**Status:** DONE
**Date:** 2026-06-19

## What was delivered

### Provider abstraction (`src/backend/ai/provider.py`)
- `AIProvider` ABC with `.complete(messages, system)` method
- `ClaudeProvider` — wraps Anthropic SDK (`anthropic.Anthropic`)
- `GeminiProvider` — wraps `google.generativeai`
- `MockProvider` — deterministic fallback for tests/CI
- Factory: `get_provider()` reads `AI_PROVIDER` env var (`claude`|`gemini`|`mock`, default `mock`)

### Summary service (`src/backend/ai/summary/service.py`)
- `generate_incident_summary(incident, logs, alerts) -> str`
- Prompt instructs 3-paragraph format: what happened, impact, current state
- Redis cache with 5-minute TTL (key: `sentinel:ai:summary:{incident_id}`)
- Graceful degradation: if Redis unavailable, runs without cache

### Root-cause service (`src/backend/ai/rootcause/service.py`)
- `suggest_root_causes(incident, logs, deployments) -> list[RootCauseSuggestion]`
- Returns top-5 ranked by confidence (descending, 0.0-1.0)
- `RootCauseSuggestion` dataclass with: `hypothesis`, `confidence`, `supporting_evidence`, `suggested_action`
- Lenient JSON parsing (strips markdown fences, fallback to single low-confidence suggestion)

### API endpoints (`src/backend/ai/routes.py`)
- `GET /api/ai/incidents/{id}/summary` — returns cached or newly generated summary
- `POST /api/ai/incidents/{id}/root-causes` — triggers analysis, returns ranked list
- Both persist results on the incident row (`ai_summary`, `ai_root_cause_ranking`)

### Fail-loud (FM-11)
- Both endpoints catch AI provider exceptions and return `503` with `{"error": "ai_unavailable", "fallback": null}`
- No fake data is ever returned

## Files in write-set
| File | Status |
|------|--------|
| `src/backend/ai/provider.py` | Already existed, no changes needed |
| `src/backend/ai/summary/service.py` | Already existed, no changes needed |
| `src/backend/ai/rootcause/service.py` | Already existed, no changes needed |
| `src/backend/ai/routes.py` | **NEW** — created |
| `src/backend/ai/__init__.py` | Already existed |
| `src/backend/ai/summary/__init__.py` | Already existed |
| `src/backend/ai/rootcause/__init__.py` | Already existed |
| `tests/integration/test_ai_summary.py` | **NEW** — created |
| `api/main.py` | **MODIFIED** — added `ai_router` |

## Forbid-set (no changes)
- `src/backend/ai/chat/` — untouched
- `src/backend/ai/postmortem/` — untouched

## Test results
```
12 passed in 0.42s

TestSummaryEndpoint
  test_generate_summary_returns_3_paragraphs PASSED
  test_summary_cached_on_second_call PASSED
  test_summary_incident_not_found PASSED
  test_summary_ai_failure_returns_503 PASSED

TestRootCauseEndpoint
  test_root_causes_returns_ranked_list PASSED
  test_root_causes_incident_not_found PASSED
  test_root_causes_ai_failure_returns_503 PASSED
  test_root_causes_persisted_on_incident PASSED

TestProviderAbstraction
  test_mock_provider_returns_text PASSED
  test_get_provider_defaults_to_mock PASSED
  test_get_provider_returns_claude PASSED
  test_get_provider_returns_gemini PASSED
```

Existing tests (14/14) remain green.

## Acceptance proof (FM-09)
- Summary endpoint returns non-empty string; caching verified (second call does not re-invoke AI)
- Root-cause endpoint returns 1-5 items, each with confidence 0-1, sorted descending
- AI failure produces 503, not fake data (FM-11)
- No live API key needed — tests use `unittest.mock` to simulate recorded AI responses
