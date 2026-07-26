from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, select
from sqlalchemy.sql import text
from datetime import datetime, timezone
import logging

from src.backend.shared_models import UserModel, TeamModel, LogEntryModel, IncidentModel
from src.backend.shared.repositories import UnitOfWork
from src.backend.shared.input_validator import InputValidator

logger = logging.getLogger(__name__)

class QueryOptimizer:
    """Service for optimizing database queries and fixing N+1 issues."""
    
    def __init__(self, db: Session):
        self.db = db
        self.uow = UnitOfWork(db)
    
    def get_incidents_with_details(
        self,
        team_id: str,
        limit: int = 20,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Get incidents with their details in a single query to avoid N+1 issues."""
        
        # Build base query
        query = select(
            IncidentModel,
            func.count(LogEntryModel.id).label('log_count'),
            func.max(LogEntryModel.created_at).label('last_log_time')
        ).outerjoin(
            LogEntryModel,
            IncidentModel.id == LogEntryModel.incident_id
        ).filter(
            IncidentModel.team_id == team_id
        ).group_by(IncidentModel.id)
        
        # Apply filters
        if filters:
            if 'severity' in filters:
                query = query.filter(IncidentModel.severity == filters['severity'])
            if 'status' in filters:
                query = query.filter(IncidentModel.status == filters['status'])
            if 'created_after' in filters:
                query = query.filter(IncidentModel.created_at >= filters['created_after'])
            if 'created_before' in filters:
                query = query.filter(IncidentModel.created_at <= filters['created_before'])
        
        # Get total count
        count_query = select(func.count(IncidentModel.id)).filter(
            IncidentModel.team_id == team_id
        )
        if filters:
            if 'severity' in filters:
                count_query = count_query.filter(IncidentModel.severity == filters['severity'])
            if 'status' in filters:
                count_query = count_query.filter(IncidentModel.status == filters['status'])
            if 'created_after' in filters:
                count_query = count_query.filter(IncidentModel.created_at >= filters['created_after'])
            if 'created_before' in filters:
                count_query = count_query.filter(IncidentModel.created_at <= filters['created_before'])
        
        total = self.db.execute(count_query).scalar()
        
        # Apply pagination and ordering
        query = query.order_by(desc(IncidentModel.created_at)).offset(offset).limit(limit)
        
        # Execute query
        results = self.db.execute(query).all()
        
        # Format results
        incidents = []
        for row in results:
            incident = row[0]
            log_count = row[1]
            last_log_time = row[2]
            
            incidents.append({
                "id": str(incident.id),
                "title": incident.title,
                "description": incident.description,
                "severity": incident.severity,
                "status": incident.status,
                "created_at": incident.created_at.isoformat() if incident.created_at else None,
                "updated_at": incident.updated_at.isoformat() if incident.updated_at else None,
                "resolved_at": incident.resolved_at.isoformat() if incident.resolved_at else None,
                "assigned_to": incident.assigned_to,
                "escalated_to": incident.escalated_to,
                "ai_summary": incident.ai_summary,
                "ai_root_cause_ranking": incident.ai_root_cause_ranking,
                "log_count": log_count,
                "last_log_time": last_log_time.isoformat() if last_log_time else None,
                "team_id": str(incident.team_id)
            })
        
        return incidents, total
    
    def get_users_with_team_and_role(
        self,
        team_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Get users with their team and role information in a single query."""
        
        # Build query with joins
        query = select(
            UserModel,
            TeamModel.name.label('team_name'),
            RoleModel.name.label('role_name'),
            RoleModel.permissions.label('role_permissions')
        ).join(
            TeamModel,
            UserModel.team_id == TeamModel.id
        ).join(
            RoleModel,
            UserModel.role_id == RoleModel.id
        )
        
        # Apply team filter if specified
        if team_id:
            query = query.filter(UserModel.team_id == team_id)
        
        # Get total count
        count_query = select(func.count(UserModel.id))
        if team_id:
            count_query = count_query.filter(UserModel.team_id == team_id)
        total = self.db.execute(count_query).scalar()
        
        # Apply pagination and ordering
        query = query.order_by(desc(UserModel.created_at)).offset(offset).limit(limit)
        
        # Execute query
        results = self.db.execute(query).all()
        
        # Format results
        users = []
        for row in results:
            user = row[0]
            team_name = row[1]
            role_name = row[2]
            role_permissions = row[3]
            
            users.append({
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "name": user.name,
                "team_id": str(user.team_id),
                "team_name": team_name,
                "role_id": str(user.role_id),
                "role_name": role_name,
                "role_permissions": role_permissions,
                "is_active": user.is_active,
                "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "updated_at": user.updated_at.isoformat() if user.updated_at else None
            })
        
        return users, total
    
    def get_log_entries_with_incident_details(
        self,
        team_id: str,
        limit: int = 100,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Get log entries with incident details in a single query."""
        
        # Build query with joins
        query = select(
            LogEntryModel,
            IncidentModel.title.label('incident_title'),
            IncidentModel.severity.label('incident_severity'),
            IncidentModel.status.label('incident_status')
        ).outerjoin(
            IncidentModel,
            LogEntryModel.incident_id == IncidentModel.id
        ).filter(
            LogEntryModel.team_id == team_id
        )
        
        # Apply filters
        if filters:
            if 'service' in filters:
                query = query.filter(LogEntryModel.service == filters['service'])
            if 'level' in filters:
                query = query.filter(LogEntryModel.level == filters['level'])
            if 'incident_id' in filters:
                query = query.filter(LogEntryModel.incident_id == filters['incident_id'])
            if 'created_after' in filters:
                query = query.filter(LogEntryModel.created_at >= filters['created_after'])
            if 'created_before' in filters:
                query = query.filter(LogEntryModel.created_at <= filters['created_before'])
            if 'message_search' in filters:
                search_term = InputValidator.sanitize_search_query(filters['message_search'])
                if search_term:
                    query = query.filter(LogEntryModel.message.ilike(f"%{search_term}%"))
        
        # Get total count
        count_query = select(func.count(LogEntryModel.id)).filter(
            LogEntryModel.team_id == team_id
        )
        if filters:
            if 'service' in filters:
                count_query = count_query.filter(LogEntryModel.service == filters['service'])
            if 'level' in filters:
                count_query = count_query.filter(LogEntryModel.level == filters['level'])
            if 'incident_id' in filters:
                count_query = count_query.filter(LogEntryModel.incident_id == filters['incident_id'])
            if 'created_after' in filters:
                count_query = count_query.filter(LogEntryModel.created_at >= filters['created_after'])
            if 'created_before' in filters:
                count_query = count_query.filter(LogEntryModel.created_at <= filters['created_before'])
            if 'message_search' in filters:
                search_term = InputValidator.sanitize_search_query(filters['message_search'])
                if search_term:
                    count_query = count_query.filter(LogEntryModel.message.ilike(f"%{search_term}%"))
        
        total = self.db.execute(count_query).scalar()
        
        # Apply pagination and ordering
        query = query.order_by(desc(LogEntryModel.created_at)).offset(offset).limit(limit)
        
        # Execute query
        results = self.db.execute(query).all()
        
        # Format results
        log_entries = []
        for row in results:
            log_entry = row[0]
            incident_title = row[1]
            incident_severity = row[2]
            incident_status = row[3]
            
            log_entries.append({
                "id": str(log_entry.id),
                "team_id": str(log_entry.team_id),
                "incident_id": str(log_entry.incident_id) if log_entry.incident_id else None,
                "service": log_entry.service,
                "level": log_entry.level,
                "message": log_entry.message,
                "metadata": log_entry.metadata_ or {},
                "source_ip": log_entry.source_ip,
                "indexed_at": log_entry.indexed_at.isoformat() if log_entry.indexed_at else None,
                "created_at": log_entry.created_at.isoformat() if log_entry.created_at else None,
                "incident_title": incident_title,
                "incident_severity": incident_severity,
                "incident_status": incident_status
            })
        
        return log_entries, total
    
    def get_team_statistics(self, team_id: str, days: int = 7) -> Dict[str, Any]:
        """Get comprehensive team statistics in a single query."""
        
        since = datetime.now(timezone.utc) - timezone.timedelta(days=days)
        
        # Build complex query for all statistics
        query = text("""
            SELECT 
                COUNT(DISTINCT i.id) as incident_count,
                COUNT(DISTINCT CASE WHEN i.severity = 'SEV1' THEN i.id END) as sev1_count,
                COUNT(DISTINCT CASE WHEN i.severity = 'SEV2' THEN i.id END) as sev2_count,
                COUNT(DISTINCT CASE WHEN i.severity = 'SEV3' THEN i.id END) as sev3_count,
                COUNT(DISTINCT CASE WHEN i.severity = 'SEV4' THEN i.id END) as sev4_count,
                COUNT(DISTINCT CASE WHEN i.status = 'resolved' THEN i.id END) as resolved_count,
                COUNT(DISTINCT CASE WHEN i.status = 'closed' THEN i.id END) as closed_count,
                COUNT(DISTINCT l.id) as log_count,
                COUNT(DISTINCT CASE WHEN l.level = 'ERROR' THEN l.id END) as error_count,
                COUNT(DISTINCT CASE WHEN l.level = 'WARNING' THEN l.id END) as warning_count,
                COUNT(DISTINCT u.id) as user_count,
                COUNT(DISTINCT CASE WHEN u.is_active = true THEN u.id END) as active_user_count,
                COUNT(DISTINCT s.id) as service_count
            FROM incidents i
            LEFT JOIN log_entries l ON i.team_id = l.team_id AND l.created_at >= :since
            LEFT JOIN users u ON i.team_id = u.team_id AND u.created_at >= :since
            LEFT JOIN (
                SELECT DISTINCT service, team_id FROM log_entries 
                WHERE team_id = :team_id AND created_at >= :since
            ) s ON 1=1
            WHERE i.team_id = :team_id AND i.created_at >= :since
        """)
        
        # Execute query
        result = self.db.execute(query, {
            "team_id": team_id,
            "since": since
        }).fetchone()
        
        if result:
            return {
                "period_days": days,
                "incident_count": result.incident_count or 0,
                "severity_breakdown": {
                    "SEV1": result.sev1_count or 0,
                    "SEV2": result.sev2_count or 0,
                    "SEV3": result.sev3_count or 0,
                    "SEV4": result.sev4_count or 0
                },
                "status_breakdown": {
                    "resolved": result.resolved_count or 0,
                    "closed": result.closed_count or 0
                },
                "log_count": result.log_count or 0,
                "error_count": result.error_count or 0,
                "warning_count": result.warning_count or 0,
                "user_count": result.user_count or 0,
                "active_user_count": result.active_user_count or 0,
                "service_count": result.service_count or 0
            }
        else:
            return {
                "period_days": days,
                "incident_count": 0,
                "severity_breakdown": {"SEV1": 0, "SEV2": 0, "SEV3": 0, "SEV4": 0},
                "status_breakdown": {"resolved": 0, "closed": 0},
                "log_count": 0,
                "error_count": 0,
                "warning_count": 0,
                "user_count": 0,
                "active_user_count": 0,
                "service_count": 0
            }
    
    def get_dashboard_data(self, team_id: str) -> Dict[str, Any]:
        """Get all dashboard data in optimized queries."""
        
        # Get current time
        now = datetime.now(timezone.utc)
        
        # Get data for different time periods
        today_stats = self.get_team_statistics(team_id, 1)
        week_stats = self.get_team_statistics(team_id, 7)
        month_stats = self.get_team_statistics(team_id, 30)
        
        # Get recent incidents
        recent_incidents, _ = self.get_incidents_with_details(
            team_id=team_id,
            limit=10,
            offset=0
        )
        
        # Get recent errors
        recent_errors, _ = self.get_log_entries_with_incident_details(
            team_id=team_id,
            limit=10,
            offset=0,
            filters={"level": "ERROR"}
        )
        
        # Get active users
        active_users, _ = self.get_users_with_team_and_role(
            team_id=team_id,
            limit=10,
            offset=0
        )
        
        return {
            "timestamp": now.isoformat(),
            "team_id": team_id,
            "statistics": {
                "today": today_stats,
                "week": week_stats,
                "month": month_stats
            },
            "recent_incidents": recent_incidents,
            "recent_errors": recent_errors,
            "active_users": active_users
        }