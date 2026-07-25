# SENTINEL — ETERNAL FINAL PLAN (Win Hard Track)

> **Law:** Evidence or it did not happen (FM-09).  
> **Mindset:** Current winning score ≈ **15%**. Scaffold + seed ≠ product.  
> **Goal:** Maximize to **100%** against METIS Hard rubric — real live system, not vibe-coding theater.  
> **Sources of law:** `ps.md` · `PROBLEM_STATEMENT.md` · `docs/SCOPE_GUARD.md` · ADAPTOID-LITE · `PRODUCT.md` · `DESIGN.md` · code audits (backend + frontend, 2026-07-25).  
> **Anti-pattern ban:** HANDOFF saying COMPLETE, SUBMISSION.md claiming “functionally complete,” green pytest without browser+live AI+security proof.

---

## 0. Intent lock (do not re-litigate)

| Decision | Value |
|----------|--------|
| Track | METIS Hard — SENTINEL AI-Native Eng Ops |
| Outcome | **Win lane** — competitor should not look like a serious alternative |
| Deploy | Keep Render API + Vercel FE; harden until cold-start and CORS never shame us |
| AI | **Live provider mandatory in production** (OpenRouter/Claude/Gemini). Mock **only** in tests |
| Scope | All **10 FRs** production-grade + all **5 brownie** features **honest** (or label “local-only” if cloud cannot run Docker) |
| Process | Adaptoid dual-tier: orchestrator plans/reviews; workers implement one task with write-sets |
| Demo path | Sacred, end-to-end, browser-proven, unfakeable |

**What “100%” means here:**  
Every rubric criterion has **live proof** a hostile judge can reproduce in &lt;10 minutes without your narration.

---

## 1. Honest baseline (why ~15%, not “done”)

### Rubric-weighted reality (hostile judge)

| Criterion | Weight | Today (honest) | Why it is not winning |
|----------|--------|----------------|------------------------|
| System Design & Scalability | 25% | ~25–35% of weight | Modular FastAPI exists; but `create_all` not migrations, stub models, single-process hub, orphaned prober, no workers, dual role taxonomies |
| Real-Time Features & Reliability | 20% | ~20–30% | SSE hub exists; **incidents do not publish**; “connected” light only; Redis multi-worker incomplete; WS open publish |
| AI Integration & Automation | 20% | ~15–30% | Provider abstraction real; **default mock**; pseudo-RAG (concat prompt); no evals; RCA soft-dummy; voice mock |
| Security & Access Control | 15% | ~10–20% | JWT + team filter on many routes; **RBAC dead**; unauth health + voice; demo password in API; optional webhook verify |
| UI/UX & Product Quality | 10% | ~20–40% | Login direction good; dashboard silent zeros; war room scroll hell; light-theme leaks; no escalate |
| Deployment & DevOps | 10% | ~40–50% | Live URLs exist; compose+prometheus partially; cold start; no CI gate on sacred path; docs overclaim |

**Blended win-score: ~15–25%.**  
Having 185 tests and two URLs is **table stakes**, not excellence. Tests mock AI/RBAC and **do not prove** live product.

### Ten functional requirements — truth table

| # | FR | Status | Gap to “real” |
|---|----|--------|----------------|
| 1 | Team auth + RBAC | Auth **partial**; RBAC **fake** | Wire `require_permission` on every mutating route; align `admin|owner` names |
| 2 | Realtime incident dashboard | Dashboard **static** | Incident.* events + FE subscription + honest loading/errors |
| 3 | Log + alert monitoring | DB real; UI thin | Fail-loud resolve; live alert feed; log level filters |
| 4 | AI summary + RCA | Endpoints real; quality optional | Force live provider; separate summary/RCA panels; no mock in prod |
| 5 | GitHub/GitLab deploys | Webhooks real if secret set | Require secrets; GitLab as first-class; UI not empty-on-error |
| 6 | Service health + uptime | Rows exist; **unauth** | Auth + team scope; run prober; charts |
| 7 | Per-incident comms | Real + SSE | Design tokens; multi-user demo optional |
| 8 | Timeline provenance | Real | Always write on every lifecycle change; show source/actor/ts |
| 9 | Tasks + escalate + SLA | Tasks + countdown only | **Escalate API+UI**; SLA worker/breach events; create-task UI |
| 10 | Analytics trends | Aggregations real | No hang; metric consistency with dashboard; deploy stability metric |

