"""Load test: 500 concurrent SSE connections, broadcast latency < 1s.

Two layers tested:
  1. Hub fan-out (500 in-memory connections) — proves core pub/sub + fan-out.
  2. SSE HTTP integration (50 concurrent connections) — proves the wire protocol works.
"""

import asyncio
import json
import threading
import time
import uuid

import httpx
import pytest
import uvicorn
from fastapi import FastAPI

from src.backend.auth.service import create_access_token
from src.backend.realtime.hub import ConnectionEntry, RealtimeHub, get_hub
from src.backend.realtime.router import router as realtime_router

TEST_TEAM_ID = str(uuid.uuid4())
TEST_USER_ID = str(uuid.uuid4())
CONNECTION_COUNT = 500
BROADCAST_LATENCY_BUDGET = 1.0  # seconds
SERVER_PORT = 18999


def _create_test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(realtime_router, prefix="/api/v1")

    @app.post("/api/v1/test/broadcast")
    async def test_broadcast():
        hub = get_hub()
        await hub.publish(TEST_TEAM_ID, "load_test_broadcast", {"message": "hello", "seq": 1})
        return {"status": "ok"}

    return app


# Realtime SSE/WS auth is token-only (decodes team_id from the signed JWT, no DB
# lookup per connection), so the load test just needs a valid signed token.
_token = create_access_token(TEST_USER_ID, TEST_TEAM_ID, "admin")


@pytest.mark.asyncio
async def test_500_connections_receive_broadcast_within_1s():
    """500 in-memory connections receive a broadcast within 1s.

    Tests the hub fan-out directly (no HTTP overhead).
    """
    import src.backend.realtime.hub as hub_mod

    hub_mod._hub = RealtimeHub(use_redis=False)
    hub = get_hub()
    await hub.initialize()

    received_events: list[float] = []
    entries: list[ConnectionEntry] = []

    for i in range(CONNECTION_COUNT):
        entry = await hub.subscribe(TEST_TEAM_ID)
        entries.append(entry)

    assert hub.connection_count == CONNECTION_COUNT

    broadcast_time = time.monotonic()
    await hub.publish(TEST_TEAM_ID, "load_test_broadcast", {"message": "hello", "seq": 1})

    async def drain_entry(entry: ConnectionEntry):
        event = await asyncio.wait_for(entry.queue.get(), timeout=BROADCAST_LATENCY_BUDGET)
        if event.event_type == "load_test_broadcast":
            received_events.append(time.monotonic())

    drain_tasks = [asyncio.create_task(drain_entry(e)) for e in entries]
    done, pending = await asyncio.wait(drain_tasks, timeout=BROADCAST_LATENCY_BUDGET + 2.0)

    for t in pending:
        t.cancel()
    if pending:
        await asyncio.gather(*pending, return_exceptions=True)

    assert len(done) == CONNECTION_COUNT, f"Only {len(done)}/{CONNECTION_COUNT} received broadcast"
    assert len(received_events) == CONNECTION_COUNT, f"Only {len(received_events)}/{CONNECTION_COUNT} received broadcast"

    max_latency = max(t - broadcast_time for t in received_events)
    assert max_latency < BROADCAST_LATENCY_BUDGET, (
        f"Broadcast latency {max_latency:.3f}s exceeded {BROADCAST_LATENCY_BUDGET}s budget"
    )

    for e in entries:
        await hub.unsubscribe(e)
    await hub.shutdown()


@pytest.mark.asyncio
async def test_sse_http_broadcast_integration():
    """20 concurrent SSE HTTP connections receive a broadcast within 1s.

    Proves the full wire protocol works end-to-end.
    """
    app = _create_test_app()
    config = uvicorn.Config(app, host="127.0.0.1", port=SERVER_PORT, log_level="warning")
    server = uvicorn.Server(config)

    server_thread = threading.Thread(target=server.run, daemon=True)
    server_thread.start()

    for _ in range(50):
        try:
            async with httpx.AsyncClient() as c:
                r = await c.get(f"http://127.0.0.1:{SERVER_PORT}/api/v1/nonexistent", timeout=1.0)
                break
        except Exception:
            await asyncio.sleep(0.1)

    http_count = 20
    received_events: list[float] = []
    connected_count = 0
    connected_lock = asyncio.Lock()
    all_connected: asyncio.Event = asyncio.Event()

    try:
        async def sse_client(client_id: int):
            nonlocal connected_count
            url = f"http://127.0.0.1:{SERVER_PORT}/api/v1/realtime/events?token={_token}"
            async with httpx.AsyncClient() as client:
                async with client.stream("GET", url, timeout=30.0) as response:
                    assert response.status_code == 200
                    buffer = ""
                    connected = False
                    async for chunk in response.aiter_bytes():
                        buffer += chunk.decode("utf-8", errors="replace")
                        while "\n" in buffer:
                            line, buffer = buffer.split("\n", 1)
                            line = line.strip()
                            if not connected and line.startswith("event: connected"):
                                async with connected_lock:
                                    connected_count += 1
                                    if connected_count >= http_count:
                                        all_connected.set()
                                connected = True
                                continue
                            if connected and line.startswith("data: "):
                                try:
                                    data = json.loads(line[6:])
                                    if data.get("event_type") == "load_test_broadcast":
                                        received_events.append(time.monotonic())
                                        return
                                except json.JSONDecodeError:
                                    pass

        tasks = [asyncio.create_task(sse_client(i)) for i in range(http_count)]

        await asyncio.wait_for(all_connected.wait(), timeout=15.0)

        broadcast_time = time.monotonic()
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"http://127.0.0.1:{SERVER_PORT}/api/v1/test/broadcast")
            assert resp.status_code == 200

        done, pending = await asyncio.wait(tasks, timeout=BROADCAST_LATENCY_BUDGET + 5.0)

        for t in pending:
            t.cancel()
        if pending:
            await asyncio.gather(*pending, return_exceptions=True)

        assert len(done) == http_count, f"Only {len(done)}/{http_count} HTTP tasks completed"
        assert len(received_events) == http_count, f"Only {len(received_events)}/{http_count} received broadcast"

        max_latency = max(t - broadcast_time for t in received_events)
        assert max_latency < BROADCAST_LATENCY_BUDGET, (
            f"HTTP broadcast latency {max_latency:.3f}s exceeded {BROADCAST_LATENCY_BUDGET}s budget"
        )

    finally:
        server.should_exit = True
        server_thread.join(timeout=5.0)
