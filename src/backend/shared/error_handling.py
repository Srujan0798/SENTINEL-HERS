import logging
import traceback
from enum import Enum
from typing import Any, Dict, Optional, Union, List
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
import uuid

logger = logging.getLogger(__name__)

class ErrorType(str, Enum):
    """Error types for classification."""
    VALIDATION_ERROR = "validation_error"
    AUTHENTICATION_ERROR = "authentication_error"
    AUTHORIZATION_ERROR = "authorization_error"
    NOT_FOUND = "not_found"
    CONFLICT = "conflict"
    RATE_LIMIT_ERROR = "rate_limit_error"
    EXTERNAL_SERVICE_ERROR = "external_service_error"
    DATABASE_ERROR = "database_error"
    BUSINESS_LOGIC_ERROR = "business_logic_error"
    SYSTEM_ERROR = "system_error"
    UNKNOWN_ERROR = "unknown_error"

class ErrorSeverity(str, Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorContext(BaseModel):
    """Context information for errors."""
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    user_id: Optional[str] = None
    team_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None

class ErrorDetail(BaseModel):
    """Detailed error information."""
    type: ErrorType
    severity: ErrorSeverity
    message: str
    code: str
    details: Optional[Dict[str, Any]] = None
    stack_trace: Optional[str] = None
    context: ErrorContext

class AppException(Exception):
    """Base application exception."""
    
    def __init__(
        self,
        message: str,
        error_type: ErrorType = ErrorType.SYSTEM_ERROR,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        code: str = "APP_ERROR",
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None
    ):
        self.message = message
        self.error_type = error_type
        self.severity = severity
        self.code = code
        self.details = details or {}
        self.user_message = user_message or message
        super().__init__(message)

class ValidationError(AppException):
    """Validation error exception."""
    
    def __init__(self, message: str, field: str = None, details: Dict[str, Any] = None):
        super().__init__(
            message=message,
            error_type=ErrorType.VALIDATION_ERROR,
            severity=ErrorSeverity.LOW,
            code="VALIDATION_ERROR",
            details={"field": field, **(details or {})}
        )

class AuthenticationError(AppException):
    """Authentication error exception."""
    
    def __init__(self, message: str, token_type: str = None):
        super().__init__(
            message=message,
            error_type=ErrorType.AUTHENTICATION_ERROR,
            severity=ErrorSeverity.HIGH,
            code="AUTHENTICATION_ERROR",
            details={"token_type": token_type}
        )

class AuthorizationError(AppException):
    """Authorization error exception."""
    
    def __init__(self, message: str, required_permission: str = None):
        super().__init__(
            message=message,
            error_type=ErrorType.AUTHORIZATION_ERROR,
            severity=ErrorSeverity.HIGH,
            code="AUTHORIZATION_ERROR",
            details={"required_permission": required_permission}
        )

class NotFoundError(AppException):
    """Not found error exception."""
    
    def __init__(self, resource: str, resource_id: str = None):
        message = f"{resource} not found"
        if resource_id:
            message += f": {resource_id}"
        
        super().__init__(
            message=message,
            error_type=ErrorType.NOT_FOUND,
            severity=ErrorSeverity.MEDIUM,
            code="NOT_FOUND",
            details={"resource": resource, "resource_id": resource_id}
        )

class ConflictError(AppException):
    """Conflict error exception."""
    
    def __init__(self, message: str, resource: str = None):
        super().__init__(
            message=message,
            error_type=ErrorType.CONFLICT,
            severity=ErrorSeverity.MEDIUM,
            code="CONFLICT",
            details={"resource": resource}
        )

class RateLimitError(AppException):
    """Rate limit error exception."""
    
    def __init__(self, message: str, retry_after: int = None):
        super().__init__(
            message=message,
            error_type=ErrorType.RATE_LIMIT_ERROR,
            severity=ErrorSeverity.LOW,
            code="RATE_LIMIT_ERROR",
            details={"retry_after": retry_after}
        )

class ExternalServiceError(AppException):
    """External service error exception."""
    
    def __init__(self, message: str, service: str = None, status_code: int = None):
        super().__init__(
            message=message,
            error_type=ErrorType.EXTERNAL_SERVICE_ERROR,
            severity=ErrorSeverity.HIGH,
            code="EXTERNAL_SERVICE_ERROR",
            details={"service": service, "status_code": status_code}
        )

class DatabaseError(AppException):
    """Database error exception."""
    
    def __init__(self, message: str, operation: str = None, table: str = None):
        super().__init__(
            message=message,
            error_type=ErrorType.DATABASE_ERROR,
            severity=ErrorSeverity.HIGH,
            code="DATABASE_ERROR",
            details={"operation": operation, "table": table}
        )

class BusinessLogicError(AppException):
    """Business logic error exception."""
    
    def __init__(self, message: str, rule: str = None):
        super().__init__(
            message=message,
            error_type=ErrorType.BUSINESS_LOGIC_ERROR,
            severity=ErrorSeverity.MEDIUM,
            code="BUSINESS_LOGIC_ERROR",
            details={"rule": rule}
        )

class ErrorHandler:
    """Centralized error handler."""
    
    def __init__(self):
        self.error_counts: Dict[str, int] = {}
        self.error_history: List[ErrorDetail] = []
        self.max_history = 1000
    
    def handle_exception(self, error: Exception, context: Optional[ErrorContext] = None) -> ErrorDetail:
        """Handle an exception and return error details."""
        
        # Create error context if not provided
        if context is None:
            context = ErrorContext()
        
        # Convert exception to AppException if needed
        if not isinstance(error, AppException):
            error = self._convert_to_app_exception(error)
        
        # Create error detail
        error_detail = ErrorDetail(
            type=error.error_type,
            severity=error.severity,
            message=error.message,
            code=error.code,
            details=error.details,
            stack_trace=traceback.format_exc(),
            context=context
        )
        
        # Log the error
        self._log_error(error_detail, error)
        
        # Update error counts
        self.error_counts[error.code] = self.error_counts.get(error.code, 0) + 1
        
        # Add to history
        self.error_history.append(error_detail)
        if len(self.error_history) > self.max_history:
            self.error_history.pop(0)
        
        return error_detail
    
    def _convert_to_app_exception(self, error: Exception) -> AppException:
        """Convert a generic exception to an AppException."""
        error_type = ErrorType.UNKNOWN_ERROR
        severity = ErrorSeverity.MEDIUM
        code = "UNKNOWN_ERROR"
        
        if isinstance(error, HTTPException):
            if error.status_code == 401:
                return AuthenticationError(str(error.detail))
            elif error.status_code == 403:
                return AuthorizationError(str(error.detail))
            elif error.status_code == 404:
                return NotFoundError("Resource")
            elif error.status_code == 429:
                return RateLimitError(str(error.detail))
        
        elif isinstance(error, ValueError):
            return ValidationError(str(error))
        
        elif "database" in str(error).lower() or "sql" in str(error).lower():
            return DatabaseError(str(error))
        
        return AppException(str(error), error_type, severity, code)
    
    def _log_error(self, error_detail: ErrorDetail, error: Exception):
        """Log the error with appropriate level."""
        log_data = {
            "error_type": error_detail.type.value,
            "severity": error_detail.severity.value,
            "code": error_detail.code,
            "message": error_detail.message,
            "context": error_detail.context.dict(),
            "details": error_detail.details
        }
        
        if error_detail.severity == ErrorSeverity.CRITICAL:
            logger.critical(f"Critical error: {error_detail.message}", extra=log_data)
        elif error_detail.severity == ErrorSeverity.HIGH:
            logger.error(f"High severity error: {error_detail.message}", extra=log_data)
        elif error_detail.severity == ErrorSeverity.MEDIUM:
            logger.warning(f"Medium severity error: {error_detail.message}", extra=log_data)
        else:
            logger.info(f"Low severity error: {error_detail.message}", extra=log_data)
    
    def create_error_response(self, error_detail: ErrorDetail) -> JSONResponse:
        """Create a JSON response for the error."""
        response_data = {
            "error": {
                "type": error_detail.type.value,
                "severity": error_detail.severity.value,
                "message": error_detail.user_message,
                "code": error_detail.code,
                "details": error_detail.details,
                "request_id": error_detail.context.request_id,
                "timestamp": error_detail.context.timestamp.isoformat()
            }
        }
        
        # Set appropriate HTTP status code
        status_codes = {
            ErrorType.VALIDATION_ERROR: 400,
            ErrorType.AUTHENTICATION_ERROR: 401,
            ErrorType.AUTHORIZATION_ERROR: 403,
            ErrorType.NOT_FOUND: 404,
            ErrorType.CONFLICT: 409,
            ErrorType.RATE_LIMIT_ERROR: 429,
            ErrorType.EXTERNAL_SERVICE_ERROR: 502,
            ErrorType.DATABASE_ERROR: 503,
            ErrorType.BUSINESS_LOGIC_ERROR: 422,
            ErrorType.SYSTEM_ERROR: 500,
            ErrorType.UNKNOWN_ERROR: 500
        }
        
        status_code = status_codes.get(error_detail.type, 500)
        
        return JSONResponse(
            status_code=status_code,
            content=response_data
        )
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics."""
        return {
            "total_errors": len(self.error_history),
            "error_counts": self.error_counts,
            "error_types": {
                error_type.value: sum(1 for error in self.error_history if error.type == error_type)
                for error_type in ErrorType
            },
            "severity_distribution": {
                severity.value: sum(1 for error in self.error_history if error.severity == severity)
                for severity in ErrorSeverity
            },
            "recent_errors": [
                error.dict() for error in self.error_history[-10:]
            ]
        }

# Global error handler instance
error_handler = ErrorHandler()

def exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler for FastAPI."""
    
    # Create context from request
    context = ErrorContext(
        endpoint=str(request.url),
        method=request.method,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        parameters=dict(request.query_params)
    )
    
    # Handle the exception
    error_detail = error_handler.handle_exception(exc, context)
    
    # Return error response
    return error_handler.create_error_response(error_detail)

def setup_error_handling(app):
    """Setup error handling for FastAPI app."""
    app.add_exception_handler(Exception, exception_handler)

# Decorator for error handling
def handle_errors(func):
    """Decorator to handle errors in functions."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except AppException:
            # Re-raise app exceptions as they are already handled
            raise
        except Exception as e:
            # Convert to app exception and handle
            app_exception = error_handler._convert_to_app_exception(e)
            raise app_exception
    return wrapper

# Context manager for error handling
class ErrorContextManager:
    """Context manager for error handling."""
    
    def __init__(self, operation: str):
        self.operation = operation
        self.context = None
    
    def __enter__(self):
        self.context = ErrorContext(endpoint=self.operation)
        return self.context
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val:
            error_handler.handle_exception(exc_val, self.context)
        return False  # Don't suppress the exception