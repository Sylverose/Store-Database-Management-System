"""
User authentication and verification.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class UserAuthenticator:
    """Handles user authentication and login tracking."""
    
    def __init__(self, db_connection, password_handler):
        """
        Initialize UserAuthenticator.
        
        Args:
            db_connection: Database connection object
            password_handler: PasswordHandler instance for verification
        """
        self.db_connection = db_connection
        self.password_handler = password_handler
    
    def authenticate(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate a user with username and password.
        
        Args:
            username: Username
            password: Plain text password
            
        Returns:
            Dict with user info if authenticated, None otherwise
        """
        try:
            # Try mysql.connector style first, then PyMySQL style
            try:
                cursor = self.db_connection.cursor(dictionary=True)
            except TypeError:
                # If dictionary=True fails, try PyMySQL style
                import pymysql.cursors
                cursor = self.db_connection.cursor(pymysql.cursors.DictCursor)
            
            query = """
                SELECT u.user_id, u.username, u.password_hash, u.role, u.staff_id, u.active,
                       s.name, s.last_name, s.email
                FROM users u
                LEFT JOIN staffs s ON u.staff_id = s.staff_id
                WHERE u.username = %s
            """
            cursor.execute(query, (username,))
            user = cursor.fetchone()
            cursor.close()
            
            if not user:
                logger.warning(f"Authentication failed: User '{username}' not found")
                return None
            
            if not user['active']:
                logger.warning(f"Authentication failed: User '{username}' is inactive")
                return None
            
            # Verify password
            if self.password_handler.verify_password(password, user['password_hash']):
                self._update_last_login(user['user_id'])
                del user['password_hash']  # Remove hash from returned data
                logger.info(f"User '{username}' authenticated successfully")
                return user
            else:
                logger.warning(f"Authentication failed: Invalid password for user '{username}'")
                return None
                
        except Exception as e:
            logger.error(f"Error authenticating user '{username}': {e}")
            return None
    
    def _update_last_login(self, user_id: int):
        """Update the last_login timestamp for a user."""
        try:
            cursor = self.db_connection.cursor()
            query = "UPDATE users SET last_login = %s WHERE user_id = %s"
            cursor.execute(query, (datetime.now(), user_id))
            self.db_connection.commit()
            cursor.close()
        except Exception as e:
            logger.error(f"Error updating last login for user_id {user_id}: {e}")
