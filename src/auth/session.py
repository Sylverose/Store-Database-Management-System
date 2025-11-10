"""
Session management for tracking authenticated users.
Provides singleton session manager to maintain current user state.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class SessionManager:
    """Singleton session manager for tracking the current logged-in user."""
    
    _instance = None
    _current_user: Optional[Dict[str, Any]] = None
    _login_time: Optional[datetime] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SessionManager, cls).__new__(cls)
        return cls._instance
    
    def login(self, user_data: Dict[str, Any]) -> bool:
        """
        Set the current logged-in user.
        
        Args:
            user_data: Dictionary with user information from authentication
            
        Returns:
            bool: True if session started successfully
        """
        try:
            self._current_user = user_data.copy()
            self._login_time = datetime.now()
            logger.info(f"Session started for user '{user_data.get('username')}' with role '{user_data.get('role')}'")
            # Explicitly reinitialize connection pool on login
            try:
                from src.database.connection_manager import DatabaseConnection
                DatabaseConnection.close_pool()
                logger.info("Database connection pool forcibly reset on login.")
                DatabaseConnection.reinitialize_pool()
                logger.info("Database connection pool reinitialized on login.")
            except Exception as e:
                logger.warning(f"Failed to reset/reinitialize connection pool on login: {e}")
            return True
        except Exception as e:
            logger.error(f"Error starting session: {e}")
            return False
    
    def logout(self):
        """Clear the current session."""
        if self._current_user:
            username = self._current_user.get('username', 'unknown')
            logger.info(f"Session ended for user '{username}'")
        self._current_user = None
        self._login_time = None
        # Force database connection pool reset and reinit on logout
        try:
            from src.database.connection_manager import DatabaseConnection
            DatabaseConnection.close_pool()
            logger.info("Database connection pool forcibly reset on logout.")
            DatabaseConnection.reinitialize_pool()
            logger.info("Database connection pool reinitialized on logout.")
        except Exception as e:
            logger.warning(f"Failed to reset/reinitialize connection pool on logout: {e}")
    
    def is_logged_in(self) -> bool:
        """Check if a user is currently logged in."""
        return self._current_user is not None
    
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """
        Get the current logged-in user data.
        
        Returns:
            Dict with user information or None if not logged in
        """
        return self._current_user.copy() if self._current_user else None
    
    def get_user_id(self) -> Optional[int]:
        """Get the current user's ID."""
        return self._current_user.get('user_id') if self._current_user else None
    
    def get_username(self) -> Optional[str]:
        """Get the current user's username."""
        return self._current_user.get('username') if self._current_user else None
    
    def get_role(self) -> Optional[str]:
        """Get the current user's role."""
        return self._current_user.get('role') if self._current_user else None
    
    def get_staff_id(self) -> Optional[int]:
        """Get the current user's staff ID."""
        return self._current_user.get('staff_id') if self._current_user else None
    
    def get_login_time(self) -> Optional[datetime]:
        """Get the time when the current user logged in."""
        return self._login_time
    
    def update_user_data(self, updated_data: Dict[str, Any]):
        """
        Update the current user's session data.
        
        Args:
            updated_data: Dictionary with updated user information
        """
        if self._current_user:
            self._current_user.update(updated_data)
            logger.debug(f"Updated session data for user '{self._current_user.get('username')}'")
