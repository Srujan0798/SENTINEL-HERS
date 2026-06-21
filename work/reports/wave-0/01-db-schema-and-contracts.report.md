# REPORT — wave-0 / 01-db-schema-and-contracts

- **Agent:** deep (Tier-2 worker)
- **Result:** DONE
- **Date:** 2026-06-19

## What I changed
- `schema/migrations/versions/001_initial_schema.py` — Alembic migration with all 16 entities
- `schema/alembic.ini` — Alembic configuration
- `schema/migrations/env.py` — Alembic environment setup
- `schema/migrations/script.py.mako` — Migration template
- `.specify/specs/wave-0/contracts/openapi.yaml` — Complete OpenAPI 3.1 specification (56KB)
- `docs/schemas/erd.md` — Mermaid ERD with all entities and relationships

## Acceptance proof (REQUIRED — FM-09)
```
$ cd /Users/srujansai/Desktop/SENTINEL-HERS/schema && DATABASE_URL="postgresql://sentinel:sentinel@localhost:5432/sentinel" alembic upgrade head
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> 001, Initial schema - all SENTINEL entities

$ python3 -c "
from openapi_spec_validator import validate
import yaml

with open('.specify/specs/wave-0/contracts/openapi.yaml', 'r') as f:
    spec = yaml.safe_load(f)

try:
    validate(spec)
    print('OpenAPI spec validation: PASSED')
except Exception as e:
    print(f'OpenAPI spec validation: FAILED')
    print(f'Error: {e}')
"
OpenAPI spec validation: PASSED
```

## Entities implemented (16 total)
1. **teams** — Multi-tenant scoping
2. **roles** — RBAC with JSONB permissions
3. **users** — Auth with team_id FK
4. **incidents** — SEV1-4, status state machine
5. **log_entries** — Full-text search with pg_trgm
6. **alerts** — Alert management with resolution tracking
7. **service_health** — Uptime monitoring
8. **deployments** — Deploy tracking with rollback support
9. **commits** — VCS integration with bidirectional FK
10. **timeline_events** — Provenance with source/actor/ts columns
11. **tasks** — Incident task assignment
12. **slas** — SLA tracking with breach detection
13. **channels** — Per-incident communication
14. **messages** — Channel messages with AI attribution
15. **anomaly_scores** — ML anomaly detection results
16. **alembic_version** — Migration tracking

## OpenAPI coverage
- **auth** — Register, login, refresh, me
- **teams** — List, get
- **incidents** — CRUD, assign, escalate
- **logs** — Ingest, search
- **alerts** — CRUD, resolve
- **health** — Service health CRUD
- **deployments** — CRUD, rollback
- **commits** — List
- **timeline** — Get/add events
- **tasks** — CRUD
- **sla** — List, get
- **channels/messages** — List, send
- **ai** — Summarize, root-cause, chat, postmortem
- **analytics** — Metrics, time series, services
- **integrations** — GitHub/GitLab webhooks
- **realtime** — SSE event stream
- **metrics** — Prometheus endpoint

## Deviations from brief
- None

## Gotchas hit (→ orchestrator adds to docs/waves/wave-0-gotchas.md)
- SQLAlchemy `op.execute()` interprets `:read` as bind parameters in JSON strings. Used `text()` with escaped colons (`\\:read`) for role seeding.
- Enum types must be created before tables that reference them. Used raw SQL approach to avoid SQLAlchemy enum creation conflicts.

## Follow-ups / parked (→ BACKLOG)
- None
