# SENTINEL — ETERNAL FINAL PLAN (100% submission)

> **Tier-1 Orchestrator only.** No feature labor in this file.  
> Sources of law: `ps.md` · `ADAPTOID-LITE.md` (§0S SHIP, §1 dual-tier, §5 waves, §13 FMs) · `CLAUDE.md` · `HANDOFF.md` · `plan/EXECUTION.md`  
> Archetype: **hackathon + saas-product lean** · Tier: **T2** · Demo path is sacred.

**Invariant (Adaptoid):** *Evidence or it didn’t happen (FM-09). Disjoint write-sets (FM-13). Replace HANDOFF, never append (FM-01/14). Orchestrator never implements; workers never plan.*

---

## 0. Intent lock (already decided — do not re-litigate)

| Decision | Value |
|----------|--------|
| Deploy | Render (API + Postgres + Redis) + Vercel (Next.js) |
| AI | Live Claude/Gemini keys in dashboard; mock fallback for tests |
| Scope | Mandatory bar (wave-9) **then** brownie max (wave-10) |
| Worker harness | OpenCode (or any Tier-2 CLI) — one task per window |
| Brain | You + this orchestrator (Grok/Claude) — reviews, merges, plans |

---

## 1. Ground truth — what is ALREADY DONE (do NOT reassign)

| Gate | Status | Evidence |
|------|--------|----------|
| Core product W0–W8 | Built | modules under `src/backend`, `src/frontend` |
| False-green logs fix | ✅ | `a7d4277` + `/logs/` gitignore anchor |
| Full suite | ✅ **150 passed** | independent pytest |
| Render blueprint | ✅ | `render.yaml`, `Dockerfile.api`, `deployment/render/release.sh` · `5e93840` |
| CORS + idempotent seed + requests | ✅ | `258fc66` |
| Vercel config + env wiring | ✅ | `acccc70` · Root = `src/frontend` |
| Live AI providers | ✅ | `285bb38` |
| WRITEUP ≥500 words | ✅ | `WRITEUP.md` (~1149 words) |
| Judge walkthrough | ✅ | `docs/PRODUCTION_WALKTHROUGH.md` |
| README / problem brief | ✅ | `README.md`, `ps.md` |
| Meaningful commit history | ✅ building | local `main` **ahead of origin** |

### What is NOT done (blocks “100% valid submission”)

| # | Gap | Owner | Blast |
|---|-----|--------|-------|
| G1 | `git push` of local commits | **HUMAN** | r3 |
| G2 | Live Render URL healthy | **HUMAN** | r3 |
| G3 | Live Vercel URL + CORS cross-wire | **HUMAN** | r3 |
| G4 | Real HTTPS URLs pasted into README | Agent F **after** G2/G3 | r1 |
| G5 | Wave-10 brownie harden+prove (5 tasks) | **OpenCode agents A–E** | r1 |
| G6 | Optional CI (anti-regression) | Agent G | r1 |
| G7 | Final SHIP audit + freeze | **Orchestrator + HUMAN** | r0 |

**Submission bar from `ps.md` (mandatory):**
1. Live deployment URL  
2. Public GitHub + meaningful commits  
3. README setup  
4. WRITEUP 1–2 pages  

Brownie (wave-10) = **rubric max / race lane**, not the legal minimum — but you locked GO BIG.

---

## 2. Eternal SHIP ladder (Adaptoid §0S)

Never claim SHIP until every required box is green **with proof**.

```
PHASE-H  HUMAN DEPLOY GATE     (G1–G3)     ← START HERE if not pushed
PHASE-P  PARALLEL BROWNIE      (B∥C∥E)     ← OpenCode Round 1
PHASE-S  SERIAL AI BROWNIE     (A → D)     ← OpenCode Round 2
PHASE-U  URL + SUBMISSION POLISH (F)       ← after live URLs
PHASE-C  CI SHIELD (optional G)            ← eternal anti-wipe
PHASE-Z  FINAL AUDIT + FREEZE              ← orchestrator
```

### Self-heal rules (every phase)
- `on_acceptance_fail → REVISE brief with exact gap` (never merge red)
- `on_write_set_collision → kill one agent, sequence` (FM-13)
- `on_false_green_suspect → orchestrator re-runs acceptance` (FM-09)
- `on_context_full → rewrite HANDOFF, clear chat` (FM-04/14)
- `on_secret_leak → rotate + purge history` (FM-07)

---

## 3. PHASE-H — Human deploy (you do this; no agent)

**Do in order. Do not start Round-1 agents until step H4 is green** (suite already green offline; deploy can run in parallel with Round 1 if you want speed — preferred: push first so agents work on same remote).

