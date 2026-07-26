"""Database indexes for performance optimization."""

from sqlalchemy import Index, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

Base = declarative_base()

def create_performance_indexes(db: Session) -> None:
    """Create all performance indexes for the database."""
    
    # Log entries indexes
    log_entries_indexes = [
        # Composite index for team + created_at (most common query pattern)
        Index('ix_log_entries_team_created', 'team_id', 'created_at'),
        
        # Composite index for team + service + level (filtering)
        Index('ix_log_entries_team_service_level', 'team_id', 'service', 'level'),
        
        # Index for incident_id (join operations)
        Index('ix_log_entries_incident_id', 'incident_id'),
        
        # Index for service (service-specific queries)
        Index('ix_log_entries_service', 'service'),
        
        # Index for level (level-based queries)
        Index('ix_log_entries_level', 'level'),
        
        # Index for created_at (time-based queries)
        Index('ix_log_entries_created_at', 'created_at'),
        
        # Full text search index (if supported)
        text('CREATE INDEX IF NOT EXISTS ix_log_entries_message_search ON log_entries USING gin(to_tsvector(\'english\', message))')
    ]
    
    # Incidents indexes
    incidents_indexes = [
        # Composite index for team + created_at (most common query pattern)
        Index('ix_incidents_team_created', 'team_id', 'created_at'),
        
        # Composite index for team + severity (severity-based queries)
        Index('ix_incidents_team_severity', 'team_id', 'severity'),
        
        # Composite index for team + status (status-based queries)
        Index('ix_incidents_team_status', 'team_id', 'status'),
        
        # Index for severity (severity-based queries)
        Index('ix_incidents_severity', 'severity'),
        
        # Index for status (status-based queries)
        Index('ix_incidents_status', 'status'),
        
        # Index for assigned_to (assignment queries)
        Index('ix_incidents_assigned_to', 'assigned_to'),
        
        # Index for escalated_to (escalation queries)
        Index('ix_incidents_escalated_to', 'escalated_to'),
        
        # Index for resolved_at (resolution time queries)
        Index('ix_incidents_resolved_at', 'resolved_at'),
        
        # Index for created_at (time-based queries)
        Index('ix_incidents_created_at', 'created_at')
    ]
    
    # Users indexes
    users_indexes = [
        # Index for username (authentication)
        Index('ix_users_username', 'username', unique=True),
        
        # Index for email (authentication)
        Index('ix_users_email', 'email', unique=True),
        
        # Composite index for team + role (team management)
        Index('ix_users_team_role', 'team_id', 'role_id'),
        
        # Index for team_id (team-based queries)
        Index('ix_users_team_id', 'team_id'),
        
        # Index for role_id (role-based queries)
        Index('ix_users_role_id', 'role_id'),
        
        # Index for is_active (active user queries)
        Index('ix_users_is_active', 'is_active'),
        
        # Index for last_login_at (activity tracking)
        Index('ix_users_last_login_at', 'last_login_at')
    ]
    
    # Teams indexes
    teams_indexes = [
        # Index for name (team lookup)
        Index('ix_teams_name', 'name', unique=True),
        
        # Index for created_at (team creation queries)
        Index('ix_teams_created_at', 'created_at')
    ]
    
    # Roles indexes
    roles_indexes = [
        # Index for name (role lookup)
        Index('ix_roles_name', 'name', unique=True),
        
        # Index for permissions (permission-based queries)
        Index('ix_roles_permissions', 'permissions')
    ]
    
    # Apply indexes
    for index in log_entries_indexes:
        if isinstance(index, Index):
            db.execute(index)
    
    for index in incidents_indexes:
        if isinstance(index, Index):
            db.execute(index)
    
    for index in users_indexes:
        if isinstance(index, Index):
            db.execute(index)
    
    for index in teams_indexes:
        if isinstance(index, Index):
            db.execute(index)
    
    for index in roles_indexes:
        if isinstance(index, Index):
            db.execute(index)
    
    # Commit the indexes
    db.commit()
    
    print("Performance indexes created successfully")

