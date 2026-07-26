import logging
import time
from functools import wraps
from typing import Any, Callable, Dict, Optional
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class ErrorTracker:
    """Tracks errors by type and provides insights for debugging."""
    
    def __init__(self):
        self.error_counts: Dict[str, int] = {}
        self.error_timestamps: Dict[str, list] = {}
        self.recent_errors: list = []
        self.max_recent_errors = 100
    
    def record_error(self, error_type: str, error: Exception, context: Optional[Dict] = None):
        """Record an error for analysis."""
        timestamp = datetime.now()
        
        # Update error counts
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        
        # Store timestamps for pattern analysis
        if error_type not in self.error_timestamps:
            self.error_timestamps[error_type] = []
        self.error_timestamps[error_type].append(timestamp)
        
        # Keep only recent timestamps (last hour)
        hour_ago = timestamp - timedelta(hours=1)
        self.error_timestamps[error_type] = [
            ts for ts in self.error_timestamps[error_type] 
            if ts > hour_ago
        ]
        
        # Add to recent errors
        error_entry = {
            "timestamp": timestamp.isoformat(),
            "type": error_type,
            "message": str(error),
            "context": context or {},
            "count": self.error_counts[error_type]
        }
        self.recent_errors.append(error_entry)
        
        # Keep only recent errors
        if len(self.recent_errors) > self.max_recent_errors:
            self.recent_errors = self.recent_errors[-self.max_recent_errors:]
        
        logger.error(f"Error recorded: {error_type} - {error}", extra=context)
    
    def get_error_patterns(self) -> Dict[str, Any]:
        """Analyze error patterns for debugging."""
        patterns = {}
        
        for error_type, timestamps in self.error_timestamps.items():
            if len(timestamps) >= 3:  # Only analyze if we have multiple occurrences
                time_diffs = []
                for i in range(1, len(timestamps)):
                    diff = (timestamps[i] - timestamps[i-1]).total_seconds()
                    time_diffs.append(diff)
                
                patterns[error_type] = {
                    "count": len(timestamps),
                    "frequency": sum(time_diffs) / len(time_diffs) if time_diffs else 0,
                    "trend": "increasing" if len(timestamps) > 10 else "stable",
                    "last_occurrence": timestamps[-1].isoformat() if timestamps else None
                }
        
        return patterns

class GracefulErrorHandler:
    """Provides graceful error handling with fallbacks."""
    
    def __init__(self, fallback_value: Any = None):
        self.fallback_value = fallback_value
        self.error_tracker = ErrorTracker()
    
    def handle_with_fallback(self, operation: Callable, error_type: str = "UnknownError"):
        """Execute operation with graceful fallback on error."""
        try:
            return operation()
        except Exception as e:
            self.error_tracker.record_error(error_type, e)
            return self.fallback_value
    
    def create_resilient_function(self, 
                                operation: Callable,
                                error_type: str,
                                fallback_func: Optional[Callable] = None) -> Callable:
        """Create a resilient version of a function with fallback."""
        def resilient_function(*args, **kwargs):
            try:
                return operation(*args, **kwargs)
            except Exception as e:
                self.error_tracker.record_error(error_type, e, {"args": args, "kwargs": kwargs})
                if fallback_func:
                    return fallback_func(*args, **kwargs)
                return self.fallback_value
        
        return resilient_function

# Decorator for automatic error handling
def handle_errors(error_type: str = "UnknownError", fallback_value: Any = None):
    """Decorator to automatically handle errors with fallback."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            error_handler = GracefulErrorHandler(fallback_value)
            return error_handler.handle_with_fallback(
                lambda: func(*args, **kwargs),
                error_type
            )
        return wrapper
    return decorator

def log_errors(error_type: str = "UnknownError"):
    """Decorator to log errors without affecting execution."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {error_type} - {e}", 
                           extra={"function": func.__name__, "error_type": error_type})
                raise
        return wrapper
    return decorator

class RetryHandler:
    """Handles retries with exponential backoff."""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.error_tracker = ErrorTracker()
    
    async def retry_async(self, operation: Callable, error_type: str = "RetryError") -> Any:
        """Retry an async operation with exponential backoff."""
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return await operation()
            except Exception as e:
                last_error = e
                self.error_tracker.record_error(error_type, e, {"attempt": attempt + 1})
                
                if attempt < self.max_retries:
                    delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                    logger.warning(f"Retry attempt {attempt + 1}/{self.max_retries} after {delay}s delay")
                    await asyncio.sleep(delay)
        
        raise last_error
    
    def retry_sync(self, operation: Callable, error_type: str = "RetryError") -> Any:
        """Retry a sync operation with exponential backoff."""
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return operation()
            except Exception as e:
                last_error = e
                self.error_tracker.record_error(error_type, e, {"attempt": attempt + 1})
                
                if attempt < self.max_retries:
                    delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                    logger.warning(f"Retry attempt {attempt + 1}/{self.max_retries} after {delay}s delay")
                    time.sleep(delay)
        
        raise last_error

# Global error handler instance
global_error_handler = GracefulErrorHandler()

def get_error_insights() -> Dict[str, Any]:
    """Get insights about recent errors for debugging."""
    return {
        "total_errors": sum(global_error_handler.error_tracker.error_counts.values()),
        "error_patterns": global_error_handler.error_tracker.get_error_patterns(),
        "recent_errors": global_error_handler.error_tracker.recent_errors[-10:],  # Last 10 errors
        "timestamp": datetime.now().isoformat()
    }