# SCOPE GUARD — SENTINEL (FM-08)

> Every worker brief lists files it MAY and MUST-NOT touch. Extras → BACKLOG, never silently built.

## IN (build now)
- Team auth + RBAC (3 roles)
- Realtime incident dashboard, severity SEV1–4, triage
- Centralised log/alert monitoring + uptime visualisation
- AI summaries, root-cause, NL chatbot, auto-postmortem
- GitHub/GitLab deploy+commit tracking, timeline + provenance
- Task assignment, escalation, SLA workflow, per-incident comms
- Analytics (deploy stability, incident frequency), anomaly ML, k8s/docker monitoring
- Voice-to-ticket (bonus), one-command deploy + observability

## OUT (do NOT build)
- Multi-tenant billing / payments
- Full compliance certification (DPDP/GDPR/HIPAA paperwork)
- Native mobile apps
- Production-grade HA / multi-region
- SSO/SAML enterprise identity (basic JWT auth only)

## LATER (BACKLOG if time remains)
- Slack/Teams two-way bridge
- Advanced ML model training pipeline
- Multi-language i18n

## The sacred demo path (protect before adding breadth)
Login → live dashboard → seeded incident fires → AI summary+root-cause → assign+escalate w/ SLA →
timeline w/ provenance → analytics trend. If a change risks this path, stop and confirm.
