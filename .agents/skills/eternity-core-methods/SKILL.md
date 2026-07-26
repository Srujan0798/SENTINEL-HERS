# SKILL — ETERNITY CORE METHODS

> **Purpose:** Capture every technique, flow, and architectural pattern used during SENTINEL-HERS so any agent can reapply them in future projects.
> **Scope:** Phase-close methodology, UI construction, backend hardening, realtime wiring, deployment automation.
> **Usage:** Load via `skill eternity-core-methods` before starting any project close-out.

---

## 1. Dual-Tier Orchestration (Brain + Workers)

| Role | Reads | Writes | Responsibility |
|---|---|---|---|
| **Orchestrator (this Brain)** | HANDOFF.md, EXECUTION.md, plan YAML, reports | Handoff files, task files, merges, scoreboard | Never writes feature code. Reads state, dispatches tasks, reviews, accepts. |
| **Workers (external AI agents)** | One self-contained task file | Code in `src/`, reports in `work/reports/<wave>/` | Stateless. Receive 1 task, execute, report. |

**Handoff contract:** `work/<wave>/<task>.md` → `work/reports/<wave>/<task>.report.md`

**Apply when:** Any project with >2 agents. Prevents context collision, parallel-safe writes, traceable provenance.

---

## 2. Phase-Close Execution (0–9)

Divide project close-out into ordered phases. Each phase produces evidence. Never skip phases.

| Phase | What |
|---|---|
| **0 — Truth Reset** | Audit scoreboard, strike fake claims, rewrite README/HANDOFF honestly |
| **1 — Security** | Auth on every route, RBAC, tenancy isolation, webhook sigs, rate limit, JWT checks |
| **2 — Live AI** | Production AI provider check, mock guard (ALLOW_MOCK_AI), warm-up test |
| **3 — Realtime** | SSE lifecycle events, WS ACL, hub with Redis-fallback |
| **4 — Core FRs** | Escalate, create-task, AI/RCA split, deep link, health prober, DB indexes, CI, live-verify |
| **5 — Brownies** | Streaming AI chat, RAG citations, postmortem download, voice-to-ticket, anomaly scores |
| **6 — System Design** | Alembic migrations, architecture diagram, Prometheus metrics, rate limiting |
| **7 — UI Polish** | Login a11y, skeletons, empty states, keyboard nav, dark theme, mobile, SSE FE subscription, cold-start overlay |
| **8 — Proof Automation** | verify_live.sh, keep_alive.sh, Playwright e2e, GitHub Actions CI (5 jobs) |
| **9 — Freeze** | Honest WRITEUP, SUBMISSION, SCOREBOARD with per-criterion evidence |

**Law:** No phase is COMPLETE until its successor phase shows green evidence. Phase 9 is the only terminal phase.

---

## 3. FM Guardrails (14 Failure Modes)

| FM | Name | Enforcement |
|---|---|---|
| 01 | State drift | HANDOFF.md updated every session |
| 02 | Stale process | Reload HANDOFF + EXECUTION.md before acting |
| 03 | Broken refs | Grep imports after any rename |
| 04 | Context bloat | Hard line at 300 lines of plan; worker tasks are self-contained |
| 05 | Metric inconsistency | verify_live.sh checks live metrics match code |
| 06 | Config revert | Render/Vercel env vars checked by probe (`scripts/check_env.sh`) |
| 07 | Embarrassing artifacts | No secrets in code, no debug logs in prod, no `console.log` in FE build |
| 08 | Scope creep | SCOPE_GUARD.md — IN vs OUT explicitly |
| 09 | False status | Evidence required for every claim. No "done" without `verify_live.sh` PASS |
| 10 | Flaky tests | CI must pass 3 consecutive runs before merge |
| 11 | Silent failures | Incident tooling fails loud — no try/catch swallowing |
| 12 | Stale derived docs | `docs/SCOREBOARD.md` regenerated after each phase |
| 13 | Parallel collisions | Disjoint write-sets per worker — no two agents touch same file in same wave |
| 14 | Lost handoff | Every session ends with HANDOFF.md update; orchestration state never in agent memory |

---

## 4. Evidence-First Development (FM-09 Compliance)

**Rule:** You cannot claim anything works without a live probe.

**Flow:**
1. Write feature
2. Write probe (`curl`, `verify_live.sh`, test)
3. Run probe → capture output
4. Assert evidence in SCOREBOARD.md

