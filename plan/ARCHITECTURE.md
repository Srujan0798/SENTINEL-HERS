# ARCHITECTURE — SENTINEL

## High-level
```
Browser (Next.js 15 / Tailwind + shadcn)
   │  HTTPS + SSE/WebSocket
   ▼
Nginx ──► FastAPI (Python 3.11)
              │
   ┌──────────┼─────────────┬───────────────┬──────────────┐
   ▼          ▼             ▼               ▼              ▼
PostgreSQL  Redis        AI Layer      Integrations    Realtime hub
(Supabase) (pub/sub +   (Claude /     (GitHub/GitLab  (SSE + WS
            SLA timers)  Gemini)        webhooks,       fan-out)
                                        K8s/Docker)
   │
   ▼
Prometheus ──► Grafana   (metrics, uptime, SLOs)
```

## Subsystems (own a wave each)
- **auth/rbac** (W1) — JWT + refresh; role policy middleware; team scoping.
- **incidents** (W2) — model, severity SEV1–4, triage state machine.
- **realtime** (W2) — SSE primary, WebSocket for bidirectional comms; Redis fan-out.
- **logs/ingest + health** (W3) — log/alert intake, indexed search, uptime probes, /metrics.
- **ai** (W4) — summary, root-cause ranking, RAG chatbot, auto-postmortem. Provider-abstracted.
- **integrations + timeline** (W5) — VCS webhooks, deploy/commit linking, provenance log.
- **tasks/sla + comms** (W6) — assignment, escalation, SLA timers, per-incident channels.
- **analytics + ml + containers** (W7) — trend dashboards, anomaly detection, k8s/docker status.

## Key design rules
- **Contracts-first:** OpenAPI spec in `.specify/specs/wave-0/contracts/` is the source of truth;
  frontend + backend code to it. Generated, not hand-typed (FM-12).
- **One metrics source** (FM-05): all numbers derive from `results/metrics.json` / Prometheus.
- **Realtime everywhere:** any state change that a human watches emits an event to the realtime hub.
- **Provenance:** every timeline event carries `{source, actor, ts, payload_ref}` — immutable.
- **AI provider abstraction:** `src/backend/ai/provider.py` wraps Claude/Gemini; swappable, keys in `.env`.
- **Fail loud** (FM-11): no swallowed errors in incident-critical paths; missing input → explicit error.

## Data model (core entities)
`Team, User, Role, Incident, Severity, LogEntry, Alert, ServiceHealth, Deployment, Commit,
TimelineEvent, Task, SLA, Channel, Message, AnomalyScore`. Full ERD in `docs/schemas/`.
