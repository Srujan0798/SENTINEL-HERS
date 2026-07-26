"""SSE + WebSocket realtime router.

SSE endpoint:  GET /api/realtime/events?token=<jwt>
WebSocket:     WS   /api/ws?token=<jwt>

Both require a valid JWT access token. The token carries team_id used for fan-out.
"""

import asyncio
import json
import logging
import time
from typing import Optional

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse

from ..auth.service import decode_access_token
from .hub import RealtimeHub, get_hub

logger = logging.getLogger(__name__)

router = APIRouter(tags=["realtime"])

SSE_RETRY_MS = 3000  # 3s reconnect hint


def _authenticate_token(token: str) -> dict:
    """Validate a JWT access token and return the identity needed for fan-out.

    Realtime connections only need team_id (fan-out scope) and user id, both of
    which are carried in the signed token — no DB round-trip per connection.
    """
    payload = decode_access_token(token)
    return {"id": payload["sub"], "team_id": payload["team_id"], "role": payload.get("role")}


@router.get("/realtime/events")
async def sse_events(
    token: str = Query("", description="JWT access token (fallback — prefer Authorization header)"),
    authorization: str = "",
):
    """SSE stream — pushes realtime events for the caller's team.

    Prefers Authorization: Bearer <token> header. Falls back to ?token= query param.
    """
    # Prefer Authorization header over query param to avoid token leakage in logs
    auth_token = token
    if authorization.startswith("Bearer "):
        auth_token = authorization[7:]
    user = _authenticate_token(auth_token)
    team_id = user["team_id"]
    hub = get_hub()
    await hub.initialize()

    entry = await hub.subscribe(team_id)

    async def event_generator():
        try:
            # Initial connection event
            yield f"event: connected\ndata: {json.dumps({'team_id': team_id, 'user_id': user['id']})}\n\n"

            while True:
                try:
                    event = await asyncio.wait_for(entry.queue.get(), timeout=30.0)
                    yield event.to_sse()
                except asyncio.TimeoutError:
                    # Send keepalive comment to prevent proxy timeouts
                    yield ": keepalive\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            await hub.unsubscribe(entry)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Retry": str(SSE_RETRY_MS),
        },
    )


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(..., description="JWT access token")):
    """WebSocket endpoint — bidirectional realtime for the caller's team."""
    try:
        user = _authenticate_token(token)
    except Exception:
        await websocket.close(code=4001, reason="Invalid token")
        return

    team_id = user["team_id"]
    hub = get_hub()
    await hub.initialize()

    await websocket.accept()
    entry = await hub.subscribe(team_id)

    try:
        # Send connection confirmation
        await websocket.send_json({"event_type": "connected", "payload": {"team_id": team_id, "user_id": user["id"]}})

        async def forward_events():
            while True:
                try:
                    event = await asyncio.wait_for(entry.queue.get(), timeout=30.0)
                    await websocket.send_json(event.to_dict())
                except asyncio.TimeoutError:
                    await websocket.send_json({"event_type": "ping", "payload": {}})
                except Exception:
                    break

        forward_task = asyncio.create_task(forward_events())

        try:
            while True:
                raw = await websocket.receive_text()
                try:
                    msg = json.loads(raw)
                    event_type = msg.get("event_type", "")
                    if event_type == "pong":
                        continue
                    # Only allow specific client-originated event types
                    allowed_client_events = {"channel:message", "typing", "pong"}
                    if event_type not in allowed_client_events:
                        logger.warning("WS client tried to publish disallowed event: %s", event_type)
                        await websocket.send_json({"event_type": "error", "payload": {"error": f"Event type '{event_type}' not allowed"}})
                        continue
                    await hub.publish(team_id, event_type, msg.get("payload", {}))
                except json.JSONDecodeError:
                    logger.warning("Invalid JSON from WS client: %s", raw[:200])
        finally:
            forward_task.cancel()
            try:
                await forward_task
            except asyncio.CancelledError:
                pass
    except WebSocketDisconnect:
        logger.debug("WS client disconnected (team=%s)", team_id)
    finally:
        await hub.unsubscribe(entry)