**Evidence types:**
- `curl -sS <endpoint>` output (JSON, status code)
- `npm run build` exit code + output
- `npx tsc --noEmit` exit code
- `pytest -x` output count
- Playwright trace
- verify_live.sh PASS

**Anti-pattern:** "I checked and it works" without showing output.

---

## 5. Verification-Before-Completion (Gate)

Every task must pass through this gate before marked done:

```bash
# 1. TypeScript check
npx tsc --noEmit

# 2. Lint (ESLint with --quiet)
npm run lint -- --quiet  # or next build which runs lint

# 3. Build
npm run build

# 4. Backend tests (if backend changed)
pytest -x -q

# 5. Live probe (if endpoints changed)
bash scripts/verify_live.sh

# 6. CI check (if committed)
gh run list --limit 1 --json conclusion --jq '.[0].conclusion'
```

All 6 must pass. If any fails, fix first, then re-run all 6.

---

## 6. Mock-AI Layer with Production Guard

```
AI Provider → OpenRouter (prod) / Mock (dev)
```

**Rules:**
- Production (`ENV=production`) blocks `AI_PROVIDER=mock` unless `ALLOW_MOCK_AI=1` is set
- Startup check in `api/main.py` fails loud if AI misconfigured
- Mock provider returns realistic fake data (not empty strings)
- Each route has fallback path: if AI call fails, return helpful error, not 500

**Pattern:**
```python
# api/main.py
if ENV == "production" and AI_PROVIDER == "mock" and not ALLOW_MOCK_AI:
    raise RuntimeError("Production blocks mock AI")
```

---

## 7. SSE + WebSocket Realtime Wiring

| Component | Tech | Purpose |
|---|---|---|
| Hub | `realtime/hub.py` | Redis-backed, in-memory fallback, typed events |
| API events | SSE via `StreamingResponse` | incident.create, update, assign, escalate; task.create, update; sla.breach; health.change |
| WS (optional) | WebSocket in `realtime/router.py` | channel:message, typing, pong (ACL restricted) |
| FE subscription | `useRealtimeEvents` hook | Auto-reconnect, token auth, event dispatch to Zustand |

**SSE endpoint:** `GET /api/realtime/events?token=<jwt>`

**FE hook pattern:**
```typescript
const { events, connected } = useRealtimeEvents();
// events[] drives live UI updates
```

---

## 8. RBAC Permission System

| Role | Scope |
|---|---|
| `ADMIN` | Everything |
| `OWNER` | Everything in team |
| `RESPONDER` | incidents:create/update, tasks:create, voice:create |
| `VIEWER` | Read-only (incidents:read, tasks:read) |

**Pattern:**
```python
@router.post("/{id}/escalate")
async def escalate_incident(
    id: str,
    body: EscalateRequest,
    current_user: User = Depends(require_permission("incidents:escalate")),
):
    ...
```

Every mutating endpoint guarded. Read endpoints check tenancy (team_id from JWT matches resource team_id).

---

## 9. UI Construction Pattern (Used Across All Pages)

### 9a. Skeleton Loading
```tsx
{loading && Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-24 w-full" />)}
```

### 9b. Empty States
```tsx
{!loading && items.length === 0 && (
  <div className="flex flex-col items-center gap-2 py-12 text-center">
    <Inbox className="h-12 w-12 text-muted-foreground" />
    <h3 className="font-semibold">No incidents</h3>
    <p className="text-sm text-muted-foreground">Your team hasn't had any incidents yet.</p>
    <Button onClick={handleCreate}>Create your first incident</Button>
  </div>
)}
```

### 9c. Mobile Stack
- Use `flex-col` on mobile, `flex-row lg:flex-row` on desktop
- Side panels become bottom sheets or below-fold sections on mobile
- Table → card list on small screens
- 44px minimum touch targets on all interactive elements

### 9d. Keyboard A11y
```tsx
<div
  role="button"
  tabIndex={0}
  onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") handleAction(); }}
  onClick={handleAction}
>
```

### 9e. SSE Live Subscription
```tsx
const { events, connected } = useRealtimeEvents();
// Filter events by type, update local state
```

### 9f. Focus Management
```tsx
useEffect(() => {
  dialogRef.current?.focus();
}, [open]);
```

### 9g. SEV Color Mapping
```tsx
const severityColor: Record<string, string> = {
  SEV1: "destructive",
  SEV2: "warning",
  SEV3: "info",
  SEV4: "secondary",
};
```

