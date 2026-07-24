# TASK — wave-10 / 03-container-monitoring

> Self-contained brief. Brownie feature (rubric: System Design 25% + DevOps 10%).

## Goal (one sentence)
Make the **Kubernetes + Docker deployment monitoring** real: the existing clients connect to a live
Docker/K8s API when available, list containers/pods with health, and the monitoring UI shows them —
with a clean graceful-fallback message when no cluster is reachable (e.g. on Render).

## Context
- Wave: 10. Depends on: wave-9 green.
- Existing: `src/backend/integrations/docker/client.py`, `src/backend/integrations/k8s/client.py`,
  `src/backend/integrations/containers/`, `src/frontend/src/app/(dashboard)/monitoring/page.tsx`.

## Write-set (FM-13)
- `src/backend/integrations/docker/`, `src/backend/integrations/k8s/`, `src/backend/integrations/containers/`
- `src/frontend/src/app/(dashboard)/monitoring/page.tsx` (containers/pods panel)
- `tests/integration/test_containers.py` (new — mocked docker/k8s client)

## Forbid-set
- Non-integration backend, auth, deploy config for other services

## Blast radius
r1 (reads container/cluster state; no mutation). Never expose container env/secrets in the API response (FM-07).

## Steps
1. Ensure each client degrades gracefully: no daemon/cluster → return `available:false` + reason, never crash the endpoint (FM-11: surfaced, not swallowed).
2. Endpoint returns containers/pods with name, status, restarts, image (NOT env/secrets).
3. Monitoring UI: a "Deployments" panel; show the fallback state clearly when unavailable.
4. Test with a mocked client for both the available and unavailable branches.

## Acceptance (PROOF — FM-09)
- `python -m pytest tests/integration/test_containers.py -q` → pass (both branches). Paste it.
- Paste the endpoint JSON in the no-daemon fallback case showing `available:false` + reason (proves it fails loud-but-graceful).

## Guardrails
- FM-11 graceful fallback, logged · FM-07 never leak container secrets/env.

## Report to
`work/reports/wave-10/03-container-monitoring.report.md`
