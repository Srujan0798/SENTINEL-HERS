# SKILLS_MANIFEST — SENTINEL Hard-track excellence stack

> Installed via `npx skills add` (find-skills ecosystem).  
> **Honest rule:** skills do **not** equal product quality. They only equip agents.  
> Current product quality: **not 100/100**, not 1000/100 — roughly **UI ~25–40%, backend/API ~70–80%** until browser UX is proven with `verification-before-completion` + `webapp-testing`.

---

## Install location

| Path | Purpose |
|------|---------|
| `.agents/skills/*` | Canonical skill packages (project) |
| `.claude/skills/*` | Symlinks for Claude Code |
| `skills-lock.json` | Pinned versions — restore with `npx skills experimental_install` |

Agents wired: **Claude Code · OpenCode · Cursor** (+ lockfile multi-agent metadata).

---

## PS / Rubric → skills map

| PS / rubric axis | Weight | Skills to load when working | What “1000/100” means |
|------------------|--------|----------------------------|------------------------|
| **System Design & Scalability** | 25% | `improve-codebase-architecture`, `domain-modeling`, `supabase-postgres-best-practices` | Clear bounded contexts, indexes, no N+1, tenancy model explicit |
| **Real-Time Features & Reliability** | 20% | `systematic-debugging`, `webapp-testing`, `playwright-cli`, `verification-before-completion` | SSE “connected” in **browser**, no fake status, reconnection |
| **AI Integration & Automation** | 20% | `qa`, `tdd` / `test-driven-development`, `code-review` | Summary/RCA/chat/postmortem **visible + correct shape** in UI |
| **Security & Access Control** | 15% | `security-review`, `verification-before-completion` | JWT everywhere, no tenant leak, seed secret not default in prod |
| **UI/UX & Product Quality** | 10% | `impeccable` (+ polish/critique/harden), `frontend-design`, `design-taste-frontend`, `high-end-visual-design`, `redesign-existing-projects`, `ui-ux-pro-max`, `web-design-guidelines`, `design-an-interface`, `vercel-react-best-practices` | Login works first try; war room dense; no dead nav; mobile usable |
| **Deployment & DevOps** | 10% | `deploy-to-vercel`, `qa` | Live FE+BE always match main; demo-status ready after every deploy |
| **Meta / process** | — | `find-skills`, `requesting-code-review` | Never claim done without live browser proof |

---

## How to use (agents)

1. **Before UI work:**  
   `node .agents/skills/impeccable/scripts/context.mjs --target src/frontend`  
   then follow `PRODUCT.md` + `DESIGN.md` + impeccable **Operate** mode.

2. **Before claiming done:**  
   Load `verification-before-completion` — run live probes + pytest + FE build. No greenwash.

3. **Login/nav regressions:**  
   Load `systematic-debugging` + `webapp-testing` / `playwright-cli` — **browser**, not curl only.

4. **Security pass:**  
   Load `security-review` against `src/backend/**` + auth paths.

5. **Architecture cleanup:**  
   Load `improve-codebase-architecture` + `domain-modeling` only after UI path is solid.

---

## Installed package list (count ~30)

```
find-skills
impeccable
frontend-design
web-design-guidelines
vercel-react-best-practices
deploy-to-vercel
design-taste-frontend
high-end-visual-design
redesign-existing-projects
ui-ux-pro-max (+ brand, design, design-system, ui-styling, banner-design, slides)
design-an-interface
improve-codebase-architecture
domain-modeling
tdd
qa
code-review
security-review
webapp-testing
playwright-cli (+ dev)
supabase-postgres-best-practices
verification-before-completion
systematic-debugging
test-driven-development
requesting-code-review
```

---

## Honest gap board (do not delete until true)

| Gap | Why it blocks “1000/100” | Skill to drive fix |
|-----|---------------------------|--------------------|
| Login / session UX still fragile historically | Judges bounce → score 0 | impeccable + webapp-testing |
| UI density / ops craft | Still not Radar-console grade everywhere | redesign-existing-projects + ui-ux-pro-max |
| Browser E2E not automated against prod | Curl ≠ user | playwright-cli + webapp-testing |
| Security depth unreviewed by skill | JWT fixed; deeper audit pending | security-review |
| Free-tier cold start / seed ops | Demo can die after redeploy | verification-before-completion |
| No Loom | Hard-track story incomplete | product (human) |

---

## Commands (refresh / add)

```bash
# Search
npx skills find "security review"

# Install more
npx skills add <owner/repo> -y -a claude-code -a opencode -a cursor -s <skill-name>

# Restore from lockfile
npx skills experimental_install

# List
npx skills list
```

---

## Law

**Installing skills ≠ finishing the product.**  
Every agent session must open this file + `PRODUCT.md` + `DESIGN.md` and ship **browser-proven** deltas only.
