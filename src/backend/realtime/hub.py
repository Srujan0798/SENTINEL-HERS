"""Realtime hub — Redis pub/sub fan-out with in-memory fallback for tests."""

import asyncio
import json
import logging
import os
import time
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "")


class RealtimeEvent:
    """A single realtime event pushed to clients."""

    __slots__ = ("event_type", "payload", "team_id", "timestamp")

    def __init__(self, event_type: str, payload: dict[str, Any], team_id: str, timestamp: float | None = None):
        self.event_type = event_type
        self.payload = payload
        self.team_id = team_id
        self.timestamp = timestamp or time.time()

    def to_sse(self) -> str:
        data = json.dumps({"event_type": self.event_type, "payload": self.payload, "team_id": self.team_id, "timestamp": self.timestamp})
        return f"event: {self.event_type}\ndata: {data}\n\n"

    def to_dict(self) -> dict[str, Any]:
        return {"event_type": self.event_type, "payload": self.payload, "team_id": self.team_id, "timestamp": self.timestamp}


class ConnectionEntry:
    """One connected SSE/WS client."""

    __slots__ = ("queue", "team_id", "user_id", "connected_at")

    def __init__(self, team_id: str, user_id: str):
        self.queue: asyncio.Queue[RealtimeEvent] = asyncio.Queue()
        self.team_id = team_id
        self.user_id = user_id
        self.connected_at = time.time()


class RealtimeHub:
    """Manages client connections and broadcasts events via Redis pub/sub or in-memory."""

    def __init__(self, use_redis: bool = False, redis_url: str = ""):
        self._use_redis = use_redis
        self._redis_url = redis_url or REDIS_URL
        self._connections: dict[str, list[ConnectionEntry]] = {}  # team_id -> [connections]
        self._redis = None
        self._pubsub = None
        self._listener_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
        self._initialized = False

    async def initialize(self):
        """Initialize Redis connection if available."""
        if self._initialized:
            return
        self._initialized = True

        if self._use_redis and self._redis_url:
            try:
                import redis.asyncio as aioredis

                self._redis = aioredis.from_url(self._redis_url, decode_responses=True)
                await self._redis.ping()
                self._pubsub = self._redis.pubsub()
                logger.info("RealtimeHub connected to Redis at %s", self._redis_url)
            except Exception:
                logger.warning("Redis unavailable — falling back to in-memory fan-out")
                self._redis = None
                self._pubsub = None
                self._use_redis = False

    async def shutdown(self):
        """Clean up resources."""
        if self._listener_task and not self._listener_task.done():
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass
        if self._pubsub:
            await self._pubsub.unsubscribe()
        if self._redis:
            await self._redis.close()

    async def subscribe(self, team_id: str) -> ConnectionEntry:
        """Register a new connection for a team and return its entry."""
        async with self._lock:
            entry = ConnectionEntry(team_id=team_id, user_id="")
            self._connections.setdefault(team_id, []).append(entry)

            if self._redis and self._pubsub:
                channel = f"team:{team_id}"
                await self._pubsub.subscribe(channel)
                if not self._listener_task:
                    self._listener_task = asyncio.create_task(self._redis_listener())

            logger.debug("Client subscribed to team %s (total: %d)", team_id, self.connection_count)
            return entry

    async def unsubscribe(self, entry: ConnectionEntry):
        """Remove a connection."""
        async with self._lock:
            conns = self._connections.get(entry.team_id, [])
            if entry in conns:
                conns.remove(entry)
            if not conns and entry.team_id in self._connections:
                del self._connections[entry.team_id]
        logger.debug("Client unsubscribed from team %s", entry.team_id)

    async def publish(self, team_id: str, event_type: str, payload: dict[str, Any]):
        """Broadcast an event to all connected clients of a team.

        Fans out to both Redis pub/sub (cross-worker) AND local in-memory
        connections (same-worker) so every client receives the event exactly once.
        """
        event = RealtimeEvent(event_type=event_type, payload=payload, team_id=team_id)

        if self._redis:
            channel = f"team:{team_id}"
            message = json.dumps(event.to_dict())
            await self._redis.publish(channel, message)

        # Always fan-out to local connections (even when Redis is active)
        conns = self._connections.get(team_id, [])
        for conn in conns:
            try:
                conn.queue.put_nowait(event)
            except asyncio.QueueFull:
                logger.warning("Dropping event for full queue (user=%s)", conn.user_id)

    async def _on_redis_message(self, message: dict):
        """Handle incoming Redis pub/sub message."""
        if message["type"] != "message":
            return
        try:
            data = json.loads(message["data"])
            event = RealtimeEvent(
                event_type=data["event_type"],
                payload=data["payload"],
                team_id=data["team_id"],
                timestamp=data.get("timestamp"),
            )
            conns = self._connections.get(event.team_id, [])
            for conn in conns:
                try:
                    conn.queue.put_nowait(event)
                except asyncio.QueueFull:
                    logger.warning("Dropping event for full queue (user=%s)", conn.user_id)
        except (json.JSONDecodeError, KeyError) as exc:
            logger.error("Failed to decode Redis message: %s", exc)

    async def _redis_listener(self):
        """Background task that reads from Redis pub/sub."""
        try:
            while self._pubsub:
                message = await self._pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message:
                    await self._on_redis_message(message)
                await asyncio.sleep(0.01)
        except asyncio.CancelledError:
            pass
        except Exception:
            logger.exception("Redis listener crashed")

    @property
    def connection_count(self) -> int:
        return sum(len(c) for c in self._connections.values())

    def team_connection_count(self, team_id: str) -> int:
        return len(self._connections.get(team_id, []))


# Singleton hub instance
_hub: Optional[RealtimeHub] = None


def get_hub() -> RealtimeHub:
    """Get or create the global hub singleton."""
    global _hub
    if _hub is None:
        use_redis = bool(REDIS_URL)
        _hub = RealtimeHub(use_redis=use_redis)
    return _hub
