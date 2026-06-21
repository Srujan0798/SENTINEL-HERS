# TASK — wave-8 / 01-demo-hardening

## Goal
Polish the live demo path so it never breaks during a 3-minute judge walkthrough.
Seed realistic data, ensure the happy path works on a fresh DB, fix any rough edges.

## Context
- Wave: 8. All other waves complete. Demo seed already at `scripts/seed_demo.py`.
- DB must be portable (works in dev container and on judges' laptops).

## Write-set (ONLY these)
- scripts/
- docker-compose.yml (extend with seed service)
- scripts/demo_smoke_test.sh

## Forbid-set
- src/backend/** (don't change business logic), src/frontend/src/components/ui/**

## Blast radius
r1.

## Steps
1. Polish `scripts/seed_demo.py`:
   - Make idempotent (running twice doesn't crash).
   - Add a "JudgeDemo" team with predictable credentials shown in logs.
   - Seed at least 3 incidents (1 SEV1, 1 SEV2, 1 SEV3), 20+ logs, 5+ alerts, 4+ tasks.
   - Print final demo URL + clickable test creds to console in a nice box.
2. Add `scripts/demo_smoke_test.sh`: bash script that hits every key endpoint after seeding
   and prints a ✅/❌ summary. Exits non-zero on any failure. FM-11 fail-loud.
3. Add a "demo" service to `docker-compose.yml` that:
   - Waits for backend healthy.
   - Runs the seed.
   - Marks itself complete (so `make demo` knows it's ready).
4. Update `HOW_TO_RUN.md` with a "Demo in 60 seconds" section.

## Acceptance (PROOF — FM-09)
```
bash scripts/demo_smoke_test.sh
# Expected: all checks pass
# Test creds printed: demo@sentinel.io / Demo123!
```

## Report to
`work/reports/wave-8/01-demo-hardening.report.md`
