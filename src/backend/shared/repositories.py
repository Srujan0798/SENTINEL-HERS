from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_
from datetime import datetime, timezone

from src.backend.shared_models import UserModel, TeamModel, RoleModel
from src.backend.auth.models import UserResponse, RoleResponse

class BaseRepository(ABC):
    """Base repository class with common functionality."""
    
    def __init__(self, db: Session):
        self.db = db
    
    @abstractmethod
    def get_by_id(self, id: str) -> Optional[Any]:
        """Get entity by ID."""
        pass
    
    @abstractmethod
    def create(self, entity: Any) -> Any:
        """Create a new entity."""
        pass
    
    @abstractmethod
    def update(self, entity: Any) -> Any:
        """Update an entity."""
        pass
    
    @abstractmethod
    def delete(self, id: str) -> bool:
        """Delete an entity by ID."""
        pass
    
    def commit(self):
        """Commit database changes."""
        self.db.commit()
    
    def rollback(self):
        """Rollback database changes."""
        self.db.rollback()

class UserRepository(BaseRepository):
    """Repository for user-related operations."""
    
    def get_by_id(self, id: str) -> Optional[UserModel]:
        """Get user by ID."""
        return self.db.query(UserModel).filter(UserModel.id == id).first()
    
    def get_by_username(self, username: str) -> Optional[UserModel]:
        """Get user by username."""
        return self.db.query(UserModel).filter(UserModel.username == username).first()
    
    def get_by_email(self, email: str) -> Optional[UserModel]:
        """Get user by email."""
        return self.db.query(UserModel).filter(UserModel.email == email).first()
    
    def get_by_team_id(self, team_id: str) -> List[UserModel]:
        """Get all users in a team."""
        return self.db.query(UserModel).filter(UserModel.team_id == team_id).all()
    
    def create(self, user_data: Dict[str, Any]) -> UserModel:
        """Create a new user."""
        user = UserModel(**user_data)
        self.db.add(user)
        self.commit()
        return user
    
    def update(self, user: UserModel) -> UserModel:
        """Update a user."""
        self.db.commit()
        return user
    
    def delete(self, id: str) -> bool:
        """Delete a user by ID."""
        user = self.get_by_id(id)
        if user:
            self.db.delete(user)
            self.commit()
            return True
        return False
    
    def authenticate(self, username: str, password: str) -> Optional[UserModel]:
        """Authenticate user with username and password."""
        user = self.get_by_username(username)
        if user and user.verify_password(password):
            return user
        return None
    
    def is_active(self, user_id: str) -> bool:
        """Check if user is active."""
        user = self.get_by_id(user_id)
        return user and user.is_active
    
    def update_last_login(self, user_id: str) -> None:
        """Update user's last login timestamp."""
        user = self.get_by_id(user_id)
        if user:
            user.last_login_at = datetime.now(timezone.utc)
            self.commit()

class TeamRepository(BaseRepository):
    """Repository for team-related operations."""
    
    def get_by_id(self, id: str) -> Optional[TeamModel]:
        """Get team by ID."""
        return self.db.query(TeamModel).filter(TeamModel.id == id).first()
    
    def get_by_name(self, name: str) -> Optional[TeamModel]:
        """Get team by name."""
        return self.db.query(TeamModel).filter(TeamModel.name == name).first()
    
    def create(self, team_data: Dict[str, Any]) -> TeamModel:
        """Create a new team."""
        team = TeamModel(**team_data)
        self.db.add(team)
        self.commit()
        return team
    
    def update(self, team: TeamModel) -> TeamModel:
        """Update a team."""
        self.db.commit()
        return team
    
    def delete(self, id: str) -> bool:
        """Delete a team by ID."""
        team = self.get_by_id(id)
        if team:
            self.db.delete(team)
            self.commit()
            return True
        return False
    
    def get_all_teams(self) -> List[TeamModel]:
        """Get all teams."""
        return self.db.query(TeamModel).all()

class RoleRepository(BaseRepository):
    """Repository for role-related operations."""
    
    def get_by_id(self, id: str) -> Optional[RoleModel]:
        """Get role by ID."""
        return self.db.query(RoleModel).filter(RoleModel.id == id).first()
    
    def get_by_name(self, name: str) -> Optional[RoleModel]:
        """Get role by name."""
        return self.db.query(RoleModel).filter(RoleModel.name == name).first()
    
    def create(self, role_data: Dict[str, Any]) -> RoleModel:
        """Create a new role."""
        role = RoleModel(**role_data)
        self.db.add(role)
        self.commit()
        return role
    
    def update(self, role: RoleModel) -> RoleModel:
        """Update a role."""
        self.db.commit()
        return role
    
    def delete(self, id: str) -> bool:
        """Delete a role by ID."""
        role = self.get_by_id(id)
        if role:
            self.db.delete(role)
            self.commit()
            return True
        return False
    
    def get_all_roles(self) -> List[RoleModel]:
        """Get all roles."""
        return self.db.query(RoleModel).all()
    
    def assign_role_to_user(self, user_id: str, role_id: str) -> bool:
        """Assign a role to a user."""
        user = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        role = self.get_by_id(role_id)
        
        if user and role:
            user.role_id = role_id
            self.commit()
            return True
        return False

class UnitOfWork:
    """Unit of Work pattern for managing database transactions."""
    
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)
        self.teams = TeamRepository(db)
        self.roles = RoleRepository(db)
        self._committed = False
    
    def commit(self):
        """Commit all changes."""
        if not self._committed:
            self.db.commit()
            self._committed = True
    
    def rollback(self):
        """Rollback all changes."""
        self.db.rollback()
        self._committed = False
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()