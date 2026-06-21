# TASK — wave-2 / 01-realtime-transport

## Goal
SSE + WebSocket realtime hub so the frontend gets live pushes < 1s latency. Redis pub/sub for fan-out.

## Context
- Wave: 2. Depends on wave-1 (auth merged). Read `src/backend/auth/` to get `get_current_user`.
- Contract: `.specify/specs/wave-0/contracts/openapi.yaml` `/realtime/events` SSE path.

## Write-set (ONLY these)
- src/backend/realtime/
- src/frontend/lib/realtime.ts

## Forbid-set
- src/backend/auth/, src/backend/rbac/, frontend/app/ (other wave-2 agents own those)

## Blast radius
r1.

## Steps
1. `src/backend/realtime/`: `hub.py` (Redis pub/sub manager), `router.py` (SSE `/api/realtime/events` + WS `/api/ws`).
2. Any backend service can call `await hub.publish(team_id, event_type, payload)` to push to all connected clients of that team.
3. Auto-reconnect SSE on drop (retry header).
4. `src/frontend/lib/realtime.ts`: `useRealtimeStream(handler)` hook — SSE primary, reconnects on close, dispatches typed events.
5. Load-test stub in `tests/performance/test_realtime_load.py` — 500 concurrent SSE connections, all receive a broadcast within 1s.

## Acceptance (PROOF — FM-09)
```
pytest tests/performance/test_realtime_load.py -v
# Expected: PASSED — 500 connections, broadcast latency < 1s
```

## Report to
`work/reports/wave-2/01-realtime-transport.report.md`
