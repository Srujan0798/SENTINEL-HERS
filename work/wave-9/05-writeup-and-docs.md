# TASK — wave-9 / 05-writeup-and-docs

> Self-contained brief. The worker needs NOTHING outside this file + the repo.

## Goal (one sentence)
Write the **required** `WRITEUP.md` (1–2 pages: technical decisions, challenges, what-I'd-do-with-more-time)
and polish `README.md` so a judge can go from clone → running in minutes and understands the system —
both are explicit submission requirements.

## Context (just enough)
- Wave: 9 — Submission Hardening.
- **Depends on: wave-9/03 + wave-9/04** (needs the real live URLs to embed).
- Submission rules (from `ps.md`) require: live deployment URL, public GitHub repo, README with setup,
  and a 1–2 page write-up. The write-up is graded alongside the rubric
  (System Design 25% · Realtime 20% · AI 20% · Security 15% · UI/UX 10% · DevOps 10%).
- Truthful sources to mine: `plan/ARCHITECTURE.md`, `plan/EXECUTION.md`, `plan/PRD.md`,
  `docs/`, the wave reports in `work/reports/`, and the real test count from wave-9/02.

## Write-set (you may ONLY create/edit these — FM-13)
- `WRITEUP.md` (new)
- `README.md` (edit — add live URLs, demo credentials, architecture diagram link, test badge/count)
- `docs/PRODUCTION_WALKTHROUGH.md` (new — the exact demo path judges should click)

## Forbid-set (do NOT touch)
- Any code, tests, deploy config
- Do NOT invent metrics. Every number (test count, latency, uptime) must come from a real report/run.

## Blast radius
r0 — docs only. Auto.

## Steps
1. `WRITEUP.md` structure:
   - **What & why** (the fragmented-toolchain problem SENTINEL replaces).
   - **Architecture & key technical decisions** — map each choice to a rubric axis (why FastAPI+Next, why SSE+WS for realtime, RBAC model, AI provider abstraction w/ mock fallback, anomaly ML).
   - **Challenges faced** — be honest (e.g. the missing-logs-module regression and how the dual-tier process caught it; test isolation; cloud config).
   - **What I'd do with more time** — pull real items from `BACKLOG.md` if present.
   - Keep it to ~2 pages. Judges skim — lead with a diagram and a bullet summary.
2. `README.md`: live URLs (frontend + backend), demo login creds (from `scripts/seed_demo.py`), one-command local run, the sacred demo path, real test count from wave-9/02's report.
3. `docs/PRODUCTION_WALKTHROUGH.md`: numbered click-path matching the demo path in CLAUDE.md, with what to point out at each step (severity triage, AI summary provenance, SLA timer, analytics trend).

## Acceptance (must produce PROOF — FM-09)
- Command: `wc -w WRITEUP.md && test $(wc -w < WRITEUP.md) -ge 500 && echo "WRITEUP length OK"`
- Expected: prints the word count and `WRITEUP length OK` (≥500 words ≈ the 1–2 page bar).
- Command: `grep -c "https://" README.md` → must be ≥2 (live frontend + backend URLs present). Paste it.
- In your report, paste the section headings of WRITEUP.md so the orchestrator can verify all four required sections exist.

## Guardrails to obey
- FM-09 no invented numbers — cite the run/report each figure came from · FM-07 no secrets/creds beyond the intentional demo login
- Honest status: if a brownie feature is partial, say "partial", don't oversell.

## Report to
`work/reports/wave-9/05-writeup-and-docs.report.md`
