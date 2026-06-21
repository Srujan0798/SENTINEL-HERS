# Security Posture — SENTINEL

This document records the security controls in place and the known tradeoffs made
for the hackathon MVP, with the hardening path for each.

## Controls in place

- **Authentication:** JWT access (15 min) + refresh (30 day) tokens, HS256, separate
  signing secrets. Passwords hashed with bcrypt.
- **Authorization / multi-tenancy:** every data query is scoped by `team_id` derived
  from the verified token (not from client input). Cross-tenant reads are not possible
  through the API surface.
- **Webhook authenticity:** GitHub webhooks verified via HMAC-SHA256
  (`X-Hub-Signature-256`); GitLab via shared token. Invalid signatures are rejected
  before any processing.
- **Tenant-scoped webhooks:** deployment/commit events are written to the team
  identified on the webhook URL and validated against the DB — unknown teams are
  rejected (no placeholder/default tenant).
- **Secrets:** all secrets are environment variables; `.env` is gitignored. The repo
  ships only `.env.example` with placeholders.
- **Transport headers:** auth middleware does not echo tokens into response headers.

## Known tradeoffs (accepted for the MVP)

### 1. Realtime tokens in query string (MEDIUM)
SSE/WebSocket connections pass the JWT as a `?token=` query parameter because browser
`EventSource` cannot set an `Authorization` header. Tokens in URLs can land in access
logs.
**Mitigation today:** tokens are short-lived (15 min); realtime auth decodes the token
without a DB lookup and only extracts `team_id`/`sub`.
**Hardening path:** issue a short-lived, single-use "connect ticket" via an
authenticated `POST`, exchanged on connect and immediately invalidated.

### 2. Tokens in `localStorage` (MEDIUM)
The frontend stores access/refresh tokens in `localStorage`, which is readable by JS
and therefore XSS-sensitive.
**Mitigation today:** strict input handling; tokens are short-lived; no third-party
script injection surface in the dashboard.
**Hardening path:** move the refresh token to an `HttpOnly; Secure; SameSite=Strict`
cookie set by the backend, keep the access token in memory only, and refresh via the
cookie-bearing `/auth/refresh` endpoint.

### 3. Shared webhook secret (LOW)
GitHub/GitLab webhook secrets are global rather than per-team, so a party holding the
secret could target any `team_id`.
**Hardening path:** bind a per-team webhook secret at integration-registration time and
verify the signature against that team's secret, deriving the team from the secret used.

## Reporting
This is an academic project. For real deployments, rotate all secrets, enable TLS
everywhere, and complete the hardening items above before exposing the API publicly.
