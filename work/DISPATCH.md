# DISPATCH — Wave 9 (done) & Wave 10 (OpenCode)

> Orchestrator owns this file. For **OpenCode agents**, use the dedicated pack:  
> **`work/OPENCODE_DISPATCH.md`** (copy-paste roster + worker prompt + order).

## Worker prompt (prepend to EVERY task)

```
You are a Tier-2 worker on the SENTINEL build. Execute ONE self-contained task and stop.
1. Read the task file. Build ONLY what it asks. Write ONLY to its write-set. Never touch the forbid-set.
2. Use your own skills/tools. Do NOT redesign or expand scope (FM-08).
3. Fail loud (FM-11): no except: pass, no silent fallback, no synthetic data to fake a pass.
4. Run the acceptance command. Paste its REAL output into your report (FM-09). No proof = not done.
5. Write your report to work/reports/<wave>/<task-id>.report.md using REPORT_TEMPLATE.md.
6. If blocked or ambiguous, report BLOCKED with the specific question — do not guess.
Then STOP. The orchestrator reviews, re-runs acceptance, and merges.
[TASK FILE FOLLOWS]
```

## Wave-9 — Submission Hardening

| # | Task | Status |
|---|---|---|
| 9.1 | restore-logs | ✅ `a7d4277` |
| 9.2 | green-suite | ✅ `4e84356` |
| 9.3 | render-deploy | ✅ `5e93840` |
| 9.3b | CORS + seed | ✅ `258fc66` |
| 9.4 | vercel-frontend | ✅ `acccc70` |
| 9.5 | writeup-and-docs | ✅ (this wave) |
| 9.6 | live-ai-wiring | ✅ `285bb38` |

**Human residual:** `git push` + Render Blueprint + Vercel project + paste live URLs into README.

## Wave-10 — Brownie (assign to OpenCode)

| # | Task file | Parallel | Agent suggestion |
|---|---|---|---|
| 10.1 | `work/wave-10/01-conversational-chatbot.md` | serial w/ 10.4 | Agent A |
| 10.2 | `work/wave-10/02-predictive-anomaly.md` | yes | Agent B |
| 10.3 | `work/wave-10/03-container-monitoring.md` | yes | Agent C |
| 10.4 | `work/wave-10/04-postmortem-export.md` | after 10.1 | Agent D |
| 10.5 | `work/wave-10/05-voice-to-ticket-e2e.md` | yes | Agent E |

**Order:** Round1 `10.2 ∥ 10.3 ∥ 10.5` → Round2 `10.1 → 10.4`.

Full paste instructions: `work/OPENCODE_DISPATCH.md`.
