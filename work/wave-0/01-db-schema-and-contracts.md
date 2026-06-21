# TASK — wave-0 / 01-db-schema-and-contracts

## Goal
Define the canonical data model + OpenAPI contract that ALL later waves code against (contracts-first).

## Context
- Wave: 0. Run after (or parallel-safe with) 00 — disjoint write-set.
- This is the single source of truth (FM-05/FM-12). Frontend + backend generate from it.

## Write-set (ONLY these)
- schema/  (SQL + Alembic migrations, or Supabase migration SQL)
- .specify/specs/wave-0/contracts/  (openapi.yaml + JSON schemas)
- docs/schemas/  (ERD + entity docs)

## Forbid-set
- docker-compose.yml, src/**, frontend/**

## Blast radius
r1.

## Entities (from plan/ARCHITECTURE.md — model all)
Team, User, Role, Incident, Severity(SEV1-4), LogEntry, Alert, ServiceHealth, Deployment, Commit,
TimelineEvent, Task, SLA, Channel, Message, AnomalyScore.

## Steps
1. Write migrations creating all tables with FKs, indexes, and provenance columns
   (`source, actor, ts`) on TimelineEvent.
2. Author `openapi.yaml` covering auth, incidents, logs, health, ai, integrations, tasks, analytics.
3. Generate an ERD into `docs/schemas/erd.md` (Mermaid).

## Acceptance (PROOF — FM-09)
- Command: `alembic upgrade head && npx @redocly/cli lint .specify/specs/wave-0/contracts/openapi.yaml`
- Expected: migration applies clean; OpenAPI lints with 0 errors.

## Report to
`work/reports/wave-0/01-db-schema-and-contracts.report.md`
