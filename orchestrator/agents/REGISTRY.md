# Agent Registry & Orchestration Map — SENTINEL

> **Tier-1 orchestrator owns this file.** It maps your 12 external AI agents (Tier-2 workers) to
> waves/tasks. The orchestrator writes the task file into `work/<wave>/<task>.md`; you paste it
> into the assigned agent's window. The agent writes code + a report; the orchestrator reviews & merges.
>
> **You assign — this is the *recommended* mapping.** Reassign freely; only keep the
> disjoint-write-set law (FM-13): two agents in the same wave must never write the same file.

## Roster (12 workers)

| Agent | Suggested specialty | Why |
|---|---|---|
| **claude**     | Orchestration-adjacent reasoning, AI layer, root-cause | strongest long-context reasoning |
| **gpt**        | Backend services, API design, integrations | reliable structured code |
| **gemini**     | AI summaries, multimodal (voice-to-ticket), RAG | multimodal + long context |
| **kimi**       | Backend heavy lifting, realtime infra | strong agentic coding, big context |
| **deep**       | DB schema, data modelling, anomaly ML | deep reasoning on data |
| **qwen**       | Frontend components, dashboard UI | solid codegen |
| **mistral**    | Auth/RBAC, security spine | tight, correct systems code |
| **grok**       | Integrations (GitHub/GitLab), webhooks | fast iteration |
| **perplexity** | Research-grounded tasks, monitoring/log search | retrieval strength |
| **minimax**    | Realtime transport, comms channels | throughput |
| **mimo**       | Analytics, charts, container monitoring | breadth |
| **z.ai**       | Polish, demo hardening, observability config | generalist finisher |

> Specialties are defaults, not locks. Capacity > specialty — if an agent is free, assign it.

## Wave → Task → Agent assignment

### Wave-0 — Foundation & Contracts (SEQUENTIAL, one owner at a time)
| Task | Recommended agent | Write-set (disjoint) |
|---|---|---|
| 00-repo-and-compose | **gpt** | docker-compose, Dockerfiles, Makefile, CI |
| 01-db-schema-and-contracts | **deep** | schema/, contracts/, docs/schemas/ |
| 02-design-system | **qwen** | frontend/ui, theme/ |

### Wave-1 — Auth + RBAC + Teams (parallel ×3)
| Task | Agent | Write-set |
|---|---|---|
| 01-auth-backend | **mistral** | backend/auth/ |
| 02-rbac-policy | **claude** | backend/rbac/ |
| 03-auth-frontend | **qwen** | frontend/(auth)/ |

### Wave-2 — Realtime Dashboard + Severity/Triage (parallel ×3)
| Task | Agent | Write-set |
|---|---|---|
| 01-realtime-transport | **minimax** | backend/realtime/, frontend/lib/realtime.ts |
| 02-incident-model-and-api | **kimi** | backend/incidents/ |
| 03-dashboard-ui | **qwen** | frontend/dashboard/ |

### Wave-3 — Logs/Alerts + Service Health (parallel ×3)
| Task | Agent | Write-set |
|---|---|---|
| 01-log-ingestion | **gpt** | backend/logs/, backend/ingest/ |
| 02-service-health | **deep** | backend/health/, prometheus.yml |
| 03-monitoring-ui | **perplexity** | frontend/monitoring/ |

### Wave-4 — AI Layer (parallel ×3) ★ highest-weight differentiator
| Task | Agent | Write-set |
|---|---|---|
| 01-ai-summary-rootcause | **claude** | backend/ai/summary/, backend/ai/rootcause/ |
| 02-ai-chatbot-rag | **gemini** | backend/ai/chat/, frontend/chat/ |
| 03-auto-postmortem | **kimi** | backend/ai/postmortem/ |

### Wave-5 — Integrations + Timeline/Provenance (parallel ×2)
| Task | Agent | Write-set |
|---|---|---|
| 01-vcs-integration | **grok** | backend/integrations/github,gitlab/ |
| 02-timeline-provenance | **gpt** | backend/timeline/, frontend/timeline/ |

### Wave-6 — Task/SLA + Comms (parallel ×2)
| Task | Agent | Write-set |
|---|---|---|
| 01-task-sla-engine | **mistral** | backend/tasks/, backend/sla/ |
| 02-incident-comms | **minimax** | backend/comms/, frontend/comms/ |

### Wave-7 — Analytics + Anomaly ML + Container Monitoring (parallel ×3)
| Task | Agent | Write-set |
|---|---|---|
| 01-analytics-dashboard | **mimo** | backend/analytics/, frontend/analytics/ |
| 02-anomaly-ml | **deep** | backend/ml/anomaly/, models/ |
| 03-container-monitoring | **grok** | backend/integrations/k8s,docker/ |

### Wave-8 — Polish + Demo + Deploy (parallel ×3)
| Task | Agent | Write-set |
|---|---|---|
| 01-demo-hardening-and-seed | **z.ai** | scripts/seed_demo.py |
| 02-voice-to-ticket | **gemini** | frontend/voice/, backend/ai/transcribe/ |
| 03-deploy-and-observability | **z.ai** | docker-compose.prod.yml, docs/operational/ |

## Load balance (tasks per agent across the run)
claude 2 · gpt 3 · gemini 2 · kimi 2 · deep 3 · qwen 3 · mistral 2 · grok 2 · perplexity 1 · minimax 2 · mimo 1 · z.ai 2

## Critical path (longest dependency chain → schedule first)
`wave-0 → wave-1 → wave-2 → wave-4 → wave-8`. Waves 3/5/6/7 fan out off this spine.
Run wave-0 alone. Then 1. Then 2+3 in parallel. Then 4+5+6 in parallel. Then 7. Then 8.
