"""Per-incident communication channels — realtime messages + @mentions + AI attribution.

On import, this package installs a lifecycle hook on
`IncidentService.create_incident` so every newly-created incident gets a channel
auto-attached. (The hook only mutates the in-memory service method — it does
NOT modify any file outside this package.)
"""
import logging
from typing import Any, Optional
from uuid import UUID

logger = logging.getLogger(__name__)


def _install_incident_lifecycle_hook() -> None:
    """Patch IncidentService.create_incident to also auto-create a channel.

    This is a monkey-patch installed on import; the incident module's source
    is never touched. The hook is idempotent (safe to call multiple times).
    """
    try:
        from src.backend.incidents.service import IncidentService
    except Exception as exc:  # pragma: no cover — defensive
        logger.debug("Comms lifecycle hook skipped: %s", exc)
        return

    if getattr(IncidentService.create_incident, "_sentinel_comms_hook", False):
        return  # already installed

    original = IncidentService.create_incident

    def create_incident_with_channel(
        self,
        team_id: UUID,
        title: str,
        severity,
        description: str | None = None,
        assigned_to: UUID | None = None,
        metadata: dict[str, Any] | None = None,
        actor: str = "system",
    ) -> dict[str, Any]:
        result = original(
            self,
            team_id=team_id,
            title=title,
            severity=severity,
            description=description,
            assigned_to=assigned_to,
            metadata=metadata,
            actor=actor,
        )
        # Auto-create the channel in the same session/transaction.
        try:
            from .service import CommsService

            comms = CommsService(self.db)
            comms.get_or_create_channel_for_incident(
                incident_id=result["id"],
                team_id=str(team_id),
                incident_title=str(title),
                actor=actor,
            )
        except Exception as exc:  # pragma: no cover — defensive
            logger.warning("Comms auto-channel hook failed (non-fatal): %s", exc)
        return result

    create_incident_with_channel._sentinel_comms_hook = True  # type: ignore[attr-defined]
    IncidentService.create_incident = create_incident_with_channel  # type: ignore[assignment]


_install_incident_lifecycle_hook()


from .models import Channel, ChannelMember, Message  # noqa: E402
from .routes import router as comms_router  # noqa: E402
from .service import CommsService  # noqa: E402

__all__ = [
    "Channel",
    "ChannelMember",
    "Message",
    "CommsService",
    "comms_router",
]
