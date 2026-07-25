"""Initial schema + performance indexes

Revision ID: 0001_initial
Revises:
Create Date: 2026-07-25

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Performance indexes (idempotent — safe to run multiple times)
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_incidents_team_id ON incidents(team_id)",
        "CREATE INDEX IF NOT EXISTS idx_incidents_status ON incidents(status)",
        "CREATE INDEX IF NOT EXISTS idx_incidents_severity ON incidents(severity)",
        "CREATE INDEX IF NOT EXISTS idx_incidents_detected_at ON incidents(detected_at)",
        "CREATE INDEX IF NOT EXISTS idx_incidents_created_at ON incidents(created_at)",
        "CREATE INDEX IF NOT EXISTS idx_tasks_team_id ON tasks(team_id)",
        "CREATE INDEX IF NOT EXISTS idx_tasks_incident_id ON tasks(incident_id)",
        "CREATE INDEX IF NOT EXISTS idx_timeline_events_incident_id ON timeline_events(incident_id)",
        "CREATE INDEX IF NOT EXISTS idx_log_entries_team_id ON log_entries(team_id)",
        "CREATE INDEX IF NOT EXISTS idx_log_entries_level ON log_entries(level)",
        "CREATE INDEX IF NOT EXISTS idx_log_entries_created_at ON log_entries(created_at)",
        "CREATE INDEX IF NOT EXISTS idx_alerts_team_id ON alerts(team_id)",
        "CREATE INDEX IF NOT EXISTS idx_deployments_team_id ON deployments(team_id)",
        "CREATE INDEX IF NOT EXISTS idx_deployments_deployed_at ON deployments(deployed_at)",
        "CREATE INDEX IF NOT EXISTS idx_channels_team_id ON channels(team_id)",
        "CREATE INDEX IF NOT EXISTS idx_messages_channel_id ON messages(channel_id)",
        "CREATE INDEX IF NOT EXISTS idx_incidents_team_status_severity ON incidents(team_id, status, severity)",
        "CREATE INDEX IF NOT EXISTS idx_incidents_sla_cover ON incidents(team_id, status, detected_at, severity)",
    ]
    for stmt in indexes:
        op.execute(stmt)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_incidents_sla_cover")
    op.execute("DROP INDEX IF EXISTS idx_incidents_team_status_severity")
    op.execute("DROP INDEX IF EXISTS idx_messages_channel_id")
    op.execute("DROP INDEX IF EXISTS idx_channels_team_id")
    op.execute("DROP INDEX IF EXISTS idx_deployments_deployed_at")
    op.execute("DROP INDEX IF EXISTS idx_deployments_team_id")
    op.execute("DROP INDEX IF EXISTS idx_alerts_team_id")
    op.execute("DROP INDEX IF EXISTS idx_log_entries_created_at")
    op.execute("DROP INDEX IF EXISTS idx_log_entries_level")
    op.execute("DROP INDEX IF EXISTS idx_log_entries_team_id")
    op.execute("DROP INDEX IF EXISTS idx_timeline_events_incident_id")
    op.execute("DROP INDEX IF EXISTS idx_tasks_incident_id")
    op.execute("DROP INDEX IF EXISTS idx_tasks_team_id")
    op.execute("DROP INDEX IF EXISTS idx_incidents_created_at")
    op.execute("DROP INDEX IF EXISTS idx_incidents_detected_at")
    op.execute("DROP INDEX IF EXISTS idx_incidents_severity")
    op.execute("DROP INDEX IF EXISTS idx_incidents_status")
    op.execute("DROP INDEX IF EXISTS idx_incidents_team_id")