| Step | Action | Done when |
|------|--------|-----------|
| H1 | `git push origin main` (confirm intentionally — 10 local commits) | `git status` clean vs origin |
| H2 | Render → New → Blueprint → this repo → Apply | service building |
| H3 | Render env: `ANTHROPIC_API_KEY`, optional `GEMINI_API_KEY`, `CORS_ORIGINS` temp | saved |
| H4 | Wait deploy → `curl https://<api>/healthz` → `{"status":"ok"}` | 200 |
| H5 | Vercel → import repo → **Root Directory = `src/frontend`** | project created |
| H6 | Vercel env: `NEXT_PUBLIC_API_BASE_URL=https://<api-host>` (no trailing slash) | saved |
| H7 | Deploy frontend → note `https://<app>.vercel.app` | live UI |
| H8 | Render `CORS_ORIGINS=https://<app>.vercel.app` → Manual Deploy | redeploy done |
| H9 | Login `demo@sentinel.io` / `Sentinel2026!` → open SEV1 | demo path works |
| H10 | Tell orchestrator both URLs → dispatch Agent F | URLs in chat |

**Demo credentials (seeded, intentional):** email `demo@sentinel.io` · password `Sentinel2026!`

---

## 4. Universal worker shell (paste ABOVE every task file)

Copy exactly:

```
You are a Tier-2 worker on SENTINEL (METIS Hard track). Execute ONE self-contained task and STOP.

LAW (Adaptoid dual-tier):
1. Read the task file. Build ONLY what it asks. Write ONLY to its write-set. Never touch the forbid-set (FM-13/FM-08).
2. Use your own tools/skills. Do NOT redesign architecture or expand scope.
3. Fail loud (FM-11): no bare except/pass, no silent fallback, no synthetic data to fake a pass.
4. Run the acceptance command(s). Paste REAL terminal output into your report (FM-09). No proof = not done.
5. Write report to the exact path in the task (work/reports/wave-10/…).
6. If blocked: report BLOCKED with one specific question — do not guess.
7. Do NOT commit, push, deploy, or edit HANDOFF/EXECUTION/render.yaml/api/main.py unless the write-set says so.
8. Sacred demo path must keep working: login → SEV1 → AI summary → assign/SLA → timeline → analytics.

Then STOP. Orchestrator re-runs acceptance and merges.

[TASK FILE FOLLOWS — paste full contents of the task .md below this line]
```

Also on disk: `work/WORKER_PROMPT.md`.

---

## 5. OpenCode agent roster — exact assignment

### Round 1 — PARALLEL (safe write-sets)

| Agent | Label | Task file | Write-set (summary) | Acceptance (orchestrator re-runs) |
|-------|--------|-----------|---------------------|-----------------------------------|
| **B** | Anomaly | `work/wave-10/02-predictive-anomaly.md` | `src/backend/ml/`, analytics routes/UI, `test_anomaly.py` | `pytest tests/integration/test_anomaly.py -q` |
| **C** | Containers | `work/wave-10/03-container-monitoring.md` | docker/k8s/containers, monitoring UI, `test_containers.py` | `pytest tests/integration/test_containers.py -q` |
| **E** | Voice | `work/wave-10/05-voice-to-ticket-e2e.md` | `src/backend/voice/`, VoiceRecorder, `test_voice.py` | `pytest tests/integration/test_voice.py -q` |

### Round 2 — SERIAL (shared `src/backend/ai/`)

| Agent | Label | Task file | After | Acceptance |
|-------|--------|-----------|-------|------------|
| **A** | Chat RAG | `work/wave-10/01-conversational-chatbot.md` | Round 1 merged | `pytest tests/integration/test_ai_chat.py -q` + cross-tenant assertion |
| **D** | Postmortem | `work/wave-10/04-postmortem-export.md` | **A merged** | `pytest tests/integration/test_postmortem.py -q` |

### Round 3 — polish (after live URLs)

| Agent | Label | Goal | Write-set |
|-------|--------|------|-----------|
| **F** | URL polish | Paste real HTTPS frontend+backend into README + SUBMISSION | `README.md`, `docs/SUBMISSION.md` only |
| **G** | CI shield (optional, race insurance) | `.github/workflows/ci.yml` pytest + frontend build | new workflow only |

### NEVER parallel
- A ∥ D (both touch `src/backend/ai/`)
- Anyone editing `api/main.py` / `render.yaml` during brownie wave without a new orchestrator task

---

## 6. Copy-paste packs (one window each)

### Agent B — paste

```
[UNIVERSAL WORKER SHELL from §4]

Then open and paste the FULL file:
work/wave-10/02-predictive-anomaly.md

Repo root: SENTINEL-HERS. Branch: main. Do not push.
Report: work/reports/wave-10/02-predictive-anomaly.report.md
```

### Agent C — paste

```
[UNIVERSAL WORKER SHELL from §4]

Then open and paste the FULL file:
work/wave-10/03-container-monitoring.md

Repo root: SENTINEL-HERS. Branch: main. Do not push.
Report: work/reports/wave-10/03-container-monitoring.report.md
```

### Agent E — paste

```
[UNIVERSAL WORKER SHELL from §4]

Then open and paste the FULL file:
work/wave-10/05-voice-to-ticket-e2e.md

Repo root: SENTINEL-HERS. Branch: main. Do not push.
Report: work/reports/wave-10/05-voice-to-ticket-e2e.report.md
```

