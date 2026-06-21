# TASK — wave-7 / 03-container-monitoring

## Goal
Read Docker/K8s container/pod status and surface unhealthy containers to the monitoring dashboard.

## Context
- Wave: 7. Uses docker SDK (local) + optional k8s client (if KUBECONFIG present). Falls back gracefully if k8s unavailable.

## Write-set (ONLY these)
- src/backend/integrations/k8s/
- src/backend/integrations/docker/

## Forbid-set
- src/backend/integrations/github/, gitlab/, src/backend/analytics/, src/backend/ml/

## Blast radius
r1 (reads Docker socket — local only; k8s reads cluster state — no writes).

## Steps
1. `docker/client.py`: `list_containers()` → `[{name, image, status, health, cpu_pct, mem_mb, started_at}]` using `docker` Python SDK.
2. `k8s/client.py`: `list_pods()` → same schema. Uses `kubernetes` client with KUBECONFIG. Returns empty list if kubeconfig not found (FM-11: fail gracefully, log warning, do NOT crash).
3. `GET /api/integrations/containers` — merged list from docker + k8s; filters by `team_id` service labels.
4. Background poller: every 30s, check unhealthy/restarting containers → emit `container.unhealthy` realtime event + create SEV3 alert.
5. Monitoring UI (extend existing `src/frontend/src/components/health/`) — `<ContainerGrid>` showing container cards with status + restart count. Consume from health API.

## Acceptance (PROOF — FM-09)
```
pytest tests/integration/test_container_monitoring.py -v
# Expected: docker containers listed (uses running docker daemon); k8s returns [] gracefully when no config
```

## Report to
`work/reports/wave-7/03-container-monitoring.report.md`