### Five brownie features — truth table

| Feature | Status | To count as excellence |
|---------|--------|------------------------|
| Conversational AI chat | Pseudo-RAG | Citations, team isolation tests, live model, streaming preferred |
| Docker/K8s monitoring | Real clients, empty on PaaS | Compose demo path + UI honesty; optional local k3s doc |
| Auto postmortem | Endpoint exists | Durable artifact, quality, download, not mock |
| Voice-to-ticket | **Unauth + mock STT** | Auth, team from JWT, real Whisper or explicit “demo audio” mode |
| Predictive anomaly | Synthetic/random | Real feature scores from logs/metrics or label “research demo” |

---

## 2. Non-negotiable laws (every phase)

1. **Evidence law:** Done = command output + browser screenshot/trace + live URL probe. Chat claims do not count.  
2. **No greenwash:** Never mark FR complete if only tests pass on mocks.  
3. **Sacred path first:** Login → dashboard → SEV1 war room → AI live → assign/escalate/SLA → timeline → monitoring → deployments → analytics.  
4. **Fail loud (FM-11):** No silent `catch → []` that paints “empty healthy.”  
5. **Disjoint write-sets (FM-13):** Parallel agents never touch same files.  
6. **Secrets (FM-07):** No keys in git; seed secret production-only; rotate if leaked.  
7. **Blast radius:** r0/r1 auto; r2 migrations confirm; r3 push/deploy confirm.  
8. **Skills on task:** Load the skill that owns the work (table below).  
9. **Hostile re-score after each phase** against rubric weights.

---

## 3. Skills map (use deliberately, not as decoration)

| Work | Skills to load |
|------|----------------|
| Plan / domain language | `domain-modeling`, writing-plans |
| Backend architecture | `improve-codebase-architecture`, `supabase-postgres-best-practices` |
| Security P0 | `security-review`, `verification-before-completion` |
| UI war room / design | `impeccable` (Operate), `design-taste-frontend`, `high-end-visual-design`, `ui-ux-pro-max`, `frontend-design` |
| Live browser proof | `webapp-testing`, `playwright-cli`, `verification-before-completion` |
| Realtime bugs | `systematic-debugging` |
| AI features | `tdd` / `test-driven-development`, `qa` |
| Deploy FE | `deploy-to-vercel` |
| Pre-merge | `code-review`, `requesting-code-review` |
| Process | ADAPTOID dual-tier, `find-skills` only if a gap remains |

**Rule:** Skills install ≠ delivery. Delivery = phase acceptance green.

---

## 4. Target end-state (what “nobody comes close” looks like)

### Product experience (judge, 8 minutes)
1. Incognito → `sentinel-hers.vercel.app`  
2. **Enter live SEV1 demo** → lands on war room for open SEV1 (deep link `/incidents/{id}`)  
3. Sees **live AI paragraph** (not `[mock-ai]`), RCA hypotheses **beside** summary  
4. Assign to me · **Escalate** · Advance status (no 422) · SLA mono countdown  
5. Timeline rows with provenance; tasks checkable; comms message appears live  
6. Chat answers with **cited logs**  
7. Monitoring: alerts resolve with feedback; health services for **this team** only  
8. Deployments table non-empty; analytics MTTR matches dashboard  
9. StatusBar shows connected **and** list updates on another tab’s event  

### Engineering excellence
- RBAC enforced on every mutating route  
- No unauth cross-tenant write/read  
- Incident lifecycle emits SSE events  
- Production `AI_PROVIDER` ≠ mock; missing key → **hard fail at boot** in production  
- Alembic (or single migration script applied on release)  
- CI: pytest + FE typecheck + Playwright sacred-path smoke  
- WRITEUP honest about tradeoffs (no “functionally complete” fiction)

