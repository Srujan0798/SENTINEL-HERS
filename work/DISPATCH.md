# DISPATCH — Wave 9 & 10 (Final Submission Push)

> Orchestrator (Tier-1) owns this file. You paste each task file into the assigned Tier-2 worker,
> prepended with the WORKER PROMPT below. Worker writes code + a report; orchestrator re-runs
> acceptance independently and merges. **Disjoint write-sets only (FM-13).**

## The worker prompt (prepend to EVERY task file you paste)

```
You are a Tier-2 worker on the SENTINEL build. Execute ONE self-contained task and stop.
1. Read the task file. Build ONLY what it asks. Write ONLY to its write-set. Never touch the forbid-set.
2. Use your own skills/tools. Do NOT redesign or expand scope (FM-08).
3. Fail loud (FM-11): no `except: pass`, no silent fallback, no synthetic data to fake a pass.
4. Run the acceptance command. Paste its REAL output into your report (FM-09). No proof = not done.
5. Write your report to work/reports/<wave>/<task-id>.report.md using REPORT_TEMPLATE.md.
6. If blocked or ambiguous, report BLOCKED with the specific question — do not guess.
Then STOP. The orchestrator reviews, re-runs acceptance, and merges.
[TASK FILE FOLLOWS]
```

## Wave-9 — Submission Hardening (MANDATORY bar)

| # | Task file | Agent | Write-set (disjoint) | Depends on |
|---|---|---|---|---|
| 9.1 | `work/wave-9/01-restore-logs-module.md` | **gpt** | `src/backend/logs/` | — (BLOCKER, dispatch FIRST) |
| 9.2 | `work/wave-9/02-green-test-suite.md` | **kimi** | `tests/`, `api/requirements.txt`, surgical `src/` | 9.1 |
| 9.3 | `work/wave-9/03-render-backend-deploy.md` | **z.ai** | `render.yaml`, `Dockerfile.api`, `deployment/render/`, `docs/DEPLOYMENT.md` | 9.1 |
| 9.4 | `work/wave-9/04-vercel-frontend-deploy.md` | **qwen** | `src/frontend/vercel.json`, `src/frontend/.env.example`, frontend URL config | 9.3 |
| 9.5 | `work/wave-9/05-writeup-and-docs.md` | **perplexity** | `WRITEUP.md`, `README.md`, `docs/PRODUCTION_WALKTHROUGH.md` | 9.3, 9.4 |
| 9.6 | `work/wave-9/06-live-ai-wiring.md` | **claude** (or gemini) | `src/backend/ai/`, `.env.example` | 9.1 |

**Order:** `9.1 → 9.2` (verify green) → `9.3 → 9.4 → 9.5`; run `9.6` in parallel any time after 9.1.

## Wave-10 — Brownie & Rubric-Max (only after suite is GREEN)

| # | Task file | Agent | Write-set (disjoint) | Depends on |
|---|---|---|---|---|
| 10.1 | `work/wave-10/01-conversational-chatbot.md` | **gemini** | `src/backend/ai/` (chat), `frontend/components/chat/`, `test_ai_chat.py` | 9.2, 9.6 |
| 10.2 | `work/wave-10/02-predictive-anomaly.md` | **deep** | `src/backend/ml/`, `analytics/routes.py`, analytics UI, `test_anomaly.py` | 9.2 |
| 10.3 | `work/wave-10/03-container-monitoring.md` | **grok** | `src/backend/integrations/{docker,k8s,containers}/`, monitoring UI, `test_containers.py` | 9.2 |
| 10.4 | `work/wave-10/04-postmortem-export.md` | **kimi** | `src/backend/ai/` (postmortem), incidents UI, `test_postmortem.py` | 9.2, 9.6 |
| 10.5 | `work/wave-10/05-voice-to-ticket-e2e.md` | **mimo** | `src/backend/voice/`, `frontend/components/voice/`, `test_voice.py` | 9.2 |

> ⚠️ Write-set collision watch: 10.1, 10.4, and 9.6 all touch `src/backend/ai/`. Run **9.6 first and
> merge it**, then run 10.1 and 10.4 **sequentially** (not simultaneously) OR split `ai/` into
> subpackages (`ai/chat/`, `ai/postmortem/`) so their write-sets are disjoint. Orchestrator enforces this.

## Orchestrator merge loop (per returned report)
1. Read the report. Confirm it wrote ONLY its write-set (`git status`).
2. **Re-run the acceptance command yourself** from a clean venv — do not trust the worker's paste (FM-09).
3. Green → merge as ONE meaningful commit (builds the commit history judges want). Update EXECUTION.md
   with the commit hash. Update the task board.
4. Red/scope-violation → REVISE with the specific gap. Never merge red.
5. After each merge, re-check HANDOFF vs EXECUTION active-wave (no FM-01 drift).
