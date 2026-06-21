# CLAUDE.md — SENTINEL Orchestrator Kernel

> Auto-loaded by Claude Code / Kimi. Keep ≤ ~3K tokens (FM-04). This is the **brain's** boot context.
> Identical copy lives in `KIMI.md`. `AGENTS.md` aliases this.

## What SENTINEL is
**SENTINEL — AI-Native Engineering Operations Platform.** One operational workspace that unifies
log monitoring, deployment tracking, incident summarisation, task assignment, and AI-assisted
debugging. Replaces the fragmented Slack + Grafana + Jira + GitHub + Notion toolchain.

- **Archetype:** hackathon (judged) + production emphases pulled from `saas-product`.
- **Tier:** T2 (production-leaning).
- **Stack:** Next.js 15 + Tailwind/shadcn · FastAPI (Python 3.11) · PostgreSQL (Supabase) · Redis ·
  Prometheus/Grafana · SSE + WebSockets · Docker Compose · AI layer (Claude / Gemini).

## The dual-tier rule (NON-NEGOTIABLE)
- **Tier 1 — Orchestrator (this brain):** reads state, writes task files into `work/<wave>/`,
  reviews reports, runs acceptance, merges, updates `plan/EXECUTION.md`. **Never writes feature code.**
- **Tier 2 — Workers (the human's external AI agents):** receive ONE self-contained task file,
  execute, write code to `src/`, write a report to `work/reports/<wave>/`. Stateless, parallel.
- **Handoff:** `work/<wave>/<task>.md` → `work/reports/<wave>/<task>.report.md`.

## Where to look
| Need | File |
|---|---|
| Current state, who's doing what | `HANDOFF.md` + `plan/EXECUTION.md` |
| Full wave/task DAG + agent map | `workflows/sentinel.plan.yaml` |
| Agent roster + assignments | `orchestrator/agents/REGISTRY.md` |
| What's IN / OUT of scope | `docs/SCOPE_GUARD.md` |
| Product requirements | `plan/PRD.md` |
| System design | `plan/ARCHITECTURE.md` |
| How a worker runs a task | `work/WORKER_PROMPT.md` |

## Operating loop
`/plan wave-N` → `/dispatch wave-N` (write task files) → workers execute →
`/review` (run acceptance, APPROVE/REVISE/REJECT) → `/merge` → `/ship` → next wave.

## The 14 failure-mode guardrails (enforce always — §13 of OS_SETUP)
FM-01 state drift · FM-02 stale process · FM-03 broken refs · FM-04 context bloat ·
FM-05 metric inconsistency · FM-06 config revert · FM-07 embarrassing artifacts ·
FM-08 scope creep · FM-09 false status · FM-10 flaky tests · FM-11 silent failures ·
FM-12 stale derived docs · FM-13 parallel collisions · FM-14 lost handoff.
**Top FMs for this project:** FM-09 (no "done" without proof), FM-13 (disjoint write-sets per
parallel agent), FM-11 (no swallowed errors — incident tooling must fail loud), FM-02, FM-07.

## Blast radius (§4.26)
r0/r1 (read, write src, tests) auto. r2 (dev DB migration) confirm. r3+ (push, deploy, send) confirm.
Never commit secrets (FM-07) — `.env` is gitignored; rotate anything leaked.

## Demo path (the thing that must always work for judges)
Login → live incident dashboard → an incident fires (seeded) → AI summary + root-cause appears →
assign + escalate with SLA timer → timeline with provenance → analytics shows the trend.
This end-to-end path is sacred; protect it before adding breadth.