---

## 5. Phase plan (eternal ladder) — clean cut end-to-end

Execute **in order**. A phase is closed only when its **Acceptance gate** is green with pasted evidence.  
Parallelism only inside a phase when write-sets are disjoint.

---

### PHASE 0 — Truth reset (½ day) · **Score unlock: honesty**

**Purpose:** Stop lying to ourselves. Reset docs and scoreboard.

| Step | Action | Owner | Evidence |
|------|--------|-------|----------|
| 0.1 | Rewrite `HANDOFF.md` as **NOT DONE** with rubric table (~15%) | Orchestrator | File content |
| 0.2 | Strike false claims in `docs/SUBMISSION.md` / README badges that say complete | Worker | Diff |
| 0.3 | Create `docs/SCOREBOARD.md` with FR×rubric cells: RED/YELLOW/GREEN only via evidence links | Orchestrator | File |
| 0.4 | Inventory Render env: `AI_PROVIDER`, keys, `CORS_ORIGINS`, `SEED_SECRET`, JWT secrets, webhook secrets | Human + orchestrator | Checklist filled |
| 0.5 | Baseline probes: healthz, login, demo-status, AI summary body, SSE connected, Playwright login | Worker | Log paste |

**Acceptance:** SCOREBOARD exists; no doc claims 100%; baseline log stored in `work/reports/final/P0-baseline.md`.

**Skills:** `verification-before-completion`.

---

### PHASE 1 — Security fortress (1–2 days) · **+Security toward 100% of 15%**

**P0 bugs that get you kicked (fix first):**

| ID | Fix | Files (approx write-set) |
|----|-----|---------------------------|
| S1 | Auth + team from JWT on **voice**; remove client `team_id` injection | `src/backend/voice/**`, tests |
| S2 | Auth + **team filter** on health list; auth on register_service | `src/backend/health/**`, tests |
| S3 | Align roles: one vocabulary (`admin`↔`owner` map or rename); wire `require_permission` on mutations | `rbac/**`, `auth/**`, all mutating routes |
| S4 | Webhook signature **required** in production if env set; reject when secret missing in prod | `integrations/github/routes.py` |
| S5 | Seed: production requires strong `SEED_SECRET`; demo-status **must not** return password in production mode | `seed/**` |
| S6 | Tasks: verify `incident_id` belongs to caller team | `tasks/**` |
| S7 | WS: stop arbitrary client event rebroadcast (server-validated types only) | `realtime/router.py` |
| S8 | Production JWT secrets: refuse default `change-me` at boot | `auth/service.py`, `api/startup.py` |

**Tests (must be on real routers, not toy apps):**
- Viewer cannot create/update/assign  
- Cross-tenant health/voice/task denied  
- Unauth → 401 on former public holes  

**Acceptance:**
```bash
pytest tests/integration/test_rbac.py tests/integration/test_security_tenancy.py -q  # new file
# Live: curl unauth voice/health → 401; login viewer → 403 on POST incident
```
Security-review skill run; findings triaged or fixed.

**Skills:** `security-review`, `tdd`, `verification-before-completion`.

**Score target after P1:** Security column ≈ **80–100% of its 15%**.

---

### PHASE 2 — Live AI that cannot fake (1 day) · **+AI toward 100% of 20%**

| Step | Action |
|------|--------|
| A1 | Production boot: if `ENV=production` and `AI_PROVIDER=mock` or missing keys → **fail startup** (or explicit `ALLOW_MOCK_AI=1` only for emergency) |
| A2 | Confirm Render has OpenRouter/Claude/Gemini key; set provider |
| A3 | Summary + RCA + postmortem + chat must return non-mock text on live SEV1 |
| A4 | Split UI panels: **Summary** and **RCA** never overwrite each other |
| A5 | Chat: return citations; enforce team isolation (existing tests + live) |
| A6 | Optional: stream tokens for chat (SSE) for wow factor |
| A7 | Postmortem: persist last markdown on incident; download works |

