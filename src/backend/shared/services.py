from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import bcrypt
import jwt
from sqlalchemy.orm import Session

from src.backend.shared.repositories import UnitOfWork
from src.backend.shared_models import UserModel, TeamModel, RoleModel
from src.backend.auth.models import (
    LoginRequest,
    RegisterRequest,
    RefreshRequest,
    UserResponse,
    RoleResponse,
    TokenResponse
)
from src.backend.shared.secret_manager import get_jwt_secret, get_jwt_refresh_secret
from src.backend.shared.input_validator import InputValidator

class AuthService:
    """Service for authentication and authorization operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.uow = UnitOfWork(db)
    
    def register_user(self, request: RegisterRequest) -> UserResponse:
        """Register a new user."""
        # Validate input
        username = InputValidator.validate_username(request.username)
        password = InputValidator.validate_password(request.password)
        email = InputValidator.validate_email(request.email)
        name = InputValidator.validate_name(request.name)
        team_name = InputValidator.validate_team_name(request.team_name)
        
        # Check if user already exists
        if self.uow.users.get_by_username(username):
            raise ValueError("Username already exists")
        if self.uow.users.get_by_email(email):
            raise ValueError("Email already exists")
        
        # Create team if it doesn't exist
        team = self.uow.teams.get_by_name(team_name)
        if not team:
            team = self.uow.teams.create({
                "name": team_name,
                "created_at": datetime.now(timezone.utc)
            })
        
        # Get default role
        role = self.uow.roles.get_by_name("user")
        if not role:
            role = self.uow.roles.create({
                "name": "user",
                "permissions": ["*"],
                "description": "Default user role"
            })
        
        # Create user
        user_data = {
            "username": username,
            "password_hash": self._hash_password(password),
            "email": email,
            "name": name,
            "team_id": team.id,
            "role_id": role.id,
            "is_active": True,
            "created_at": datetime.now(timezone.utc)
        }
        
        user = self.uow.users.create(user_data)
        
        return UserResponse(
            id=str(user.id),
            username=user.username,
            email=user.email,
            name=user.name,
            team_id=str(user.team_id),
            role_id=str(user.role_id),
            role=RoleResponse(
                id=str(role.id),
                name=role.name,
                permissions=role.permissions,
                description=role.description
            ),
            is_active=user.is_active,
            last_login_at=user.last_login_at,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
    
    def login_user(self, request: LoginRequest) -> TokenResponse:
        """Authenticate user and return tokens."""
        # Validate input
        username = InputValidator.validate_username(request.username)
        password = InputValidator.validate_password(request.password)
        
        # Authenticate user
        user = self.uow.users.authenticate(username, password)
        if not user:
            raise ValueError("Invalid credentials")
        
        # Update last login
        self.uow.users.update_last_login(str(user.id))
        
        # Generate tokens
        access_token = self._create_access_token(str(user.id), str(user.team_id), user.role.name)
        refresh_token = self._create_refresh_token(str(user.id))
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=900,  # 15 minutes
            user=UserResponse(
                id=str(user.id),
                username=user.username,
                email=user.email,
                name=user.name,
                team_id=str(user.team_id),
                role_id=str(user.role_id),
                role=RoleResponse(
                    id=str(user.role.id),
                    name=user.role.name,
                    permissions=user.role.permissions,
                    description=user.role.description
                ),
                is_active=user.is_active,
                last_login_at=user.last_login_at,
                created_at=user.created_at,
                updated_at=user.updated_at
            )
        )
    
    def refresh_token(self, request: RefreshRequest) -> TokenResponse:
        """Refresh access token using refresh token."""
        try:
            payload = jwt.decode(
                request.refresh_token,
                get_jwt_refresh_secret(),
                algorithms=["HS256"]
            )
            
            user_id = payload.get("sub")
            if not user_id:
                raise ValueError("Invalid refresh token")
            
            user = self.uow.users.get_by_id(user_id)
            if not user or not user.is_active:
                raise ValueError("User not found or inactive")
            
            # Generate new tokens
            access_token = self._create_access_token(str(user.id), str(user.team_id), user.role.name)
            refresh_token = self._create_refresh_token(str(user.id))
            
            return TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer",
                expires_in=900,
                user=UserResponse(
                    id=str(user.id),
                    username=user.username,
                    email=user.email,
                    name=user.name,
                    team_id=str(user.team_id),
                    role_id=str(user.role_id),
                    role=RoleResponse(
                        id=str(user.role.id),
                        name=user.role.name,
                        permissions=user.role.permissions,
                        description=user.role.description
                    ),
                    is_active=user.is_active,
                    last_login_at=user.last_login_at,
                    created_at=user.created_at,
                    updated_at=user.updated_at
                )
            )
            
        except jwt.ExpiredSignatureError:
            raise ValueError("Refresh token expired")
        except jwt.InvalidTokenError:
            raise ValueError("Invalid refresh token")
    
    def get_current_user(self, token: str) -> UserResponse:
        """Get current user from token."""
        try:
            payload = jwt.decode(token, get_jwt_secret(), algorithms=["HS256"])
            
            user_id = payload.get("sub")
            if not user_id:
                raise ValueError("Invalid token")
            
            user = self.uow.users.get_by_id(user_id)
            if not user or not user.is_active:
                raise ValueError("User not found or inactive")
            
            return UserResponse(
                id=str(user.id),
                username=user.username,
                email=user.email,
                name=user.name,
                team_id=str(user.team_id),
                role_id=str(user.role_id),
                role=RoleResponse(
                    id=str(user.role.id),
                    name=user.role.name,
                    permissions=user.role.permissions,
                    description=user.role.description
                ),
                is_active=user.is_active,
                last_login_at=user.last_login_at,
                created_at=user.created_at,
                updated_at=user.updated_at
            )
            
        except jwt.ExpiredSignatureError:
            raise ValueError("Token expired")
        except jwt.InvalidTokenError:
            raise ValueError("Invalid token")
    
    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt."""
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    
    def _create_access_token(self, user_id: str, team_id: str, role: str) -> str:
        """Create access token."""
        now = datetime.now(timezone.utc)
        payload = {
            "sub": user_id,
            "team_id": team_id,
            "role": role,
            "iat": int(now.timestamp()),
            "exp": int((now + timezone.timedelta(minutes=15)).timestamp()),
            "type": "access"
        }
        return jwt.encode(payload, get_jwt_secret(), algorithm="HS256")
    
    def _create_refresh_token(self, user_id: str) -> str:
        """Create refresh token."""
        now = datetime.now(timezone.utc)
        payload = {
            "sub": user_id,
            "iat": int(now.timestamp()),
            "exp": int((now + timezone.timedelta(days=30)).timestamp()),
            "type": "refresh"
        }
        return jwt.encode(payload, get_jwt_refresh_secret(), algorithm="HS256")