### Agent A — paste (only after Round 1 merges)

```
[UNIVERSAL WORKER SHELL from §4]

Then open and paste the FULL file:
work/wave-10/01-conversational-chatbot.md

Repo root: SENTINEL-HERS. Branch: main. Do not push.
Report: work/reports/wave-10/01-conversational-chatbot.report.md
CRITICAL: team-scope every retrieval — no cross-tenant leak (Security 15%).
```

### Agent D — paste (only after A merges)

```
[UNIVERSAL WORKER SHELL from §4]

Then open and paste the FULL file:
work/wave-10/04-postmortem-export.md

Repo root: SENTINEL-HERS. Branch: main. Do not push.
Report: work/reports/wave-10/04-postmortem-export.report.md
Postmortem must ground in REAL timeline/logs — no fictional template (FM-09).
```

### Agent F — paste (after you have both live URLs)

```
[UNIVERSAL WORKER SHELL from §4]

TASK (inline — no other files):
1. Replace placeholder live URLs in README.md top table with:
   - Frontend: <PASTE_VERCEL_URL>
   - Backend:  <PASTE_RENDER_URL>
2. Update docs/SUBMISSION.md GitHub + Live Deployment fields if present.
3. Do not invent metrics. Do not touch code.
4. Prove: grep -c "https://" README.md  (expect ≥2 real deploy hosts)
5. Report: work/reports/wave-10/06-url-polish.report.md
Write-set ONLY: README.md, docs/SUBMISSION.md
```

### Agent G — paste (optional eternal shield)

```
[UNIVERSAL WORKER SHELL from §4]

TASK (inline):
Create .github/workflows/ci.yml that on push/PR:
- sets up Python 3.11+, installs api/requirements.txt, runs pytest -q
- sets up Node, npm ci in src/frontend, runs NEXT_PUBLIC_API_BASE_URL=https://example.test npm run build
No secrets. No deploy. Fail loud on red.
Write-set ONLY: .github/workflows/ci.yml
Report: work/reports/wave-10/07-ci-shield.report.md
```

---

## 7. Orchestrator merge loop (YOU or me — never trust agent paste)

For each returned report:

```
1. git status / git diff — files ⊆ write-set? else REJECT
2. Re-run acceptance command yourself (FM-09)
3. Full suite smoke if they touched backend: python -m pytest -q
4. APPROVE → one meaningful commit message → update plan/EXECUTION.md row
5. REVISE → send exact failing log + missing acceptance line
6. Rewrite HANDOFF.md to current truth (never append)
```

Suggested commit pattern:
- `feat(ml): predictive anomaly surface + alert hook (wave-10/02)`
- `feat(containers): docker/k8s monitoring prove (wave-10/03)`
- etc.

---

## 8. Rubric map (why this order wins the race)

| Rubric | Weight | Wave that locks it |
|--------|--------|--------------------|
| System Design | 25% | core + containers (C) + architecture docs |
| Realtime | 20% | already in W2 — protect demo path |
| AI | 20% | 9.6 + A chat + D postmortem |
| Security | 15% | RBAC + team-scope chat test + webhooks already |
| UI/UX | 10% | walkthrough + voice UX (E) |
| DevOps | 10% | Render/Vercel + optional CI (G) |

**Eternal edge vs competitors:** green suite on clean checkout · live URL · WRITEUP honesty · commit history · CI so nobody “wipes the lane” with a missing module again (Hall of Shame Pattern 1).

---

## 9. PHASE-Z — Final freeze checklist (orchestrator)

- [ ] origin/main == local main  
- [ ] `curl` healthz + metrics on Render  
- [ ] Vercel login → SEV1 → AI panel → timeline → analytics  
- [ ] README has **real** HTTPS frontend + backend  
- [ ] WRITEUP.md present  
- [ ] `python -m pytest -q` → 150+ passed  
- [ ] No secrets in git (`git log -p | grep -i sk-ant` empty)  
- [ ] HANDOFF says SHIPPED with commit hashes  
- [ ] Optional: all 5 wave-10 reports APPROVED  

When all boxes checked → **submission is eternal-valid**. Only then stop opening new features (FM-08).

---

## 10. How you monitor me (orchestrator contract)

You say:
- **`status`** → I rewrite ground truth table only  
- **`review <agent report path>`** → I re-run acceptance + APPROVE/REVISE  
- **`dispatch round1`** → I confirm B/C/E prompts only (no code)  
- **`merge`** → I verify then commit (ask first if you want commits)  
- **`ship`** → PHASE-Z checklist  

I will **not** write feature code unless you explicitly break dual-tier law.

---

## 11. Immediate next 3 actions (bottom line)

1. **YOU:** `git push origin main` (or tell orchestrator “push approved”).  
2. **YOU:** Render + Vercel clicks (PHASE-H).  
3. **YOU:** Open 3 OpenCode windows → paste Agent **B**, **C**, **E** packs (§6).  

When reports land, paste them here → I review under FM-09 and guide merges.
