# OPENCODE DISPATCH — Assign these to your agents

> Orchestrator finished wave-9 code/docs that can be done offline.  
> **You** push + click Render/Vercel. **OpenCode agents** run wave-10 brownie tasks below.  
> One agent = one task file. Disjoint write-sets. Paste **WORKER PROMPT + task file** only.

---

## Before any OpenCode agent runs

### Human checklist (do once)

1. `git push origin main` (branch is ahead of origin — confirm intentionally).
2. **Render** → New → Blueprint → this repo → apply `render.yaml`.
3. Render env (dashboard): `ANTHROPIC_API_KEY`, optional `GEMINI_API_KEY`, temp `CORS_ORIGINS`.
4. **Vercel** → import repo → **Root Directory = `src/frontend`**.
5. Vercel env: `NEXT_PUBLIC_API_BASE_URL=https://<render-host>`.
6. After Vercel URL exists: set Render `CORS_ORIGINS=https://<vercel-host>` → redeploy.
7. Paste both live HTTPS URLs into `README.md` (table at top).
8. Smoke: `/healthz`, login `demo@sentinel.io` / `Sentinel2026!`, open SEV1.

### Prepend this to EVERY agent paste

```
You are a Tier-2 worker on the SENTINEL build. Execute ONE self-contained task and stop.
1. Read the task file. Build ONLY what it asks. Write ONLY to its write-set. Never touch the forbid-set.
2. Use your own skills/tools. Do NOT redesign or expand scope (FM-08).
3. Fail loud (FM-11): no except: pass, no silent fallback, no synthetic data to fake a pass.
4. Run the acceptance command. Paste its REAL output into your report (FM-09). No proof = not done.
5. Write your report to the path named in the task (work/reports/wave-10/…).
6. If blocked or ambiguous, report BLOCKED with the specific question — do not guess.
Then STOP. The orchestrator reviews, re-runs acceptance, and merges.
[TASK FILE FOLLOWS]
```

Full copy also in `work/WORKER_PROMPT.md`.

---

## Wave-10 agent roster (brownie / rubric-max)

| Agent label (suggestion) | Task file | Write-set summary | Depends | Parallel? |
|---|---|---|---|---|
| **Agent A — Chat** | `work/wave-10/01-conversational-chatbot.md` | `src/backend/ai/` (chat), `components/chat/`, `test_ai_chat.py` | suite green + 9.6 AI | **Serial with D** (both touch `ai/`) |
| **Agent B — Anomaly** | `work/wave-10/02-predictive-anomaly.md` | `src/backend/ml/`, analytics routes/UI, `test_anomaly.py` | suite green | ✅ parallel |
| **Agent C — Containers** | `work/wave-10/03-container-monitoring.md` | docker/k8s/containers integrations, monitoring UI, `test_containers.py` | suite green | ✅ parallel |
| **Agent D — Postmortem** | `work/wave-10/04-postmortem-export.md` | `src/backend/ai/` (postmortem), incidents UI, `test_postmortem.py` | suite green + 9.6 | **After A** (or split packages) |
| **Agent E — Voice** | `work/wave-10/05-voice-to-ticket-e2e.md` | `src/backend/voice/`, VoiceRecorder, `test_voice.py` | suite green | ✅ parallel |

### Recommended schedule

```
Round 1 (parallel):  B  ·  C  ·  E
Round 2 (serial):    A  then  D     # both write under src/backend/ai/
```

If you only have one OpenCode seat: order `B → C → E → A → D`.

### Collision rules (FM-13)

- **Never** run A and D at the same time.
- Do not let agents edit `api/main.py`, `render.yaml`, or each other’s write-sets.
- After each report: orchestrator (or you) runs the acceptance command from a clean shell; only then commit.

---

## Optional mop-up agents (if needed after deploy)

| Label | Goal | Files |
|---|---|---|
| **Agent F — URL polish** | Paste live Render+Vercel URLs into README + SUBMISSION | `README.md`, `docs/SUBMISSION.md` only |
| **Agent G — CI** | Add `.github/workflows/ci.yml` pytest + frontend build | new workflow file only |

These are **not** pre-written as full task files; only launch if you want them.

---

## What is already done (do NOT reassign)

| Item | Evidence |
|---|---|
| Logs module restored | `a7d4277` |
| Full suite green (150) | `4e84356` + later AI test |
| Render blueprint + Dockerfile | `5e93840` |
| CORS env + idempotent seed + requests | `258fc66` |
| Vercel config + frontend env wiring | `acccc70` |
| Live AI providers + mock fallback | `285bb38` |
| WRITEUP + walkthrough + README polish | wave-9/05 (this push) |

---

## Merge loop (you or orchestrator)

For each returned `work/reports/wave-10/*.report.md`:

1. `git status` — only write-set files changed?
2. Re-run the task’s acceptance command yourself (FM-09).
3. Green → one meaningful commit → update `plan/EXECUTION.md`.
4. Red → send REVISE with the exact gap; do not merge.

---

## Done definition for “project complete”

- [ ] `origin/main` has all commits  
- [ ] Live frontend + backend HTTPS URLs in README  
- [ ] Judge walkthrough works on production seed  
- [ ] WRITEUP.md present (≥500 words)  
- [ ] 150+ tests still green on clean run  
- [ ] Optional: all 5 wave-10 reports APPROVED  