class UserService:
    """Service for user management operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.uow = UnitOfWork(db)
    
    def get_user_by_id(self, user_id: str) -> Optional[UserResponse]:
        """Get user by ID."""
        user = self.uow.users.get_by_id(user_id)
        if not user:
            return None
        
        return UserResponse(
            id=str(user.id),
            username=user.username,
            email=user.email,
            name=user.name,
            team_id=str(user.team_id),
            role_id=str(user.role_id),
            role=RoleResponse(
                id=str(user.role.id),
                name=user.role.name,
                permissions=user.role.permissions,
                description=user.role.description
            ),
            is_active=user.is_active,
            last_login_at=user.last_login_at,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
    
    def get_users_by_team(self, team_id: str) -> List[UserResponse]:
        """Get all users in a team."""
        users = self.uow.users.get_by_team_id(team_id)
        return [
            UserResponse(
                id=str(user.id),
                username=user.username,
                email=user.email,
                name=user.name,
                team_id=str(user.team_id),
                role_id=str(user.role_id),
                role=RoleResponse(
                    id=str(user.role.id),
                    name=user.role.name,
                    permissions=user.role.permissions,
                    description=user.role.description
                ),
                is_active=user.is_active,
                last_login_at=user.last_login_at,
                created_at=user.created_at,
                updated_at=user.updated_at
            )
            for user in users
        ]
    
    def update_user(self, user_id: str, updates: Dict[str, Any]) -> Optional[UserResponse]:
        """Update user information."""
        user = self.uow.users.get_by_id(user_id)
        if not user:
            return None
        
        # Validate updates
        if "email" in updates:
            updates["email"] = InputValidator.validate_email(updates["email"])
        if "name" in updates:
            updates["name"] = InputValidator.validate_name(updates["name"])
        
        # Update user fields
        for key, value in updates.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        user.updated_at = datetime.now(timezone.utc)
        self.uow.users.update(user)
        
        return self.get_user_by_id(user_id)
    
    def deactivate_user(self, user_id: str) -> bool:
        """Deactivate a user."""
        user = self.uow.users.get_by_id(user_id)
        if not user:
            return False
        
        user.is_active = False
        user.updated_at = datetime.now(timezone.utc)
        self.uow.users.update(user)
        
        return True
    
    def activate_user(self, user_id: str) -> bool:
        """Activate a user."""
        user = self.uow.users.get_by_id(user_id)
        if not user:
            return False
        
        user.is_active = True
        user.updated_at = datetime.now(timezone.utc)
        self.uow.users.update(user)
        
        return True

# Dependency injection functions
def get_auth_service(db: Session) -> AuthService:
    """Get auth service instance."""
    return AuthService(db)

def get_user_service(db: Session) -> UserService:
    """Get user service instance."""
    return UserService(db)