def create_analytical_indexes(db: Session) -> None:
    """Create analytical indexes for reporting and analytics."""
    
    analytical_indexes = [
        # Time series indexes for trend analysis
        text('CREATE INDEX IF NOT EXISTS ix_incidents_created_at_severity ON incidents (created_at, severity)'),
        text('CREATE INDEX IF NOT EXISTS ix_log_entries_created_at_level ON log_entries (created_at, level)'),
        text('CREATE INDEX IF NOT EXISTS ix_log_entries_team_created_level ON log_entries (team_id, created_at, level)'),
        
        # Aggregation indexes
        text('CREATE INDEX IF NOT EXISTS ix_incidents_team_status_created ON incidents (team_id, status, created_at)'),
        text('CREATE INDEX IF NOT EXISTS ix_log_entries_team_service_created ON log_entries (team_id, service, created_at)'),
        
        # Performance monitoring indexes
        text('CREATE INDEX IF NOT EXISTS ix_users_team_created_at ON users (team_id, created_at)'),
        text('CREATE INDEX IF NOT EXISTS ix_incidents_team_severity_status ON incidents (team_id, severity, status)')
    ]
    
    for index in analytical_indexes:
        db.execute(index)
    
    db.commit()
    
    print("Analytical indexes created successfully")

def create_full_text_search_indexes(db: Session) -> None:
    """Create full-text search indexes."""
    
    full_text_indexes = [
        # Log message search
        text('CREATE INDEX IF NOT EXISTS ix_log_entries_message_search ON log_entries USING gin(to_tsvector(\'english\', message))'),
        
        # Incident title and description search
        text('CREATE INDEX IF NOT EXISTS ix_incidents_text_search ON incidents USING gin(to_tsvector(\'english\', title || \' \' || description))')
    ]
    
    for index in full_text_indexes:
        db.execute(index)
    
    db.commit()
    
    print("Full-text search indexes created successfully")

def create_all_indexes(db: Session) -> None:
    """Create all indexes for performance optimization."""
    
    print("Creating performance indexes...")
    create_performance_indexes(db)
    
    print("Creating analytical indexes...")
    create_analytical_indexes(db)
    
    print("Creating full-text search indexes...")
    create_full_text_search_indexes(db)
    
    print("All indexes created successfully")

def get_index_statistics(db: Session) -> dict:
    """Get statistics about database indexes."""
    
    # Get index information
    indexes_query = text("""
        SELECT 
            schemaname,
            tablename,
            indexname,
            indexdef
        FROM pg_indexes 
        WHERE schemaname = 'public'
        ORDER BY tablename, indexname
    """)
    
    indexes = db.execute(indexes_query).fetchall()
    
    # Get table statistics
    tables_query = text("""
        SELECT 
            schemaname,
            tablename,
            attname,
            n_distinct,
            correlation
        FROM pg_stats 
        WHERE schemaname = 'public'
        ORDER BY tablename, attname
    """)
    
    tables = db.execute(tables_query).fetchall()
    
    return {
        "indexes": [
            {
                "schema": row.schemaname,
                "table": row.tablename,
                "name": row.indexname,
                "definition": row.indexdef
            }
            for row in indexes
        ],
        "tables": [
            {
                "schema": row.schemaname,
                "table": row.tablename,
                "column": row.attname,
                "distinct_values": row.n_distinct,
                "correlation": row.correlation
            }
            for row in tables
        ]
    }

def analyze_database_performance(db: Session) -> dict:
    """Analyze database performance and provide recommendations."""
    
    # Get index statistics
    index_stats = get_index_statistics(db)
    
    # Get query performance
    query_stats = text("""
        SELECT 
            query,
            calls,
            total_time,
            rows,
            mean_time
        FROM pg_stat_statements 
        ORDER BY total_time DESC 
        LIMIT 10
    """)
    
    queries = db.execute(query_stats).fetchall()
    
    # Get table sizes
    table_sizes = text("""
        SELECT 
            schemaname,
            tablename,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
            pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
        FROM pg_tables 
        WHERE schemaname = 'public'
        ORDER BY size_bytes DESC
    """)
    
    tables = db.execute(table_sizes).fetchall()
    
    return {
        "index_statistics": index_stats,
        "slow_queries": [
            {
                "query": row.query,
                "calls": row.calls,
                "total_time": row.total_time,
                "rows": row.rows,
                "mean_time": row.mean_time
            }
            for row in queries
        ],
        "table_sizes": [
            {
                "schema": row.schemaname,
                "table": row.tablename,
                "size": row.size,
                "size_bytes": row.size_bytes
            }
            for row in tables
        ]
    }