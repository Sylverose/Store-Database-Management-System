"""
User data access and CRUD operations.
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import pymysql

logger = logging.getLogger(__name__)


class UserRepository:
    """Handles user database operations (CRUD)."""
    
    def __init__(self, db_connection, password_handler):
        """
        Initialize UserRepository.
        
        Args:
            db_connection: Database connection object
            password_handler: PasswordHandler instance for hashing
        """
        self.db_connection = db_connection
        self.password_handler = password_handler
    
    def create_user(self, username: str, password: str, role: str, staff_id: Optional[int] = None) -> bool:
        """
        Create a new user account.
        
        Args:
            username: Unique username
            password: Plain text password (will be hashed)
            role: User role ('Employee', 'Manager', or 'Administrator')
            staff_id: Optional reference to staffs table
            
        Returns:
            bool: True if user created successfully
        """
        try:
            password_hash = self.password_handler.hash_password(password)
            cursor = self.db_connection.cursor()
            query = """
                INSERT INTO users (username, password_hash, role, staff_id, created_at)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(query, (username, password_hash, role, staff_id, datetime.now()))
            self.db_connection.commit()
            cursor.close()
            
            logger.info(f"Created user '{username}' with role '{role}'")
            return True
            
        except pymysql.IntegrityError as e:
            logger.error(f"Failed to create user '{username}': {e}")
            return False
        except Exception as e:
            logger.error(f"Error creating user '{username}': {e}")
            return False
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get user information by user ID.
        
        Args:
            user_id: User ID
            
        Returns:
            Dict with user info or None
        """
        try:
            cursor = self.db_connection.cursor(pymysql.cursors.DictCursor)
            query = """
                SELECT u.user_id, u.username, u.role, u.staff_id, u.active, u.last_login, u.created_at,
                       s.name, s.last_name, s.email, s.phone
                FROM users u
                LEFT JOIN staffs s ON u.staff_id = s.staff_id
                WHERE u.user_id = %s
            """
            cursor.execute(query, (user_id,))
            user = cursor.fetchone()
            cursor.close()
            return user
            
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """
        Get all users sorted by user_id in ascending order.
        
        Returns:
            List of user dictionaries
        """
        try:
            cursor = self.db_connection.cursor(pymysql.cursors.DictCursor)
            query = """
                SELECT u.user_id, u.username, u.role, u.staff_id, u.active, u.last_login, u.created_at,
                       s.name, s.last_name, s.email
                FROM users u
                LEFT JOIN staffs s ON u.staff_id = s.staff_id
                ORDER BY u.user_id ASC
            """
            cursor.execute(query)
            users = cursor.fetchall()
            cursor.close()
            return users
            
        except Exception as e:
            logger.error(f"Error getting all users: {e}")
            return []
    
    def update_user_role(self, user_id: int, new_role: str) -> bool:
        """
        Update a user's role.
        
        Args:
            user_id: User ID
            new_role: New role ('Employee', 'Manager', or 'Administrator')
            
        Returns:
            bool: True if updated successfully
        """
        try:
            cursor = self.db_connection.cursor()
            query = "UPDATE users SET role = %s WHERE user_id = %s"
            cursor.execute(query, (new_role, user_id))
            self.db_connection.commit()
            cursor.close()
            
            logger.info(f"Updated user {user_id} role to '{new_role}'")
            return True
            
        except Exception as e:
            logger.error(f"Error updating user {user_id} role: {e}")
            return False
    
    def set_user_active_status(self, user_id: int, active: bool) -> bool:
        """
        Set a user's active status.
        
        Args:
            user_id: User ID
            active: True to activate, False to deactivate
            
        Returns:
            bool: True if updated successfully
        """
        try:
            cursor = self.db_connection.cursor()
            query = "UPDATE users SET active = %s WHERE user_id = %s"
            cursor.execute(query, (active, user_id))
            self.db_connection.commit()
            cursor.close()
            
            status = "Activated" if active else "Deactivated"
            logger.info(f"{status} user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error changing active status for user {user_id}: {e}")
            return False
    
    def deactivate_user(self, user_id: int) -> bool:
        """Deactivate a user account."""
        return self.set_user_active_status(user_id, False)
    
    def activate_user(self, user_id: int) -> bool:
        """Activate a user account."""
        return self.set_user_active_status(user_id, True)
    
    def delete_user(self, user_id: int) -> bool:
        """
        Permanently delete a user account.
        
        Warning: This is irreversible. Consider using deactivate_user instead.
        
        Args:
            user_id: User ID to delete
            
        Returns:
            bool: True if deleted successfully
        """
        try:
            cursor = self.db_connection.cursor()
            
            # Delete the user
            query = "DELETE FROM users WHERE user_id = %s"
            cursor.execute(query, (user_id,))
            self.db_connection.commit()
            affected_rows = cursor.rowcount
            cursor.close()
            
            if affected_rows > 0:
                logger.warning(f"Permanently deleted user {user_id}")
                return True
            else:
                logger.warning(f"No user found with ID {user_id} to delete")
                return False
            
        except Exception as e:
            logger.error(f"Error deleting user {user_id}: {e}")
            return False
