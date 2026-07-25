# PRODUCT.md — SENTINEL

> Impeccable init · Brand + product law for every UI/agent change.  
> Last updated: 2026-07-25

---

## 1. One sentence

**SENTINEL** is the single operational workspace for engineering teams during production pain — where incidents, logs, deploys, AI diagnosis, tasks, and team chat live in one war room instead of Slack + Grafana + Jira + GitHub + Notion.

---

## 2. Audience

| Who | Job to be done |
|-----|----------------|
| **Primary** | On-call engineers & incident commanders mid-SEV1 |
| **Secondary** | METIS judges evaluating Hard-track coherence in &lt;3 minutes |
| **Tertiary** | Team leads reviewing MTTR / deploy stability |

---

## 3. Brand identity

| Axis | Choice |
|------|--------|
| **Name** | SENTINEL (always caps in wordmark) |
| **Personality** | Calm under fire · precise · no fluff · mission-control, not consumer SaaS |
| **Voice** | Short verbs, active, no apology fluff. Errors say what to do next. |
| **Promise** | “From alert to action without leaving this screen.” |
| **Anti-brand** | Soft pastels, playful illustration, generic “AI startup” purple gradients, empty marketing hero with no live path |

### Signature metaphor

**Radar console for production.** The product feels like a phosphor radar + flight deck: density of signal, amber attention, ice-cold data, red only for true SEV1.

---

## 4. Core product loop (sacred)

```
Login (demo one-click)
  → Dashboard (live KPIs + open SEV1 CTA)
  → Incident war room (timeline · tasks · SLA · AI · comms · chat)
  → Monitoring / Deployments / Analytics
```

This path must never break. Prefer fixing it over new features.

---

## 5. Feature pillars (map to problem statement)

1. **Identity & control** — team auth, RBAC  
2. **Incident command** — severity, triage, assign, SLA  
3. **Signal** — logs, alerts, health, containers  
4. **Provenance** — timeline, deploys, commits  
5. **AI assist** — summary, RCA, chat, postmortem  
6. **Team** — per-incident channel  
7. **Trends** — analytics, anomaly risk  

---

## 6. Demo contract (judges)

| Field | Value |
|-------|--------|
| URL | https://sentinel-hers.vercel.app |
| API | https://sentinel-api-clu9.onrender.com |
| Account | `demo@sentinel.io` / `Sentinel2026!` |
| Proof | `/api/demo-status` → `ready: true` + open SEV1 |

---

## 7. Non-goals (eternal)

- Becoming a full Slack replacement  
- Full multi-region SaaS billing  
- Hiding empty states with fake KPI theater  
- Claiming “complete” without live proof (FM-09)

---

## 8. Success metrics (product)

| Metric | Target for demo |
|--------|-----------------|
| Time to SEV1 war room after login | &lt; 15 seconds |
| Dead nav links | 0 |
| Login bounce / empty nav | 0 |
| Live demo-status ready | true after every deploy |

---

## 9. Related docs

- Visual system: [`DESIGN.md`](./DESIGN.md)  
- Architecture: [`plan/ARCHITECTURE.md`](./plan/ARCHITECTURE.md)  
- Problem statement: [`ps.md`](./ps.md)  
- Handoff: [`HANDOFF.md`](./HANDOFF.md)  
