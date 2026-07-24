You are a Tier-2 worker on SENTINEL (METIS Hard — AI-native engineering ops platform).
Execute ONE self-contained task and STOP. Do not plan other waves. Do not push or deploy.

# LAW
1. Build ONLY what this brief asks. Write ONLY to the write-set. Never touch the forbid-set.
2. Do NOT redesign architecture or expand scope.
3. Fail loud: no bare `except: pass`, no silent fallback that hides errors. Graceful unavailable is OK if it surfaces `available:false` + reason.
4. Run acceptance commands. Paste REAL terminal output in your report. No proof = not done.
5. Write report to the exact path below.
6. If blocked: report BLOCKED with one specific question — do not guess.
7. Sacred demo path must keep working.
8. Repo root: SENTINEL-HERS. Do not commit secrets. Never return container env/secrets in API JSON.

# TASK — wave-10 / 03-container-monitoring

## Goal (one sentence)
Make the **Kubernetes + Docker deployment monitoring** real: clients connect when available, list
containers/pods with health, monitoring UI shows them — with clean graceful-fallback when no
cluster is reachable (e.g. on Render).

## Context
- Existing: `src/backend/integrations/docker/client.py`, `src/backend/integrations/k8s/client.py`,
  `src/backend/integrations/containers/`, `src/frontend/src/app/(dashboard)/monitoring/page.tsx`.

## Write-set (ONLY these paths)
- `src/backend/integrations/docker/`
- `src/backend/integrations/k8s/`
- `src/backend/integrations/containers/`
- `src/frontend/src/app/(dashboard)/monitoring/page.tsx`
- `tests/integration/test_containers.py` (new — mocked docker/k8s client)
- `work/reports/wave-10/03-container-monitoring.report.md`

## Forbid-set
- Non-integration backend, auth, deploy config for other services
- chat / anomaly / voice / postmortem files

## Blast radius
r1 (read-only cluster state). Never expose env/secrets (FM-07).

## Steps
1. Each client degrades gracefully: no daemon/cluster → `available:false` + reason; never crash the endpoint.
2. Endpoint returns containers/pods: name, status, restarts, image (NOT env/secrets).
3. Monitoring UI: containers/pods panel; show fallback state clearly when unavailable.
4. Tests with mocked client for available AND unavailable branches.

## Acceptance (PROOF required)
- `python -m pytest tests/integration/test_containers.py -q` → pass (both branches). Paste output.
- Paste endpoint JSON for no-daemon fallback showing `available:false` + reason.

## Report path
`work/reports/wave-10/03-container-monitoring.report.md`

### Report template
```
# REPORT — wave-10 / 03-container-monitoring
- **Agent:** <name>
- **Result:** DONE | PARTIAL | BLOCKED
- **Date:** <YYYY-MM-DD>
## What I changed
## Acceptance proof (REQUIRED)
```
$ command
output
```
## Deviations
## Gotchas
## Follow-ups
```

Then STOP.
