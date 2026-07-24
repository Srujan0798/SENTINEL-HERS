# SENTINEL — Production Walkthrough (Judge Demo Path)

> Exact click-path for evaluators. Protect this path before adding breadth.
> Local: `http://localhost:3000` · Production: set after Vercel deploy (see README).

## Prerequisites

| Item | Value |
|------|--------|
| Demo email | `demo@sentinel.io` |
| Demo password | `Sentinel2026!` |
| Seed | `make seed` (local) or Render `preDeployCommand` (prod, idempotent) |
| AI | Mock works offline; set `ANTHROPIC_API_KEY` on Render for live summaries |

---

## 1. Login (30s)

1. Open the frontend URL.
2. Sign in with the demo credentials above.
3. **Point out:** team-scoped JWT session; failed login does not leak whether the email exists beyond a clean error.

**Success:** land on the live incident dashboard.

---

## 2. Live incident dashboard (60s)

1. Confirm open incidents include a **SEV1** titled roughly *Payment service cascade failure*.
2. Note severity badges (SEV1–4) and status chips (open / investigating / …).
3. **Point out:** this is the triage surface replacing “scroll Slack + Grafana tabs.”

**Success:** SEV1 is visible without navigating away.

---

## 3. Open the SEV1 — AI summary + root cause (90s)

1. Click the SEV1 incident.
2. Trigger / view **AI summary** (panel or API-backed UI action).
3. Trigger **root-cause suggestions**.
4. **Point out:**
   - Summary is grounded in ingested logs/alerts for that incident.
   - With mock AI, text is deterministic (good for offline demo).
   - With live Claude/Gemini keys on Render, answers are model-backed; missing keys fall back to mock with a server WARNING (fail safe + loud).

**Success:** summary + ranked causes appear without leaving the incident.

---

## 4. Assign + escalate with SLA (60s)

1. Assign the incident to the demo user (or another team member if present).
2. Change status toward investigating / mitigating.
3. Open or note **tasks** / **SLA** indicators on the incident.
4. **Point out:** SLA-aware workflow and task list is in-product — not a side Jira tab.

**Success:** assignee + tasks visible; SLA timer semantics explainable in one sentence.

---

## 5. Timeline with provenance (45s)

1. Open the incident **timeline**.
2. Walk events: detection → acknowledgement → investigation → mitigation (seeded).
3. **Point out:** each event carries source/actor style provenance — judges can audit *who/what* produced the history.

**Success:** multi-step timeline is non-empty and chronological.

---

## 6. Comms channel (optional 45s)

1. Open the per-incident communication panel.
2. Send a short message; mention if UI supports `@`.
3. **Point out:** incident-scoped channel replaces “which Slack thread was that?”

---

## 7. Analytics trend (45s)

1. Navigate to **Analytics**.
2. Show MTTR / severity breakdown / open vs resolved counts.
3. If anomaly scores are seeded, note the predictive signal and that model-raised alerts are low-severity + labeled (provenance).

**Success:** at least one aggregate chart or KPI row renders for the demo team.

---

## 8. Brownie surfaces (if time — 2 min)

| Feature | Where | What to say |
|---------|--------|-------------|
| RAG chatbot | Chat panel | Natural-language Q over team logs/incidents with citations |
| Containers | Monitoring | Live Docker/K8s when available; clear `unavailable` fallback on Render |
| Voice-to-ticket | Voice control | Speak → structured incident; mic-denied falls back to text |
| Postmortem | Incident action | Generate Markdown postmortem from real timeline data |

Be honest if a brownie path is partial — overselling is worse than “implemented, hardening in progress.”

---

## 9. Ops credibility (30s)

1. Hit backend `GET /healthz` → `{"status":"ok"}`.
2. Hit `GET /metrics` → Prometheus text.
3. **Point out:** the platform is self-observing, not a black-box demo script.

---

## Failure recovery (if seed missing)

```bash
# local
make up && make seed

# or against a running API
SENTINEL_URL=https://<your-api> python scripts/seed_demo.py
```

Seed is **idempotent**: re-running does not duplicate the SEV1 when incidents already exist.
