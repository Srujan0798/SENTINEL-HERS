# TASK — wave-4 / 01-ai-summary-rootcause

## Goal
AI-generated incident summaries + ranked root-cause suggestions. Core AI differentiator (20% of judging).

## Context
- Wave: 4. Depends on wave-2 (incidents) + wave-3 (logs). Provider key in env as `ANTHROPIC_API_KEY` or `GEMINI_API_KEY`.
- Provider abstraction: `src/backend/ai/provider.py` must wrap Claude AND Gemini (switchable via `AI_PROVIDER` env var).

## Write-set (ONLY these)
- src/backend/ai/provider.py
- src/backend/ai/summary/
- src/backend/ai/rootcause/

## Forbid-set
- src/backend/ai/chat/ (gemini owns), src/backend/ai/postmortem/ (kimi owns)

## Blast radius
r1 (AI calls are outbound but not blast-radius r3 since they're API calls not human-visible).

## Steps
1. `provider.py`: `class AIProvider` abstract with `.complete(messages, system)` method. Two impls: `ClaudeProvider` (anthropic SDK) + `GeminiProvider` (google.generativeai). Factory function reads `AI_PROVIDER` env.
2. `summary/service.py`: `generate_incident_summary(incident, logs: list[LogEntry], alerts: list[Alert]) -> str`. Prompt: concise 3-paragraph summary (what happened, impact, current state). Cached in Redis for 5min.
3. `rootcause/service.py`: `suggest_root_causes(incident, logs, deployments) -> list[RootCauseSuggestion]`. Returns top-5 ranked by confidence (0-1). Each has: `hypothesis`, `confidence`, `supporting_evidence: list[str]`, `suggested_action`.
4. `GET /api/ai/incidents/{id}/summary` — returns or generates cached summary.
5. `POST /api/ai/incidents/{id}/root-causes` — triggers analysis, returns ranked list.
6. Fail loud (FM-11): if AI provider fails → 503 with `{"error":"ai_unavailable", "fallback": null}`. Never return fake data.

## Acceptance (PROOF — FM-09)
```
pytest tests/integration/test_ai_summary.py -v
# Uses VCR cassettes (recorded AI responses) so no live API key needed.
# Expected: summary non-empty, root-causes list has 1-5 items each with confidence 0-1
```

## Report to
`work/reports/wave-4/01-ai-summary-rootcause.report.md`
