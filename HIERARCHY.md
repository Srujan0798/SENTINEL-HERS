# HIERARCHY — repo map + ownership

| Path | Purpose | Owner |
|---|---|---|
| `CLAUDE.md` / `KIMI.md` / `AGENTS.md` | kernel (auto-loaded) | orchestrator |
| `HANDOFF.md` | current state, resume point | orchestrator |
| `plan/{PRD,ARCHITECTURE,EXECUTION}.md` | living strategy | orchestrator |
| `workflows/sentinel.plan.yaml` | wave/task DAG + write-sets | orchestrator |
| `orchestrator/agents/REGISTRY.md` | agent → task assignment | orchestrator |
| `docs/SCOPE_GUARD.md` | IN/OUT/LATER | orchestrator |
| `.specify/specs/wave-N/` | per-wave spec + contracts | orchestrator |
| `work/<wave>/<task>.md` | task briefs (orchestrator writes) | orchestrator |
| `work/reports/<wave>/` | worker reports (workers write) | Tier-2 agents |
| `src/**` | feature code | Tier-2 agents (per write-set) |
| `tests/**` | test suites | Tier-2 agents + orchestrator (acceptance) |
| `evals/**` | eval-driven dev tasks | orchestrator |
| `attic/` | superseded work (never deleted) | orchestrator |

**Boundary law:** orchestrator never writes `src/`; workers never write `plan/`, `orchestrator/`, or another agent's write-set.
