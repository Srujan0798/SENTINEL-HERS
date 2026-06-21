-- SENTINEL — Initial Schema Migration
-- Wave 0 / Task 01: Canonical Data Model
-- Source of truth for all entities (FM-05, FM-12)

-- ============================================================================
-- EXTENSIONS
-- ============================================================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search

-- ============================================================================
-- TEAMS & AUTH
-- ============================================================================

CREATE TABLE teams (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL UNIQUE,
    slug VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    permissions JSONB NOT NULL DEFAULT '[]',
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    avatar_url TEXT,
    role_id UUID NOT NULL REFERENCES roles(id),
    is_active BOOLEAN NOT NULL DEFAULT true,
    last_login_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_team_id ON users(team_id);
CREATE INDEX idx_users_email ON users(email);

-- ============================================================================
-- INCIDENTS
-- ============================================================================

CREATE TYPE severity_level AS ENUM ('SEV1', 'SEV2', 'SEV3', 'SEV4');

CREATE TYPE incident_status AS ENUM (
    'detected', 'triaging', 'investigating', 'mitigating', 'resolved', 'closed'
);

CREATE TABLE incidents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    severity severity_level NOT NULL DEFAULT 'SEV3',
    status incident_status NOT NULL DEFAULT 'detected',
    assigned_to UUID REFERENCES users(id),
    escalated_to UUID REFERENCES users(id),
    detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    triaged_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ,
    closed_at TIMESTAMPTZ,
    root_cause TEXT,
    ai_summary TEXT,
    ai_root_cause_ranking JSONB,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_incidents_team_id ON incidents(team_id);
CREATE INDEX idx_incidents_status ON incidents(status);
CREATE INDEX idx_incidents_severity ON incidents(severity);
CREATE INDEX idx_incidents_assigned_to ON incidents(assigned_to);
CREATE INDEX idx_incidents_detected_at ON incidents(detected_at DESC);

-- ============================================================================
-- LOGS & ALERTS
-- ============================================================================

CREATE TYPE log_level AS ENUM ('debug', 'info', 'warn', 'error', 'fatal');

CREATE TABLE log_entries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    incident_id UUID REFERENCES incidents(id) ON DELETE SET NULL,
    service VARCHAR(255) NOT NULL,
    level log_level NOT NULL DEFAULT 'info',
    message TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    source_ip INET,
    raw_payload JSONB,
    indexed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_log_entries_team_id ON log_entries(team_id);
CREATE INDEX idx_log_entries_incident_id ON log_entries(incident_id);
CREATE INDEX idx_log_entries_service ON log_entries(service);
CREATE INDEX idx_log_entries_level ON log_entries(level);
CREATE INDEX idx_log_entries_indexed_at ON log_entries(indexed_at DESC);
CREATE INDEX idx_log_entries_message_trgm ON log_entries USING gin(message gin_trgm_ops);

CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    incident_id UUID REFERENCES incidents(id) ON DELETE SET NULL,
    source VARCHAR(255) NOT NULL,
    alert_type VARCHAR(100) NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    severity severity_level NOT NULL DEFAULT 'SEV3',
    is_resolved BOOLEAN NOT NULL DEFAULT false,
    resolved_at TIMESTAMPTZ,
    resolved_by UUID REFERENCES users(id),
    metadata JSONB DEFAULT '{}',
    fired_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_alerts_team_id ON alerts(team_id);
CREATE INDEX idx_alerts_incident_id ON alerts(incident_id);
CREATE INDEX idx_alerts_is_resolved ON alerts(is_resolved);
CREATE INDEX idx_alerts_fired_at ON alerts(fired_at DESC);

-- ============================================================================
-- SERVICE HEALTH
-- ============================================================================

CREATE TYPE health_status AS ENUM ('healthy', 'degraded', 'down', 'unknown');

CREATE TABLE service_health (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    service_name VARCHAR(255) NOT NULL,
    status health_status NOT NULL DEFAULT 'unknown',
    uptime_percentage DECIMAL(5,2),
    latency_ms INTEGER,
    last_check_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    next_check_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(team_id, service_name)
);

CREATE INDEX idx_service_health_team_id ON service_health(team_id);
CREATE INDEX idx_service_health_status ON service_health(status);

-- ============================================================================
-- DEPLOYMENTS & COMMITS
-- ============================================================================

CREATE TYPE deploy_status AS ENUM ('pending', 'in_progress', 'success', 'failed', 'rolled_back');

CREATE TABLE deployments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    service VARCHAR(255) NOT NULL,
    version VARCHAR(255) NOT NULL,
    environment VARCHAR(100) NOT NULL DEFAULT 'production',
    status deploy_status NOT NULL DEFAULT 'pending',
    deployed_by UUID REFERENCES users(id),
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    rollback_at TIMESTAMPTZ,
    commit_id UUID,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_deployments_team_id ON deployments(team_id);
CREATE INDEX idx_deployments_service ON deployments(service);
CREATE INDEX idx_deployments_status ON deployments(status);
CREATE INDEX idx_deployments_started_at ON deployments(started_at DESC);

CREATE TABLE commits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    deployment_id UUID REFERENCES deployments(id) ON DELETE SET NULL,
    sha VARCHAR(40) NOT NULL,
    message TEXT NOT NULL,
    author VARCHAR(255) NOT NULL,
    author_email VARCHAR(255),
    branch VARCHAR(255) NOT NULL DEFAULT 'main',
    repository VARCHAR(500) NOT NULL,
    committed_at TIMESTAMPTZ NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(team_id, sha)
);