### 9h. Mobile Safe Area
```css
/* globals.css */
body {
  padding-top: env(safe-area-inset-top);
  padding-bottom: env(safe-area-inset-bottom);
  padding-left: env(safe-area-inset-left);
  padding-right: env(safe-area-inset-right);
}
```

---

## 10. UI Polish Checklist (For Every Page)

- [ ] Skeleton loading for async data
- [ ] Empty state with illustration + action CTA
- [ ] Mobile stack (column on mobile, row on desktop)
- [ ] 44px touch targets
- [ ] Keyboard navigation (Enter/Space on interactive elements)
- [ ] Focus ring visible
- [ ] SEV colors applied (SEV1=destructive, SEV2=warning, SEV3=info, SEV4=secondary)
- [ ] Dark theme (no hardcoded bg-gray-100/bg-blue-50/bg-red-500/bg-green-500)
- [ ] SSE live subscription (if applicable)
- [ ] Deep link support (id in URL → auto-navigate)
- [ ] Loading/error/empty/data states (all 4)
- [ ] No horizontal scroll on mobile
- [ ] Safe area padding for iOS notch

---

## 11. CI Pipeline Design

```
pytest → tsc --noEmit → npm run build → Playwright e2e → verify_live.sh
```
5 jobs. All must green. Fastest jobs first.

Playwright config:
- `baseURL` set to deployed FE
- Sacred path test covers demo login → dashboard → incident → summary → assign → escalate → SLA
- Trace + screenshot on failure via `--trace on --retries 1`

---

## 12. Live Verification Script Pattern

```bash
#!/usr/bin/env bash
# 13 checks: healthz, demo-status, login, unauth deny, auth core, FE login page
PASS=0; FAIL=0
check() { ... }
# Each check is a curl + assertion
# Exit 0 if all pass, 1 if any fail
```

**Rule:** A feature is only done when `verify_live.sh` includes a check for it and passes.

---

## 13. Cold-Start Architecture (WakingOverlay)

```tsx
function WakingOverlay({ apiBase }: { apiBase: string }) {
  // Pings /api/health every 3s
  // Shows "Waking up the engine..." with animated dots
  // Auto-dismisses when health OK
  // Manual dismiss button after 8s for impatient users
}
```

This pattern applies to any serverless backend with cold starts (Render, Railway, Fly.io).

---

## 14. Streaming AI Chat Pattern

```
FE POST /api/ai/chat/stream  →  Backend SSE stream  →  FE reads via ReadableStream
```

**Backend:**
```python
async def generate():
    async for chunk in provider.stream_complete(messages, model):
        yield f"data: {json.dumps(chunk)}\n\n"
return StreamingResponse(generate(), media_type="text/event-stream")
```

**FE:**
```typescript
const response = await fetch("/api/ai/chat/stream", { method: "POST", body, headers });
const reader = response.body!.getReader();
const decoder = new TextDecoder();
while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  // Parse SSE chunks, append to display
}
```

---

## 15. Voice-to-Ticket Flow

```
Browser mic → MediaRecorder → Blob → POST /api/voice/incidents → Whisper/stt → AI parse → Incident created
```

**FE:**
```tsx
const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
const mediaRecorder = new MediaRecorder(stream, { mimeType: "audio/webm;codecs=opus" });
// Collect chunks ondataavailable, upload onstop
```

**Backend:**
```python
file = UploadFile(...)
audio_bytes = await file.read()
# Transcribe via whisper/stt
# Parse transcript via AI into incident fields
# Create incident
```

---

## 16. Escalation + SLA Pattern

```
POST /api/incidents/{id}/escalate  →  Updates severity (SEV3→SEV2)  →  Publishes SSE event  →  SLA timer starts
```

**SLA timers:**
- SEV1: 15min acknowledge, 60min resolve
- SEV2: 30min acknowledge, 240min resolve
- SEV3: 60min acknowledge, 480min resolve
- SEV4: no SLA

**Escalate flow:** FE opens dialog → user picks reason → POST → SSE event → timeline entry created → SLA recalcs

---

## 17. Postmortem Generation + Download

```
POST /api/incidents/{id}/postmortem  →  AI generates markdown  →  Returns as downloadable .md file
```

**FE:**
```tsx
const response = await fetch(`/api/incidents/${id}/postmortem`, { method: "POST" });
const blob = await response.blob();
const url = URL.createObjectURL(blob);
const a = document.createElement("a");
a.href = url;
a.download = `postmortem-${id}.md`;
a.click();
```

---

## 18. Timestamp-Based Feeds (Provenance)

