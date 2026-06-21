# TASK — wave-<N> / <task-id>

> Self-contained brief. The worker needs NOTHING outside this file + the repo.
> Worker uses its OWN skills. Does NOT plan beyond this task. Writes ONLY to the write-set below.

## Goal (one sentence)
<what success looks like>

## Context (just enough)
- Wave: <N> — <wave name>
- Depends on (already merged): <list or "none">
- Relevant contract: `.specify/specs/wave-<N>/contracts/<file>`

## Write-set (you may ONLY create/edit these — FM-13)
- <path/>
- <path/>

## Forbid-set (do NOT touch)
- everything else, especially other agents' write-sets and shared root config

## Blast radius
r<0-5> — <auto / confirm / blocked>

## Steps
1. ...
2. ...

## Acceptance (must produce PROOF — FM-09)
- Command: `<exact command>`
- Expected: `<exact observable result>`
- Paste the command output into your report. No "done" without it.

## Guardrails to obey
- FM-09 no false status · FM-11 fail loud, no swallowed errors · FM-08 no scope creep
- Seed any data you need; never invent synthetic data to "pass"

## Report to
`work/reports/wave-<N>/<task-id>.report.md` (use REPORT_TEMPLATE.md)