**Acceptance:**
```bash
# Live, with JWT:
curl .../api/ai/incidents/{sev1}/summary | jq -r .summary | grep -vi mock-ai
# Browser: summary paragraph + RCA list both visible
playwright sacred-path AI steps green
```

**Skills:** `tdd`, `qa`, `webapp-testing`, `verification-before-completion`.

**Score target after P2:** AI column ≈ **85–100% of its 20%** (true RAG embeddings optional stretch).

---

### PHASE 3 — Realtime that moves the UI (1–2 days) · **+Realtime toward 100% of 20%**

| Step | Action |
|------|--------|
| R1 | Publish hub events on: incident.create/update/assign/status, task.*, sla.breach, health.change |
| R2 | Fix FE `lib/realtime.ts` for **named** SSE events (match StatusBar pattern) |
| R3 | Dashboard + incidents list subscribe; patch state on events (no full reload only) |
| R4 | War room timeline appends on timeline events live |
| R5 | SLA breach flash when remaining &lt; 0 |
| R6 | Redis pub/sub verified with two processes **or** document single-instance + disable fake multi-worker claims |
| R7 | Connect ticket (short-lived) instead of long JWT in query string (security bonus) |

**Acceptance:**
- Two browser tabs: assign in A → list updates in B without refresh  
- `curl -N` SSE shows `incident.updated` after PATCH  
- Perf test still green  

**Skills:** `systematic-debugging`, `webapp-testing`, `playwright-cli`.

---

### PHASE 4 — Core FR productization (2–3 days) · **+System design + product**

Parallel tracks with **disjoint write-sets**:

#### Track B — Incidents / SLA / tasks (backend+FE war room)
| Step | Action |
|------|--------|
| I1 | `POST /api/incidents/{id}/escalate` (or first-class field + policy) + timeline event |
| I2 | FE Escalate button + reason optional |
| I3 | SLA: background check or on-read breach timeline event once; notify hub |
| I4 | Create task UI in war room |
| I5 | Deep link `/incidents/[id]` + dashboard links with id |
| I6 | War room layout per DESIGN: list | command center; Summary‖RCA; Timeline‖Tasks; Comms; Chat; mobile tabs |

#### Track C — Monitoring / health
| Step | Action |
|------|--------|
| M1 | Start health prober in app lifespan (or dedicated worker) |
| M2 | Uptime visualization (sparkline or % bars) team-scoped |
| M3 | Alerts resolve fail-loud; live alert list optional via SSE |
| M4 | Log search level filters |

#### Track D — Deployments / VCS
| Step | Action |
|------|--------|
| V1 | Require webhook secrets in prod |
| V2 | FE use `api.ts`; show errors not silent empty |
| V3 | Fix light-mode chips (SHA) fully |
| V4 | Deploy stability metric on analytics (success rate over time) |

#### Track E — Analytics consistency
| Step | Action |
|------|--------|
| N1 | Dashboard uses same summary endpoint fields as analytics (FM-05) |
| N2 | Loading/error/retry everywhere (no silent zeros) |
| N3 | Anomaly: either real features from recent log rates **or** badge “synthetic research demo” |

**Acceptance:** Every FR row in SCOREBOARD moves to GREEN with browser evidence.

**Skills:** `impeccable`, `ui-ux-pro-max`, `design-taste-frontend`, `vercel-react-best-practices`, `domain-modeling`.

---

### PHASE 5 — Brownie excellence (1–2 days) · **rubric differentiators**

| Feature | Minimum excellence bar |
|---------|------------------------|
| Chat | Live model + citations + isolation test + UI usable without CSS overlap |
| Containers | Local compose shows containers; cloud shows honest unavailable + reason |
| Postmortem | Quality structure (timeline, impact, RCA, actions); download MD |
| Voice | Auth required; optional real Whisper key; else labeled **sample mode** with fixed audio |
| Anomaly | Document method; show scores tied to services in seed; no random flicker without seed |

