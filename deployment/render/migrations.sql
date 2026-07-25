-- SENTINEL — Production migration script (idempotent)
-- Run on deploy via deployment/render/release.sh or manually.
-- Safe to run multiple times — all statements use IF NOT EXISTS.

BEGIN;

-- Performance indexes (the biggest system-design win)
CREATE INDEX IF NOT EXISTS idx_incidents_team_id ON incidents(team_id);
CREATE INDEX IF NOT EXISTS idx_incidents_status ON incidents(status);
CREATE INDEX IF NOT EXISTS idx_incidents_severity ON incidents(severity);
CREATE INDEX IF NOT EXISTS idx_incidents_detected_at ON incidents(detected_at);
CREATE INDEX IF NOT EXISTS idx_incidents_created_at ON incidents(created_at);
CREATE INDEX IF NOT EXISTS idx_tasks_team_id ON tasks(team_id);
CREATE INDEX IF NOT EXISTS idx_tasks_incident_id ON tasks(incident_id);
CREATE INDEX IF NOT EXISTS idx_timeline_events_incident_id ON timeline_events(incident_id);
CREATE INDEX IF NOT EXISTS idx_log_entries_team_id ON log_entries(team_id);
CREATE INDEX IF NOT EXISTS idx_log_entries_level ON log_entries(level);
CREATE INDEX IF NOT EXISTS idx_log_entries_created_at ON log_entries(created_at);
CREATE INDEX IF NOT EXISTS idx_alerts_team_id ON alerts(team_id);
CREATE INDEX IF NOT EXISTS idx_deployments_team_id ON deployments(team_id);
CREATE INDEX IF NOT EXISTS idx_deployments_deployed_at ON deployments(deployed_at);
CREATE INDEX IF NOT EXISTS idx_channels_team_id ON channels(team_id);
CREATE INDEX IF NOT EXISTS idx_messages_channel_id ON messages(channel_id);

-- Composite index for the most common query: team + status + severity
CREATE INDEX IF NOT EXISTS idx_incidents_team_status_severity
  ON incidents(team_id, status, severity);

-- Covering index for SLA queries
CREATE INDEX IF NOT EXISTS idx_incidents_sla_cover
  ON incidents(team_id, status, detected_at, severity);

COMMIT;