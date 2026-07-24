# How to use these paste packs

## Order

| When | Open how many OpenCode windows | Paste file(s) |
|------|--------------------------------|---------------|
| **Now** | 3 parallel | `ROUND1_AGENT_B.md` · `ROUND1_AGENT_C.md` · `ROUND1_AGENT_E.md` |
| After B+C+E reports are merged | 1 then 1 | `ROUND2_AGENT_A.md` → wait → `ROUND2_AGENT_D.md` |
| After you have live Render+Vercel URLs | 1 | `ROUND3_AGENT_F_URLS.md` (fill URLs first) |
| Optional race shield | 1 | `ROUND3_AGENT_G_CI.md` |

## Rules

1. Each window = **one** paste file. Entire file. Nothing else.
2. Agent works in repo: `/Users/srujansai/Desktop/SENTINEL-HERS` (or your clone path).
3. Agents **do not push, deploy, or commit** unless you tell them.
4. When an agent finishes, take `work/reports/wave-10/*.report.md` and send to orchestrator for review.
5. **Never** run A and D at the same time.

## You (human) still must

See `HUMAN_DEPLOY.md` — push + Render + Vercel. Agents cannot click those.
