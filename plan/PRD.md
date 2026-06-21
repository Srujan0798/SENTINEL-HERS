# PRD — SENTINEL

## Problem
Engineering teams lose significant time during production incidents, deployment failures, and
infra debugging because the toolchain is fragmented across Slack, Grafana, Jira, GitHub, Notion,
and dashboards. Incident response is reactive, slow, manual.

## Goal
One AI-native operational workspace: unify log monitoring, deployment tracking, incident
summarisation, task assignment, and AI-assisted debugging into a single coherent product.

## Users & roles (RBAC)
- **Owner / Admin** — full control, team & integration config.
- **Responder / Engineer** — triage, assign, resolve, comment.
- **Viewer / Stakeholder** — read dashboards, timelines, analytics.

## Functional requirements (mapped to waves)
| # | Requirement | Wave |
|---|---|---|
| F1 | Team-based auth with RBAC | W1 |
| F2 | Real-time incident dashboard w/ severity classification + triage | W2 |
| F3 | Centralised log & alert monitoring interface | W3 |
| F4 | AI-generated incident summaries + root-cause suggestions | W4 |
| F5 | GitHub/GitLab integration for deployment + commit tracking | W5 |
| F6 | Service health monitoring with uptime visualisation | W3 |
| F7 | Integrated team communication channels per incident | W6 |
| F8 | Incident timeline generation with full event provenance | W5 |
| F9 | Task assignment, escalation, SLA-aware workflow | W6 |
| F10 | Analytics dashboard for deployment stability + incident frequency | W7 |

## Exceptional (bonus — maps to W4/W7/W8)
Conversational AI chatbot · K8s/Docker monitoring · auto-postmortem · voice-to-ticket ·
predictive anomaly detection (ML).

## Success metrics
- Sacred demo path runs end-to-end with zero errors (`scripts/seed_demo.py`).
- Realtime event latency < 1s P95.
- AI summary+root-cause eval pass@5 ≥ 50% on seeded incidents.
- Auth: 403 enforced on every under-privileged route (RBAC integration tests green).
- One-command boot (`docker compose up`) + one-command demo seed.

## Non-goals (see docs/SCOPE_GUARD.md)
Real multi-tenant billing, full compliance certification, mobile native apps, production-scale HA.
