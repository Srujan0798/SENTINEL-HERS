# ERD — SENTINEL Data Model

## Entity Relationship Diagram

```mermaid
erDiagram
    %% ─────────────────────────────────────────────
    %% Teams & Auth
    %% ─────────────────────────────────────────────
    teams {
        uuid id PK
        varchar name UK
        varchar slug UK
        text description
        jsonb settings
        timestamp created_at
        timestamp updated_at
    }

    roles {
        uuid id PK
        varchar name UK
        jsonb permissions
        text description
        timestamp created_at
    }

    users {
        uuid id PK
        uuid team_id FK
        varchar email UK
        varchar password_hash
        varchar name
        text avatar_url
        uuid role_id FK
        boolean is_active
        timestamp last_login_at
        timestamp created_at
        timestamp updated_at
    }

    %% ─────────────────────────────────────────────
    %% Incidents
    %% ─────────────────────────────────────────────
    incidents {
        uuid id PK
        uuid team_id FK
        varchar title
        text description
        severity_level severity
        incident_status status
        uuid assigned_to FK
        uuid escalated_to FK
        timestamp detected_at
        timestamp triaged_at
        timestamp resolved_at
        timestamp closed_at
        text root_cause
        text ai_summary
        jsonb ai_root_cause_ranking
        jsonb metadata
        timestamp created_at
        timestamp updated_at
    }

    %% ─────────────────────────────────────────────
    %% Logs & Alerts
    %% ─────────────────────────────────────────────
    log_entries {
        uuid id PK
        uuid team_id FK
        uuid incident_id FK
        varchar service
        log_level level
        text message
        jsonb metadata
        inet source_ip
        jsonb raw_payload
        timestamp indexed_at
        timestamp created_at
    }

    alerts {
        uuid id PK
        uuid team_id FK
        uuid incident_id FK
        varchar source
        varchar alert_type
        varchar title
        text description
        severity_level severity
        boolean is_resolved
        timestamp resolved_at
        uuid resolved_by FK
        jsonb metadata
        timestamp fired_at
        timestamp created_at
    }

    %% ─────────────────────────────────────────────
    %% Service Health
    %% ─────────────────────────────────────────────
    service_health {
        uuid id PK
        uuid team_id FK
        varchar service_name
        health_status status
        decimal uptime_percentage
        int latency_ms
        timestamp last_check_at
        timestamp next_check_at
        jsonb metadata
        timestamp created_at
        timestamp updated_at
    }

    %% ─────────────────────────────────────────────
    %% Deployments & Commits
    %% ─────────────────────────────────────────────
    deployments {
        uuid id PK
        uuid team_id FK
        varchar service
        varchar version
        varchar environment
        deploy_status status
        uuid deployed_by FK
        timestamp started_at
        timestamp completed_at
        timestamp rollback_at
        uuid commit_id FK
        jsonb metadata
        timestamp created_at
        timestamp updated_at
    }

    commits {
        uuid id PK
        uuid team_id FK
        uuid deployment_id FK
        varchar sha
        text message
        varchar author
        varchar author_email
        varchar branch
        varchar repository
        timestamp committed_at
        jsonb metadata
        timestamp created_at
    }

    %% ─────────────────────────────────────────────
    %% Timeline Events (Provenance)
    %% ─────────────────────────────────────────────
    timeline_events {
        uuid id PK
        uuid incident_id FK
        varchar event_type
        varchar source
        varchar actor
        timestamp ts
        varchar payload_ref
        text description
        jsonb metadata
        timestamp created_at
    }

    %% ─────────────────────────────────────────────
    %% Tasks & SLA
    %% ─────────────────────────────────────────────
    tasks {
        uuid id PK
        uuid incident_id FK
        uuid assigned_to FK
        varchar title
        text description
        task_status status
        int priority
        timestamp due_at
        timestamp completed_at
        uuid completed_by FK
        jsonb metadata
        timestamp created_at
        timestamp updated_at
    }

    slas {
        uuid id PK
        uuid team_id FK
        uuid incident_id FK
        severity_level severity
        int target_minutes
        int elapsed_minutes
        boolean is_breached
        timestamp breached_at
        timestamp started_at
        timestamp paused_at
        jsonb metadata
        timestamp created_at
        timestamp updated_at
    }

    %% ─────────────────────────────────────────────
    %% Channels & Messages
    %% ─────────────────────────────────────────────
    channels {
        uuid id PK
        uuid incident_id FK
        uuid team_id FK
        varchar name
        varchar channel_type
        boolean is_archived
        jsonb metadata
        timestamp created_at
        timestamp updated_at
    }

    messages {
        uuid id PK
        uuid channel_id FK
        uuid user_id FK
        text content
        varchar message_type
        boolean is_ai_generated
        varchar ai_provider
        jsonb metadata
        timestamp created_at
    }

    %% ─────────────────────────────────────────────
    %% Anomaly Scores
    %% ─────────────────────────────────────────────
    anomaly_scores {
        uuid id PK
        uuid team_id FK
        varchar service
        varchar metric_name
        decimal score
        decimal threshold
        boolean is_anomaly
        timestamp detected_at
        uuid incident_id FK
        jsonb metadata
        timestamp created_at
    }

    %% ─────────────────────────────────────────────
    %% Relationships
    %% ─────────────────────────────────────────────
    teams ||--o{ users : "has"
    teams ||--o{ incidents : "owns"
    teams ||--o{ log_entries : "contains"
    teams ||--o{ alerts : "receives"
    teams ||--o{ service_health : "monitors"
    teams ||--o{ deployments : "has"
    teams ||--o{ commits : "has"
    teams ||--o{ slas : "defines"
    teams ||--o{ channels : "has"
    teams ||--o{ anomaly_scores : "tracks"

    roles ||--o{ users : "assigned_to"

    users ||--o{ incidents : "assigned"
    users ||--o{ incidents : "escalated_to"
    users ||--o{ tasks : "assigned"
    users ||--o{ tasks : "completed"
    users ||--o{ alerts : "resolved"
    users ||--o{ deployments : "deployed"
    users ||--o{ messages : "sent"

    incidents ||--o{ log_entries : "generates"
    incidents ||--o{ alerts : "triggers"
    incidents ||--o{ timeline_events : "records"
    incidents ||--o{ tasks : "requires"
    incidents ||--o{ slas : "governed_by"
    incidents ||--o{ channels : "discussed_in"
    incidents ||--o{ anomaly_scores : "detected_by"

    deployments }o--o| commits : "includes"
    commits }o--o| deployments : "part_of"

    channels ||--o{ messages : "contains"
```

## Enums

| Enum | Values |
|------|--------|
| severity_level | SEV1, SEV2, SEV3, SEV4 |
| incident_status | detected, triaging, investigating, mitigating, resolved, closed |
| log_level | debug, info, warn, error, fatal |
| health_status | healthy, degraded, down, unknown |
| deploy_status | pending, in_progress, success, failed, rolled_back |
| task_status | pending, in_progress, blocked, completed, cancelled |

## Key Design Decisions

1. **UUID Primary Keys**: All entities use UUID for distributed system compatibility
2. **Provenance Columns**: `source`, `actor`, `ts` on TimelineEvent for immutable audit trail
3. **Soft References**: Some FKs use SET NULL to preserve data when references are deleted
4. **JSONB Metadata**: Flexible schema extension without migrations
5. **Timestamps**: All entities have `created_at`; mutable entities have `updated_at` with auto-trigger
6. **Team Scoping**: All data is scoped to teams for multi-tenant isolation
7. **Full-Text Search**: pg_trgm extension on log_entries.message for efficient text search

## Indexes

- All foreign keys are indexed
- Time-based queries optimized with DESC indexes on timestamps
- Text search enabled with trigram indexes
- Status fields indexed for filtering