Every event in the timeline stores:
- `event_type` (string enum)
- `actor_id` (who did it)
- `target_id` (what was affected)
- `timestamp` (ISO 8601)
- `metadata` (JSON blob with context)

**Display pattern:**
```tsx
{events.map((e) => (
  <TimelineItem key={e.id}>
    <div className="text-xs text-muted-foreground">{formatTimeAgo(e.timestamp)}</div>
    <div className="text-sm">{e.actor_name} {actionLabel(e.event_type)}</div>
    {e.metadata?.reason && <div className="text-xs italic">"{e.metadata.reason}"</div>}
  </TimelineItem>
))}
```

---

## 19. Deep Link Pattern

```tsx
// In navigation
router.push(`/incidents?id=${incident.id}`);

// In target page
const searchParams = useSearchParams();
const incidentId = searchParams.get("id");

useEffect(() => {
  if (incidentId) fetchIncident(incidentId);
}, [incidentId]);
```

---

## 20. Config Validation at Startup

```python
# api/main.py lifespan
async def startup():
    # Check JWT secrets
    if not JWT_SECRET or not JWT_REFRESH_SECRET:
        raise RuntimeError("JWT secrets not configured")
    # Check AI provider
    if ENV == "production" and AI_PROVIDER == "mock" and not ALLOW_MOCK_AI:
        raise RuntimeError("Production blocks mock AI")
    # Check DB connection
    await check_db()
    # Run migrations
    await run_migrations()
    # Auto-seed demo data
    await seed_demo()
    # Start health prober
    asyncio.create_task(health_prober_loop())
```

Fail loud. Never silently degrade.

---

## 21. Preventative: The "ESLint Build Fail" Trap

When you define helper functions at module level in a React component and reference them in a `useCallback`:

**Problem:** ESLint `react-hooks/exhaustive-deps` warns about missing deps AND if you add them, they change every render.

**Solution:**
1. Define helpers **before** the `useCallback` that uses them
2. Wrap helpers in `useCallback` themselves: `const fn = useCallback(...)`
3. Add the helper to the dependent `useCallback`'s dependency array
4. Or, move the helper **inside** the `useCallback` if only used there

**Check:** `npx tsc --noEmit` passes but `npm run build` fails on ESLint → this is the trap.

---

## 22. Directory Layout for Phase-Close Projects

```
project/
├── AGENTS.md / KIMI.md     # Boot context (this should load ETERNITY skills)
├── HANDOFF.md               # Current state, next moves, score
├── docs/
│   ├── SCOREBOARD.md        # Per-criterion evidence (the truth)
│   ├── WRITEUP.md           # Honest technical writeup
│   ├── SUBMISSION.md        # For judges (live URLs but honest)
│   ├── SCOPE_GUARD.md       # IN / OUT explicitly
│   ├── ARCHITECTURE.md      # System diagram
│   └── PRD.md               # Product requirements
├── plan/
│   └── EXECUTION.md         # Phase DAG, wave plan
├── work/
│   ├── <wave>/<task>.md     # Task files for workers
│   └── reports/<wave>/      # Worker reports
├── scripts/
│   ├── verify_live.sh       # 13+ live checks
│   └── keep_alive.sh        # Warm-up cron
├── src/
│   ├── backend/             # Python/FastAPI
│   ├── frontend/            # Next.js app
│   └── docs/                # Architecture diagrams
└── .github/workflows/ci.yml # CI pipeline
```

---

## 23. The "Sacred Path" (Demo Flow that Must Never Break)

```
Login (demo@sentinel.io / Sentinel2026!) → Dashboard (see incidents + stats) → Click incident → View AI Summary + RCA → Assign to responder → Escalate with reason → Check SLA timer → Timeline shows provenance → Analytics shows trends
```

This path is tested by:
1. `verify_live.sh` (13 curl checks)
2. Playwright `sacred-path.spec.ts` (14-step browser test)
3. Manual walkthrough before submission

---

## 24. Fast Debug Cycle for Frontend Build Failures

```
1. npx tsc --noEmit        # TypeScript errors (fast)
2. npm run build           # ESLint + build (slow, but catches ESLint)
3. npm run lint -- --quiet # ESLint only (fast)
```

If build fails but tsc passes → it's ESLint. Fix the ESLint error, rarely is it a real code problem. Common ESLint traps:
- `react-hooks/exhaustive-deps` (missing/wrong deps)
- `@typescript-eslint/no-unused-vars` (unused imports/vars)
- `@next/next/no-img-element` (use `next/image`)
