import re
from typing import Optional, List, Dict, Any
from fastapi import HTTPException, status
from pydantic import BaseModel, Field, field_validator

class InputValidator:
    """Comprehensive input validation and sanitization."""
    
    # Patterns for validation
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_]{3,20}$')
    PASSWORD_PATTERN = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$')
    SERVICE_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{1,50}$')
    LOG_LEVEL_PATTERN = re.compile(r'^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$')
    
    # Maximum lengths
    MAX_USERNAME_LENGTH = 50
    MAX_PASSWORD_LENGTH = 128
    MAX_EMAIL_LENGTH = 255
    MAX_TITLE_LENGTH = 200
    MAX_DESCRIPTION_LENGTH = 5000
    MAX_SERVICE_LENGTH = 100
    MAX_MESSAGE_LENGTH = 10000
    
    @classmethod
    def validate_email(cls, email: str) -> str:
        """Validate and sanitize email address."""
        if not email or not isinstance(email, str):
            raise HTTPException(status_code=400, detail="Email is required")
        
        email = email.strip()
        if len(email) > cls.MAX_EMAIL_LENGTH:
            raise HTTPException(status_code=400, detail="Email too long")
        
        if not cls.EMAIL_PATTERN.match(email):
            raise HTTPException(status_code=400, detail="Invalid email format")
        
        # Basic email sanitization
        email = email.lower()
        email = re.sub(r'[^\w\.-@]+', '', email)
        
        return email
    
    @classmethod
    def validate_username(cls, username: str) -> str:
        """Validate and sanitize username."""
        if not username or not isinstance(username, str):
            raise HTTPException(status_code=400, detail="Username is required")
        
        username = username.strip()
        if len(username) < 3 or len(username) > cls.MAX_USERNAME_LENGTH:
            raise HTTPException(status_code=400, detail="Username must be 3-50 characters")
        
        if not cls.USERNAME_PATTERN.match(username):
            raise HTTPException(status_code=400, detail="Username can only contain letters, numbers, and underscores")
        
        # Sanitize username
        username = re.sub(r'[^\w]+', '', username)
        
        return username
    
    @classmethod
    def validate_password(cls, password: str) -> str:
        """Validate password strength."""
        if not password or not isinstance(password, str):
            raise HTTPException(status_code=400, detail="Password is required")
        
        if len(password) < 8 or len(password) > cls.MAX_PASSWORD_LENGTH:
            raise HTTPException(status_code=400, detail="Password must be 8-128 characters")
        
        if not cls.PASSWORD_PATTERN.match(password):
            raise HTTPException(status_code=400, detail="Password must contain uppercase, lowercase, number, and special character")
        
        return password
    
    @classmethod
    def validate_service_name(cls, service: str) -> str:
        """Validate and sanitize service name."""
        if not service or not isinstance(service, str):
            raise HTTPException(status_code=400, detail="Service name is required")
        
        service = service.strip()
        if len(service) > cls.MAX_SERVICE_LENGTH:
            raise HTTPException(status_code=400, detail="Service name too long")
        
        if not cls.SERVICE_NAME_PATTERN.match(service):
            raise HTTPException(status_code=400, detail="Service name contains invalid characters")
        
        # Sanitize service name
        service = re.sub(r'[^\w_-]+', '', service)
        
        return service
    
    @classmethod
    def validate_log_level(cls, level: str) -> str:
        """Validate log level."""
        if not level or not isinstance(level, str):
            raise HTTPException(status_code=400, detail="Log level is required")
        
        level = level.upper().strip()
        if not cls.LOG_LEVEL_PATTERN.match(level):
            raise HTTPException(status_code=400, detail="Invalid log level")
        
        return level
    
    @classmethod
    def validate_title(cls, title: str) -> str:
        """Validate and sanitize incident title."""
        if not title or not isinstance(title, str):
            raise HTTPException(status_code=400, detail="Title is required")
        
        title = title.strip()
        if len(title) > cls.MAX_TITLE_LENGTH:
            raise HTTPException(status_code=400, detail="Title too long")
        
        # Basic sanitization
        title = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', title)
        title = re.sub(r'\s+', ' ', title).strip()
        
        return title
    
    @classmethod
    def validate_description(cls, description: str) -> str:
        """Validate and sanitize incident description."""
        if not description or not isinstance(description, str):
            raise HTTPException(status_code=400, detail="Description is required")
        
        description = description.strip()
        if len(description) > cls.MAX_DESCRIPTION_LENGTH:
            raise HTTPException(status_code=400, detail="Description too long")
        
        # Basic sanitization
        description = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', description)
        
        return description
    
    @classmethod
    def validate_message(cls, message: str) -> str:
        """Validate and sanitize log message."""
        if not message or not isinstance(message, str):
            raise HTTPException(status_code=400, detail="Message is required")
        
        message = message.strip()
        if len(message) > cls.MAX_MESSAGE_LENGTH:
            raise HTTPException(status_code=400, detail="Message too long")
        
        # Basic sanitization
        message = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', message)
        
        return message
    
    @classmethod
    def validate_severity(cls, severity: str) -> str:
        """Validate incident severity."""
        valid_severities = ["SEV1", "SEV2", "SEV3", "SEV4"]
        if severity not in valid_severities:
            raise HTTPException(status_code=400, detail=f"Invalid severity. Must be one of: {valid_severities}")
        return severity
    
    @classmethod
    def validate_status(cls, status: str) -> str:
        """Validate incident status."""
        valid_statuses = ["detected", "triaging", "investigating", "mitigating", "resolved", "closed"]
        if status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
        return status
    
    @classmethod
    def sanitize_search_query(cls, query: str) -> str:
        """Sanitize search query to prevent injection."""
        if not query or not isinstance(query, str):
            return ""
        
        # Remove potential SQL injection patterns
        query = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', query)
        query = re.sub(r'(--|;|\/\*|\*\/|@@|xp_|sp_|execute|select|insert|update|delete|drop|create|alter|truncate)', '', query, flags=re.IGNORECASE)
        query = query.strip()
        
        # Limit length
        if len(query) > 1000:
            query = query[:1000]
        
        return query
    
    @classmethod
    def validate_pagination_params(cls, page: int, per_page: int) -> tuple[int, int]:
        """Validate pagination parameters."""
        if page < 1:
            page = 1
        if per_page < 1 or per_page > 100:
            per_page = 20
        return page, per_page
    
    @classmethod
    def validate_timestamp(cls, timestamp: Optional[str]) -> Optional[str]:
        """Validate timestamp format."""
        if not timestamp:
            return None
        
        # Basic timestamp validation (ISO format)
        if not re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?$', timestamp):
            raise HTTPException(status_code=400, detail="Invalid timestamp format")
        
        return timestamp

