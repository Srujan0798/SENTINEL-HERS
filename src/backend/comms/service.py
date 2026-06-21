"""Comms service — channel auto-creation, message persistence, mention parsing,
realtime fan-out."""
import logging
import re
import time
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.backend.realtime.hub import get_hub

from .models import Channel, ChannelMember, Message

logger = logging.getLogger(__name__)

_MENTION_RE = re.compile(r"@([a-zA-Z0-9_.\-]{1,64})")


class CommsError(Exception):
    pass


class ChannelNotFound(CommsError):
    pass


class IncidentNotFound(CommsError):
    pass


class CommsService:
    """Encapsulates channel + message persistence and realtime fan-out."""

    def __init__(self, db: Session):
        self.db = db

    def get_or_create_channel_for_incident(
        self,
        incident_id: str,
        team_id: str,
        incident_title: str = "Incident",
        actor: str = "system",
    ) -> Channel:
        """Auto-create a channel for an incident. Idempotent."""
        existing = (
            self.db.query(Channel)
            .filter(Channel.incident_id == str(incident_id))
            .first()
        )
        if existing:
            return existing

        channel = Channel(
            id=str(UUID(int=0)) if False else None,  # default kicks in
            team_id=str(team_id),
            incident_id=str(incident_id),
            name=f"#{incident_title[:80]}",
            topic=f"Incident {incident_id} — realtime coordination",
            is_archived="false",
        )
        self.db.add(channel)
        try:
            self.db.commit()
        except IntegrityError:
            # Race: another request created it. Roll back and re-fetch.
            self.db.rollback()
            existing = (
                self.db.query(Channel)
                .filter(Channel.incident_id == str(incident_id))
                .first()
            )
            if existing:
                return existing
            raise
        self.db.refresh(channel)
        logger.info("Auto-created channel %s for incident %s", channel.id, incident_id)
        return channel

    def add_channel_member(
        self,
        channel_id: str,
        team_id: str,
        user_id: str,
        user_name: Optional[str] = None,
        role: str = "member",
    ) -> ChannelMember:
        existing = (
            self.db.query(ChannelMember)
            .filter(
                ChannelMember.channel_id == str(channel_id),
                ChannelMember.user_id == str(user_id),
            )
            .first()
        )
        if existing:
            return existing
        member = ChannelMember(
            team_id=str(team_id),
            channel_id=str(channel_id),
            user_id=str(user_id),
            user_name=user_name,
            role=role,
        )
        self.db.add(member)
        self.db.commit()
        self.db.refresh(member)
        return member

    def _team_users(self, team_id: str) -> list[dict[str, Any]]:
        """Fetch active users for a team from the shared users table."""
        from src.backend.shared_models import UserModel

        rows = (
            self.db.query(UserModel)
            .filter(UserModel.team_id == str(team_id), UserModel.is_active == True)  # noqa: E712
            .all()
        )
        return [
            {"id": str(u.id), "name": u.name or "", "email": u.email or "", "role": u.role}
            for u in rows
        ]

    def list_channel_members(self, team_id: str) -> list[dict[str, Any]]:
        """Return all team members for @mention autocomplete."""
        try:
            return self._team_users(team_id)
        except Exception:
            return []

    def get_channel_for_incident(
        self, incident_id: str, team_id: str
    ) -> Channel:
        ch = (
            self.db.query(Channel)
            .filter(
                Channel.incident_id == str(incident_id),
                Channel.team_id == str(team_id),
            )
            .first()
        )
        if not ch:
            raise ChannelNotFound(f"No channel for incident {incident_id}")
        return ch

    def list_messages(
        self,
        channel_id: str,
        page: int = 1,
        per_page: int = 50,
    ) -> dict[str, Any]:
        total = (
            self.db.query(func.count(Message.id))
            .filter(Message.channel_id == str(channel_id))
            .scalar()
            or 0
        )
        total_pages = max(1, (total + per_page - 1) // per_page)
        rows = (
            self.db.query(Message)
            .filter(Message.channel_id == str(channel_id))
            .order_by(Message.created_at.asc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return {
            "data": [self._serialize_message(m) for m in rows],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": total_pages,
            },
        }

    def post_message(
        self,
        incident_id: str,
        team_id: str,
        author_id: Optional[str],
        author_name: Optional[str],
        body: str,
        author_type: str = "user",
        metadata: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Persist a message, parse @mentions, fan out via realtime hub."""
        if not body or not body.strip():
            raise CommsError("Message body cannot be empty")

        # Ensure channel exists (idempotent — covers legacy incidents).
        try:
            channel = self.get_channel_for_incident(incident_id, team_id)
        except ChannelNotFound:
            channel = self.get_or_create_channel_for_incident(
                incident_id=incident_id,
                team_id=team_id,
                incident_title=f"incident-{incident_id[:8]}",
            )

        mentions = self._parse_mentions(body, team_id)

        msg = Message(
            team_id=str(team_id),
            channel_id=str(channel.id),
            incident_id=str(incident_id),
            author_id=str(author_id) if author_id else None,
            author_name=author_name,
            author_type=author_type,
            body=body.strip(),
            mentions=[{"user_id": m["user_id"], "user_name": m["user_name"], "unresolved": m.get("unresolved", False)} for m in mentions],
            metadata_=metadata or {},
        )
        self.db.add(msg)
        self.db.commit()
        self.db.refresh(msg)

        serialized = self._serialize_message(msg)

        # Fan out via realtime hub — non-blocking best-effort.
        try:
            import asyncio

            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're inside a running loop (e.g. FastAPI). Schedule and don't block.
                asyncio.create_task(
                    self._publish(team_id, "channel.message", serialized)
                )
                for m in mentions:
                    asyncio.create_task(
                        self._publish(
                            team_id,
                            "mention.created",
                            {
                                "incident_id": str(incident_id),
                                "channel_id": str(channel.id),
                                "message_id": str(msg.id),
                                "mentioned_user_id": m["user_id"],
                                "mentioned_user_name": m["user_name"],
                                "by_user_id": str(author_id) if author_id else None,
                                "by_user_name": author_name,
                                "preview": body[:140],
                                "timestamp": time.time(),
                            },
                        )
                    )
            else:
                loop.run_until_complete(
                    self._publish(team_id, "channel.message", serialized)
                )
                for m in mentions:
                    loop.run_until_complete(
                        self._publish(
                            team_id,
                            "mention.created",
                            {
                                "incident_id": str(incident_id),
                                "channel_id": str(channel.id),
                                "message_id": str(msg.id),
                                "mentioned_user_id": m["user_id"],
                                "mentioned_user_name": m["user_name"],
                                "by_user_id": str(author_id) if author_id else None,
                                "by_user_name": author_name,
                                "preview": body[:140],
                                "timestamp": time.time(),
                            },
                        )
                    )
        except RuntimeError:
            # No event loop at all (sync test client). Publish synchronously.
            try:
                self._publish_sync(team_id, "channel.message", serialized)
                for m in mentions:
                    self._publish_sync(
                        team_id,
                        "mention.created",
                        {
                            "incident_id": str(incident_id),
                            "channel_id": str(channel.id),
                            "message_id": str(msg.id),
                            "mentioned_user_id": m["user_id"],
                            "mentioned_user_name": m["user_name"],
                            "by_user_id": str(author_id) if author_id else None,
                            "by_user_name": author_name,
                            "preview": body[:140],
                            "timestamp": time.time(),
                        },
                    )
            except Exception as exc:
                logger.warning("Realtime fan-out failed (non-fatal): %s", exc)
        except Exception as exc:
            logger.warning("Realtime fan-out failed (non-fatal): %s", exc)

        return serialized

    async def _publish(self, team_id: str, event_type: str, payload: dict[str, Any]):
        hub = get_hub()
        try:
            await hub.initialize()
        except Exception:
            pass
        await hub.publish(str(team_id), event_type, payload)

    def _publish_sync(self, team_id: str, event_type: str, payload: dict[str, Any]):
        """Synchronous fan-out for non-async test clients (TestClient)."""
        hub = get_hub()
        event = _SyncEvent(event_type=event_type, payload=payload, team_id=str(team_id))
        conns = hub._connections.get(str(team_id), [])
        for conn in conns:
            try:
                conn.queue.put_nowait(event)
            except Exception:
                pass

    def _parse_mentions(self, body: str, team_id: str) -> list[dict[str, Any]]:
        """Extract @user tokens. If a registered team member matches, return user_id."""
        names = [m.group(1) for m in _MENTION_RE.finditer(body or "")]
        if not names:
            return []

        # Look up by name/email against the shared users table.
        try:
            users = self._team_users(team_id)
            by_email = {
                u["email"].split("@")[0].lower(): u for u in users if u.get("email")
            }
            by_name: dict[str, dict] = {}
            for u in users:
                full = (u.get("name") or "").lower().replace(" ", "")
                first = (u.get("name") or "").split()[0].lower() if u.get("name") else ""
                if full:
                    by_name[full] = u
                if first:
                    by_name.setdefault(first, u)
        except Exception:
            by_email, by_name = {}, {}

        resolved: list[dict[str, Any]] = []
        seen: set[str] = set()
        for raw in names:
            key = raw.lower()
            user = by_email.get(key) or by_name.get(key)
            if not user:
                # Allow mentions of names that aren't resolvable — still surface them.
                resolved.append({"user_id": f"@{raw}", "user_name": raw, "unresolved": True})
                continue
            uid = str(user["id"])
            if uid in seen:
                continue
            seen.add(uid)
            resolved.append(
                {"user_id": uid, "user_name": user.get("name") or raw, "unresolved": False}
            )
        return resolved

    def _serialize_message(self, m: Message) -> dict[str, Any]:
        return {
            "id": str(m.id),
            "team_id": str(m.team_id),
            "channel_id": str(m.channel_id),
            "incident_id": str(m.incident_id),
            "author_id": str(m.author_id) if m.author_id else None,
            "author_name": m.author_name,
            "author_type": m.author_type,
            "body": m.body,
            "mentions": m.mentions or [],
            "metadata": m.metadata_ or {},
            "created_at": m.created_at.isoformat() if m.created_at else None,
            "edited_at": m.edited_at.isoformat() if m.edited_at else None,
        }

    def serialize_channel(self, ch: Channel) -> dict[str, Any]:
        members = (
            self.db.query(func.count(ChannelMember.id))
            .filter(ChannelMember.channel_id == str(ch.id))
            .scalar()
            or 0
        )
        messages = (
            self.db.query(func.count(Message.id))
            .filter(Message.channel_id == str(ch.id))
            .scalar()
            or 0
        )
        return {
            "id": str(ch.id),
            "team_id": str(ch.team_id),
            "incident_id": str(ch.incident_id),
            "name": ch.name,
            "topic": ch.topic,
            "is_archived": ch.is_archived == "true",
            "created_at": ch.created_at.isoformat() if ch.created_at else None,
            "updated_at": ch.updated_at.isoformat() if ch.updated_at else None,
            "member_count": int(members),
            "message_count": int(messages),
        }


class _SyncEvent:
    """Minimal stand-in for RealtimeEvent that the in-memory hub can enqueue
    synchronously. We rely on duck-typing: the hub checks for .to_sse() and
    .to_dict() — we just need .event_type, .payload, .team_id, .timestamp."""

    __slots__ = ("event_type", "payload", "team_id", "timestamp")

    def __init__(self, event_type: str, payload: dict[str, Any], team_id: str):
        self.event_type = event_type
        self.payload = payload
        self.team_id = team_id
        self.timestamp = time.time()

    def to_sse(self) -> str:
        import json
        data = json.dumps(
            {
                "event_type": self.event_type,
                "payload": self.payload,
                "team_id": self.team_id,
                "timestamp": self.timestamp,
            }
        )
        return f"event: {self.event_type}\ndata: {data}\n\n"

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_type": self.event_type,
            "payload": self.payload,
            "team_id": self.team_id,
            "timestamp": self.timestamp,
        }
