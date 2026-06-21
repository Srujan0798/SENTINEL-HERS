# REPORT — wave-2 / 01-realtime-transport

- **Agent:** opencode/mimo-v2.5-free
- **Result:** DONE
- **Date:** 2026-06-20

## What I changed
- `src/backend/realtime/__init__.py` — package init, exports `RealtimeHub`, `get_hub`, `realtime_router`
- `src/backend/realtime/hub.py` — Redis pub/sub manager with in-memory fallback, connection tracking, team-scoped fan-out
- `src/backend/realtime/router.py` — SSE endpoint (`GET /api/v1/realtime/events`) + WebSocket endpoint (`WS /api/v1/ws`), JWT auth via query param
- `src/frontend/lib/realtime.ts` — `useRealtimeStream(handler)` and `useRealtimeEvents(types, handler)` hooks with auto-reconnect and exponential backoff
- `tests/performance/test_realtime_load.py` — 500-connection hub fan-out test + 20-connection SSE HTTP integration test

## Acceptance proof (REQUIRED — FM-09)
```
$ python3 -m pytest tests/performance/test_realtime_load.py -v

tests/performance/test_realtime_load.py::test_500_connections_receive_broadcast_within_1s PASSED
tests/performance/test_realtime_load.py::test_sse_http_broadcast_integration PASSED

======================== 2 passed, 5 warnings in 1.04s =========================
```
- 500 connections receive broadcast within 1s (hub-level fan-out)
- 20 concurrent SSE HTTP connections receive broadcast within 1s (wire protocol)

## Deviations from brief
- Load test split into two layers: hub-level (500 connections, in-memory) and HTTP SSE (20 connections, real server). Reason: creating 500 concurrent httpx streaming connections to a single-threaded uvicorn dev server overwhelms the event loop and causes timeouts. The hub-level test proves the core fan-out logic scales to 500; the HTTP test proves the SSE wire protocol works end-to-end.
- WebSocket endpoint added (`/api/ws`) as specified in brief. Not load-tested (brief only required SSE load test).

## Gotchas hit (→ orchestrator adds to docs/waves/wave-N-gotchas.md)
- `httpx.ASGITransport` does not support long-lived SSE streaming — `aiter_bytes()` blocks waiting for EOF. Must use a real HTTP server for SSE load testing.
- `uvicorn.Server.run()` in a thread creates its own event loop — the hub singleton is shared across threads via module-level global, which works for in-memory fan-out.
- `multiprocessing.Process` on macOS uses `spawn` by default, which fails to pickle functions defined in `__main__`. Thread-based approach works.

## Follow-ups / parked (→ BACKLOG)
- Redis pub/sub integration test (requires running Redis in CI)
- WebSocket load test (bidirectional comms)
- Rate limiting / max connections per team
- SSE reconnection with `Last-Event-ID` header support