CREATE INDEX idx_commits_team_id ON commits(team_id);
CREATE INDEX idx_commits_deployment_id ON commits(deployment_id);
CREATE INDEX idx_commits_sha ON commits(sha);
CREATE INDEX idx_commits_committed_at ON commits(committed_at DESC);

-- Add FK from deployments to commits
ALTER TABLE deployments ADD CONSTRAINT fk_deployments_commit_id
    FOREIGN KEY (commit_id) REFERENCES commits(id) ON DELETE SET NULL;

-- ============================================================================
-- TIMELINE EVENTS (Provenance — FM-11)
-- ============================================================================

CREATE TABLE timeline_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    incident_id UUID NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
    event_type VARCHAR(100) NOT NULL,
    source VARCHAR(255) NOT NULL,
    actor VARCHAR(255) NOT NULL,
    ts TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    payload_ref VARCHAR(500),
    description TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_timeline_events_incident_id ON timeline_events(incident_id);
CREATE INDEX idx_timeline_events_ts ON timeline_events(ts DESC);
CREATE INDEX idx_timeline_events_event_type ON timeline_events(event_type);

-- ============================================================================
-- TASKS & SLA
-- ============================================================================

CREATE TYPE task_status AS ENUM ('pending', 'in_progress', 'blocked', 'completed', 'cancelled');

CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    incident_id UUID NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
    assigned_to UUID REFERENCES users(id),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    status task_status NOT NULL DEFAULT 'pending',
    priority INTEGER NOT NULL DEFAULT 3,
    due_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    completed_by UUID REFERENCES users(id),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_tasks_incident_id ON tasks(incident_id);
CREATE INDEX idx_tasks_assigned_to ON tasks(assigned_to);
CREATE INDEX idx_tasks_status ON tasks(status);

CREATE TABLE slas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    incident_id UUID NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
    severity severity_level NOT NULL,
    target_minutes INTEGER NOT NULL,
    elapsed_minutes INTEGER NOT NULL DEFAULT 0,
    is_breached BOOLEAN NOT NULL DEFAULT false,
    breached_at TIMESTAMPTZ,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    paused_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_slas_team_id ON slas(team_id);
CREATE INDEX idx_slas_incident_id ON slas(incident_id);
CREATE INDEX idx_slas_is_breached ON slas(is_breached);

-- ============================================================================
-- CHANNELS & MESSAGES
-- ============================================================================

CREATE TABLE channels (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    incident_id UUID NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    channel_type VARCHAR(50) NOT NULL DEFAULT 'incident',
    is_archived BOOLEAN NOT NULL DEFAULT false,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_channels_incident_id ON channels(incident_id);
CREATE INDEX idx_channels_team_id ON channels(team_id);

CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    channel_id UUID NOT NULL REFERENCES channels(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id),
    content TEXT NOT NULL,
    message_type VARCHAR(50) NOT NULL DEFAULT 'text',
    is_ai_generated BOOLEAN NOT NULL DEFAULT false,
    ai_provider VARCHAR(50),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_messages_channel_id ON messages(channel_id);
CREATE INDEX idx_messages_user_id ON messages(user_id);
CREATE INDEX idx_messages_created_at ON messages(created_at DESC);

-- ============================================================================
-- ANOMALY SCORES
-- ============================================================================

CREATE TABLE anomaly_scores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    service VARCHAR(255) NOT NULL,
    metric_name VARCHAR(255) NOT NULL,
    score DECIMAL(10,4) NOT NULL,
    threshold DECIMAL(10,4) NOT NULL,
    is_anomaly BOOLEAN NOT NULL DEFAULT false,
    detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    incident_id UUID REFERENCES incidents(id) ON DELETE SET NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_anomaly_scores_team_id ON anomaly_scores(team_id);
CREATE INDEX idx_anomaly_scores_service ON anomaly_scores(service);
CREATE INDEX idx_anomaly_scores_is_anomaly ON anomaly_scores(is_anomaly);
CREATE INDEX idx_anomaly_scores_detected_at ON anomaly_scores(detected_at DESC);

-- ============================================================================
-- UPDATED_AT TRIGGER
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_teams_updated_at BEFORE UPDATE ON teams
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_incidents_updated_at BEFORE UPDATE ON incidents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_service_health_updated_at BEFORE UPDATE ON service_health
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_deployments_updated_at BEFORE UPDATE ON deployments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tasks_updated_at BEFORE UPDATE ON tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_slas_updated_at BEFORE UPDATE ON slas
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_channels_updated_at BEFORE UPDATE ON channels
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- SEED DEFAULT ROLES
-- ============================================================================

INSERT INTO roles (name, permissions, description) VALUES
    ('admin', '["*"]', 'Full system access'),
    ('incident_commander', '["incidents:*", "tasks:*", "channels:*", "sla:*"]', 'Lead incident response'),
    ('responder', '["incidents:read", "incidents:update", "tasks:read", "tasks:update", "channels:read", "channels:write"]', 'Respond to incidents'),
    ('viewer', '["*:read"]', 'Read-only access');
