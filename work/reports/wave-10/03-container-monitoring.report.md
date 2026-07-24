# REPORT — wave-10 / 03-container-monitoring

- **Agent:** C
- **Result:** DONE
- **Date:** 2026-07-24

## What I changed

### Backend clients — availability-aware return format
- **`src/backend/integrations/docker/client.py`**: Moved `import docker` to module level with `try/except`. Changed return type from `list` to `dict` with keys `available` (bool), `reason` (str|None), `containers` (list). No daemon → `available:false` + reason string. Never crashes (FM-11).
- **`src/backend/integrations/k8s/client.py`**: Same pattern. Module-level `try/except` for `kubernetes` import. Returns `available`, `reason`, `pods`. Timeout and config errors surface as reason. Never crashes.

### API route — merged availability view
- **`src/backend/integrations/containers/routes.py`**: Response now nests `docker` and `kubernetes` as objects with `available`/`reason` fields alongside their container lists. Auth dependency unchanged.

### Monitoring UI — clear fallback state
- **`src/frontend/src/app/(dashboard)/monitoring/page.tsx`**: Added `SourceStatus` and `ContainersResponse` interfaces. Docker/K8s rows show green "Connected (N)" when available or gray "Unavailable — <reason>" when not. Table renders when containers exist; empty-state message when both unavailable.

### Integration tests — 12 tests, all passing
- **`tests/integration/test_containers.py`** (new): Tests Docker available/unavailable, K8s available/unavailable, and API endpoint for both-unavailable, mixed, and both-available scenarios. Uses `unittest.mock.patch` on module-level `_docker`/`_k8s_client`/`_k8s_config` objects.

## Acceptance proof (REQUIRED)

### pytest — all 12 tests pass
```
$ python -m pytest tests/integration/test_containers.py -q
............                                                             [100%]
12 passed, 8 warnings in 5.04s
```

### Endpoint JSON — no-daemon fallback
```json
{
  "docker": {
    "available": false,
    "reason": "docker Python package not installed",
    "containers": []
  },
  "kubernetes": {
    "available": false,
    "reason": "kubernetes Python package not installed",
    "pods": []
  },
  "total": 0,
  "unhealthy": []
}
```

## Deviations
- None. All changes stay within write-set. No architecture redesign.

## Gotchas
- The `docker` and `kubernetes` packages are optional dependencies. Clients handle both "package not installed" and "daemon/cluster unreachable" cases.
- Auth dependency override in tests uses `app.dependency_overrides[get_current_user_dependency]` pattern, matching existing test conventions.
- No env/secrets are exposed in any response (FM-07 compliant — only name, image, status, health, cpu_pct, mem_mb, started_at, source).

## Follow-ups
- Wire real Docker/K8s health stats (mem_mb, cpu_pct) for pods via metrics-server.
- Add polling/SSE for live container status updates.
- Consider per-source "last checked" timestamps in the response.
