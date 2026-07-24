You are a Tier-2 worker. Demo polish for judges. Only after live URLs work.

# TASK — production walkthrough proof

Write-set:
- docs/PRODUCTION_WALKTHROUGH.md (update with real URLs if provided)
- scripts/smoke_demo.sh (new) OR docs/JUDGE_DEMO.md with exact clicks
- work/reports/wave-11/04-demo-proof.report.md

Steps:
1. Document exact 7-step judge path with screenshots placeholders.
2. smoke script: healthz, register/login or demo login, list incidents, AI summary endpoint with mock.
3. Confirm seed is idempotent.

Do not fake HTTP against production if keys missing — local smoke OK.

Acceptance: script exits 0 against local or documented BLOCKED with reason.

Then STOP.