**Acceptance:** Each brownie has a subsection in WRITEUP + browser or API proof.

---

### PHASE 6 — System design polish (1–2 days) · **+25% design weight**

| Step | Action |
|------|--------|
| D1 | Alembic (or `deployment/render/release.sh` applies SQL schema idempotently) — one truth |
| D2 | Kill or flesh out `shared_models.py` “stub” language; real FKs |
| D3 | Indexes on `team_id`, incident foreign keys, log timestamps (Supabase skill) |
| D4 | Architecture diagram in WRITEUP matches code |
| D5 | Prometheus metrics that matter: request latency, incident counts, AI latency |
| D6 | Rate limit auth login; CORS exact origins only |
| D7 | Optional: Redis-backed SLA/session for scale story |

**Skills:** `improve-codebase-architecture`, `supabase-postgres-best-practices`, `domain-modeling`.

---

### PHASE 7 — UI domination (1–2 days) · **+10% UI weight to max**

Treat as **Operate mode** (impeccable): density, scanability, mission console.

| Step | Action |
|------|--------|
| U1 | Register page radar-aligned |
| U2 | Dashboard: skeletons, errors, SEV1 hero, deep links |
| U3 | War room wireframe + mobile tabs |
| U4 | Kill all light-theme leaks (`bg-gray-100`, `bg-blue-50`, etc.) |
| U5 | SEV colors per DESIGN (SEV2 warn not destructive pulse) |
| U6 | a11y: keyboard cards, 36px targets, focus visible |
| U7 | Empty states with next action copy |

**Acceptance:** Playwright desktop + mobile screenshots; design critique score ≥8/10 via impeccable critique.

**Skills:** `impeccable`, `high-end-visual-design`, `web-design-guidelines`, `redesign-existing-projects`.

---

### PHASE 8 — Automated proof + DevOps (1 day) · **+10% deploy weight**

| Step | Action |
|------|--------|
| C1 | GitHub Actions: pytest + `tsc` + Playwright sacred path against preview/staging or mockable contract |
| C2 | Playwright suite: login, nav, SEV1 AI, assign, analytics not Loading |
| C3 | `scripts/verify_live.sh`: healthz, CORS, login, demo-status, AI non-mock, SSE |
| C4 | Render health check + preDeploy; Vercel root `src/frontend` documented |
| C5 | Cold-start UX: FE shows “API waking” not blank error |
| C6 | 2-min Loom (optional but high impact): no narration lies |

**Acceptance:** CI green on main; `verify_live.sh` exit 0 against production.

**Skills:** `playwright-cli`, `deploy-to-vercel`, `verification-before-completion`.

---

### PHASE 9 — Final SHIP audit (½ day) · **freeze**

| Step | Action |
|------|--------|
| Z1 | Hostile re-score SCOREBOARD; every cell GREEN or explicitly YELLOW with reason |
| Z2 | security-review full pass |
| Z3 | code-review on delta since P0 |
| Z4 | Rewrite WRITEUP honestly (challenges, tradeoffs, more time) |
| Z5 | README setup + judge path only (no false “complete”) |
| Z6 | Replace HANDOFF with cold-resume truth |
| Z7 | Tag release `v1.0-metis-hard` only if Z1–Z6 green |

**Definition of 100% (gate):**

```
[ ] All 10 FRs GREEN with live browser evidence
[ ] Security P0 closed; RBAC on mutations proven by tests + curl
[ ] Live AI non-mock on production SEV1
[ ] Realtime updates second browser tab
[ ] Sacred path Playwright green on production URL
[ ] pytest green; CI green
[ ] WRITEUP + README honest
[ ] Hostile validator walkthrough <10 min without help
```

If any box open → **not 100%**. Ship percentage = weighted sum of green cells only.

---

## 6. Execution model (how work actually gets done)

### Dual-tier
- **Orchestrator (this brain):** plan, dispatch task files, re-run acceptance, merge, SCOREBOARD, HANDOFF. **Does not** bulk-implement all labor when workers available.  
- **Workers:** one task file → one write-set → report with command output.

