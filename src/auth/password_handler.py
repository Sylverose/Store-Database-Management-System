"""
Password hashing and verification operations.
"""

import logging
import bcrypt
from typing import Optional
import pymysql

logger = logging.getLogger(__name__)


class PasswordHandler:
    """Handles password hashing, verification, and changes."""
    
    def __init__(self, db_connection):
        """
        Initialize PasswordHandler.
        
        Args:
            db_connection: Database connection object
        """
        self.db_connection = db_connection
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt.
        
        Args:
            password: Plain text password
            
        Returns:
            str: Hashed password
        """
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            password: Plain text password
            password_hash: Hashed password
            
        Returns:
            bool: True if password matches
        """
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """
        Change a user's password.
        
        Args:
            user_id: User ID
            old_password: Current password (for verification)
            new_password: New password
            
        Returns:
            bool: True if password changed successfully
        """
        try:
            cursor = self.db_connection.cursor(pymysql.cursors.DictCursor)
            query = "SELECT password_hash FROM users WHERE user_id = %s"
            cursor.execute(query, (user_id,))
            user = cursor.fetchone()
            
            if not user:
                logger.error(f"User {user_id} not found")
                cursor.close()
                return False
            
            # Verify old password
            if not self.verify_password(old_password, user['password_hash']):
                logger.warning(f"Invalid old password for user {user_id}")
                cursor.close()
                return False
            
            # Hash new password and update
            new_hash = self.hash_password(new_password)
            update_query = "UPDATE users SET password_hash = %s WHERE user_id = %s"
            cursor.execute(update_query, (new_hash, user_id))
            self.db_connection.commit()
            cursor.close()
            
            logger.info(f"Password changed for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error changing password for user {user_id}: {e}")
            return False