# Request validation models
class SafeLoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=128)
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        return InputValidator.validate_username(v)
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        return InputValidator.validate_password(v)

class SafeRegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=128)
    email: str = Field(..., max_length=255)
    name: str = Field(..., min_length=1, max_length=100)
    team_name: str = Field(..., min_length=1, max_length=100)
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        return InputValidator.validate_username(v)
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        return InputValidator.validate_password(v)
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        return InputValidator.validate_email(v)
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        v = v.strip()
        if len(v) > 100:
            raise ValueError("Name too long")
        return v
    
    @field_validator('team_name')
    @classmethod
    def validate_team_name(cls, v):
        v = v.strip()
        if len(v) > 100:
            raise ValueError("Team name too long")
        return v

class SafeIncidentRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=5000)
    severity: str = Field(..., pattern=r'^SEV[1-4]$')
    status: str = Field(..., pattern=r'^(detected|triaging|investigating|mitigating|resolved|closed)$')
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        return InputValidator.validate_title(v)
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v):
        return InputValidator.validate_description(v)
    
    @field_validator('severity')
    @classmethod
    def validate_severity(cls, v):
        return InputValidator.validate_severity(v)
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        return InputValidator.validate_status(v)

class SafeLogIngestRequest(BaseModel):
    entries: List[Dict[str, Any]] = Field(..., min_length=1, max_length=1000)
    
    @field_validator('entries')
    @classmethod
    def validate_entries(cls, v):
        for i, entry in enumerate(v):
            if not isinstance(entry, dict):
                raise ValueError(f"entries[{i}]: must be an object")
            
            if 'service' not in entry or not entry['service']:
                raise ValueError(f"entries[{i}].service: must not be empty")
            if 'message' not in entry or not entry['message']:
                raise ValueError(f"entries[{i}].message: must not be empty")
            
            # Validate and sanitize individual fields
            entry['service'] = InputValidator.validate_service_name(entry['service'])
            entry['message'] = InputValidator.validate_message(entry['message'])
            
            if 'level' in entry:
                entry['level'] = InputValidator.validate_log_level(entry['level'])
        
        return v