### Task file template (every task)
```
Goal / FR id / Rubric weight
Context (read-set)
Write-set (exact paths)
Forbid-set
Acceptance commands (copy-paste)
Skills to load
Demo-path impact (must not break)
```

### Suggested parallel waves after P1
```
P2 AI (serial — shared provider)
P3 Realtime (serial after incident publish point)
P4 tracks B ‖ C ‖ D ‖ E (parallel if write-sets disjoint)
P5 brownies (voice after S1)
P6 design polish
P7 UI (after API stable)
P8 CI
P9 freeze
```

### Human-only steps (you)
- Render dashboard: set AI keys, webhook secrets, strong JWT secrets, SEED_SECRET  
- Confirm Vercel `NEXT_PUBLIC_API_BASE_URL`  
- Record Loom  
- Final push approval (r3)

---

## 7. Sacred path — gold acceptance script

Automate as `scripts/verify_sacred_path.(sh|mjs)`:

1. `GET /healthz` → 200  
2. `GET /api/demo-status` → ready, open_sev1 ≥ 1, **no password leak in prod**  
3. `POST /auth/login` demo → JWT + nested role  
4. Unauth `POST /api/voice/incidents` → **401**  
5. Unauth `GET /api/health/services/` → **401**  
6. With token: list incidents → open SEV1 id  
7. AI summary → body length &gt; 80 and not matching `mock-ai`  
8. RCA → ≥1 hypothesis  
9. Timeline, tasks, SLA, channel messages all 200  
10. SSE: `event: connected` within 5s  
11. Playwright: login → full nav → war room text → analytics not stuck Loading  
12. Assign + escalate + status advance → 2xx  

**Any fail → phase not closed.**

---

## 8. What we will NOT do (scope guard)

- Billing, SSO/SAML, multi-region HA theater  
- Fake KPI generators to hide empty DB  
- Claiming Docker/K8s “live on Render” when socket missing  
- Claiming RBAC while routes unrestricted  
- Installing more skills instead of fixing P0s  
- Another “COMPLETE” HANDOFF before Phase 9 gate  

---

## 9. Risk register

| Risk | Mitigation |
|------|------------|
| Render cold start kills demo | Keep-alive cron or paid instance; FE “waking” state |
| AI key quota / cost | Cache summaries; short prompts; OpenRouter budget |
| Parallel agent collisions | Strict write-sets; orchestrator merge only |
| Test green / prod red | Live verify script required in P8/P9 |
| Over-scope brownie | Ship honest labels over broken magic |
| Time pressure | Order is Security → AI → Realtime → War room UI → rest |

---

## 10. Immediate next actions (start of execution, not “done”)

When you approve this plan and say **go / execute**:

1. **P0** truth reset (SCOREBOARD + kill false complete claims)  
2. **P1** security P0 (voice, health, RBAC wire) — highest kick-out risk  
3. **P2** live AI boot gate + dual panels  
4. Then P3–P9 as above  

**Do not** start new features before P1+P2. A beautiful UI on unauth voice and mock AI is still a 15% project.

---

## 11. Score ambition map

| After phase | Approx win-score (hostile) |
|-------------|----------------------------|
| Now | ~15% |
| P0 honesty | Still ~15% (truth only) |
| P1 security | ~30–40% |
| P2 live AI | ~45–55% |
| P3 realtime | ~60–70% |
| P4 FR productization | ~80–88% |
| P5–P7 polish | ~90–96% |
| P8–P9 proof + freeze | **100% only if all gates green** |

---

## 12. Bottom line

You have a **real codebase skeleton** with many modules and tests — that is **inventory**, not victory.  
Winning Hard track means a judge experiences a **coherent, secure, live-AI, live-updating ops console** and cannot find the holes this audit found in 10 minutes.

**This plan is the only path:** truth → security → live AI → realtime → full FR product → brownies honest → architecture → UI domination → automated proof → freeze.

No phase is complete without evidence.  
No claim of 100% until Phase 9 checklist is fully checked.
