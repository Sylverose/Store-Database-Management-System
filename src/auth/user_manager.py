"""
User management for authentication system.
Facade that coordinates authentication, password, and repository operations.
"""

import logging
from typing import Optional, Dict, Any, List
from .password_handler import PasswordHandler
from .user_authenticator import UserAuthenticator
from .user_repository import UserRepository

logger = logging.getLogger(__name__)


class UserManager:
    """
    Facade for user management operations.
    Delegates to specialized handlers for authentication, passwords, and data access.
    """
    
    def __init__(self, db_connection):
        """
        Initialize UserManager with specialized handlers.
        
        Args:
            db_connection: Database connection object
        """
        self.db_connection = db_connection
        self.password_handler = PasswordHandler(db_connection)
        self.authenticator = UserAuthenticator(db_connection, self.password_handler)
        self.repository = UserRepository(db_connection, self.password_handler)
    
    # Delegate authentication operations
    def authenticate(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate a user. See UserAuthenticator.authenticate()"""
        return self.authenticator.authenticate(username, password)
    
    # Delegate password operations
    def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """Change user password. See PasswordHandler.change_password()"""
        return self.password_handler.change_password(user_id, old_password, new_password)
    
    # Delegate repository operations
    def create_user(self, username: str, password: str, role: str, staff_id: Optional[int] = None) -> bool:
        """Create a new user. See UserRepository.create_user()"""
        return self.repository.create_user(username, password, role, staff_id)
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID. See UserRepository.get_user_by_id()"""
        return self.repository.get_user_by_id(user_id)
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users. See UserRepository.get_all_users()"""
        return self.repository.get_all_users()
    
    def update_user_role(self, user_id: int, new_role: str) -> bool:
        """Update user role. See UserRepository.update_user_role()"""
        return self.repository.update_user_role(user_id, new_role)
    
    def deactivate_user(self, user_id: int) -> bool:
        """Deactivate user. See UserRepository.deactivate_user()"""
        return self.repository.deactivate_user(user_id)
    
    def activate_user(self, user_id: int) -> bool:
        """Activate user. See UserRepository.activate_user()"""
        return self.repository.activate_user(user_id)
    
    def delete_user(self, user_id: int) -> bool:
        """
        Permanently delete user. See UserRepository.delete_user()
        
        Warning: This is irreversible. Consider using deactivate_user instead.
        """
        return self.repository.delete_user(user_id)
