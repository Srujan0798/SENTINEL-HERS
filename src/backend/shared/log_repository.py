from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_, func, desc
from datetime import datetime, timezone

from src.backend.shared_models import LogEntryModel
from src.backend.shared.repositories import BaseRepository
from src.backend.shared.input_validator import InputValidator

class LogRepository(BaseRepository):
    """Repository for log entry operations."""
    
    def get_by_id(self, id: str) -> Optional[LogEntryModel]:
        """Get log entry by ID."""
        return self.db.query(LogEntryModel).filter(LogEntryModel.id == id).first()
    
    def get_by_incident_id(self, incident_id: str) -> List[LogEntryModel]:
        """Get all log entries for an incident."""
        return self.db.query(LogEntryModel).filter(
            LogEntryModel.incident_id == incident_id
        ).order_by(LogEntryModel.created_at.desc()).all()
    
    def create(self, log_data: Dict[str, Any]) -> LogEntryModel:
        """Create a new log entry."""
        log_entry = LogEntryModel(**log_data)
        self.db.add(log_entry)
        self.commit()
        return log_entry
    
    def update(self, log_entry: LogEntryModel) -> LogEntryModel:
        """Update a log entry."""
        self.db.commit()
        return log_entry
    
    def delete(self, id: str) -> bool:
        """Delete a log entry by ID."""
        log_entry = self.get_by_id(id)
        if log_entry:
            self.db.delete(log_entry)
            self.commit()
            return True
        return False
    
    def search_logs(
        self,
        team_id: str,
        q: Optional[str] = None,
        service: Optional[str] = None,
        level: Optional[str] = None,
        from_ts: Optional[datetime] = None,
        to_ts: Optional[datetime] = None,
        page: int = 1,
        per_page: int = 20
    ) -> tuple[List[LogEntryModel], int]:
        """Search log entries with filtering and pagination."""
        query = self.db.query(LogEntryModel).filter(LogEntryModel.team_id == team_id)
        
        # Apply search filters
        if q:
            sanitized_q = InputValidator.sanitize_search_query(q)
            if sanitized_q:
                query = query.filter(LogEntryModel.message.ilike(f"%{sanitized_q}%"))
        
        if service:
            sanitized_service = InputValidator.validate_service_name(service)
            query = query.filter(LogEntryModel.service == sanitized_service)
        
        if level:
            sanitized_level = InputValidator.validate_log_level(level)
            query = query.filter(LogEntryModel.level == sanitized_level)
        
        if from_ts:
            query = query.filter(LogEntryModel.created_at >= from_ts)
        
        if to_ts:
            query = query.filter(LogEntryModel.created_at <= to_ts)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * per_page
        rows = query.order_by(desc(LogEntryModel.created_at)).offset(offset).limit(per_page).all()
        
        return rows, total
    
    def get_logs_by_service(
        self,
        team_id: str,
        service: str,
        hours: int = 24,
        limit: int = 100
    ) -> List[LogEntryModel]:
        """Get recent logs for a specific service."""
        since = datetime.now(timezone.utc) - timezone.timedelta(hours=hours)
        
        return self.db.query(LogEntryModel).filter(
            and_(
                LogEntryModel.team_id == team_id,
                LogEntryModel.service == service,
                LogEntryModel.created_at >= since
            )
        ).order_by(desc(LogEntryModel.created_at)).limit(limit).all()
    
    def get_error_logs(
        self,
        team_id: str,
        hours: int = 24,
        limit: int = 100
    ) -> List[LogEntryModel]:
        """Get recent error logs."""
        since = datetime.now(timezone.utc) - timezone.timedelta(hours=hours)
        
        return self.db.query(LogEntryModel).filter(
            and_(
                LogEntryModel.team_id == team_id,
                LogEntryModel.level.in_(["ERROR", "CRITICAL"]),
                LogEntryModel.created_at >= since
            )
        ).order_by(desc(LogEntryModel.created_at)).limit(limit).all()
    
    def get_log_statistics(
        self,
        team_id: str,
        days: int = 7
    ) -> Dict[str, Any]:
        """Get log statistics for a team."""
        since = datetime.now(timezone.utc) - timezone.timedelta(days=days)
        
        # Count by level
        level_counts = self.db.query(
            LogEntryModel.level,
            func.count(LogEntryModel.id).label('count')
        ).filter(
            and_(
                LogEntryModel.team_id == team_id,
                LogEntryModel.created_at >= since
            )
        ).group_by(LogEntryModel.level).all()
        
        # Count by service
        service_counts = self.db.query(
            LogEntryModel.service,
            func.count(LogEntryModel.id).label('count')
        ).filter(
            and_(
                LogEntryModel.team_id == team_id,
                LogEntryModel.created_at >= since
            )
        ).group_by(LogEntryModel.service).order_by(func.count(LogEntryModel.id).desc()).limit(10).all()
        
        # Total logs
        total_logs = self.db.query(LogEntryModel).filter(
            and_(
                LogEntryModel.team_id == team_id,
                LogEntryModel.created_at >= since
            )
        ).count()
        
        return {
            "total_logs": total_logs,
            "level_counts": {level: count for level, count in level_counts},
            "top_services": {service: count for service, count in service_counts},
            "period_days": days
        }
    
    def bulk_create(self, log_entries: List[Dict[str, Any]]) -> List[LogEntryModel]:
        """Create multiple log entries at once."""
        entries = [LogEntryModel(**entry) for entry in log_entries]
        self.db.add_all(entries)
        self.commit()
        return entries
    
    def cleanup_old_logs(self, days: int = 30) -> int:
        """Clean up logs older than specified days."""
        cutoff_date = datetime.now(timezone.utc) - timezone.timedelta(days=days)
        
        deleted = self.db.query(LogEntryModel).filter(
            LogEntryModel.created_at < cutoff_date
        ).delete()
        
        self.commit()
        return deleted