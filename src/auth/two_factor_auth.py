"""
Two-Factor Authentication (2FA) handler using TOTP (Time-based One-Time Password).
Supports Google Authenticator, Authy, and other TOTP-compatible apps.
"""

import pyotp
import qrcode
import json
import secrets
from io import BytesIO
from typing import List, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class TwoFactorAuth:
    """Handles TOTP-based two-factor authentication."""
    
    def __init__(self, db_connection):
        """Initialize 2FA handler with database connection."""
        self.db_connection = db_connection
        self.app_name = "Store Manager"
    
    def generate_secret(self) -> str:
        """Generate a new TOTP secret key."""
        return pyotp.random_base32()
    
    def generate_qr_code(self, username: str, secret: str) -> bytes:
        """
        Generate QR code for TOTP setup.
        
        Args:
            username: User's username
            secret: TOTP secret key
            
        Returns:
            QR code image as bytes
        """
        # Create provisioning URI
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=username,
            issuer_name=self.app_name
        )
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to bytes
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        return buffer.getvalue()
    
    def verify_code(self, secret: str, code: str) -> bool:
        """
        Verify a TOTP code.
        
        Args:
            secret: User's TOTP secret
            code: 6-digit code to verify
            
        Returns:
            True if code is valid, False otherwise
        """
        try:
            totp = pyotp.TOTP(secret)
            # Allow 1 time step before/after for clock skew
            return totp.verify(code, valid_window=1)
        except Exception as e:
            logger.error(f"Error verifying TOTP code: {e}")
            return False
    
    def generate_backup_codes(self, count: int = 8) -> List[str]:
        """
        Generate backup codes for account recovery.
        
        Args:
            count: Number of backup codes to generate
            
        Returns:
            List of backup codes
        """
        return [secrets.token_hex(4).upper() for _ in range(count)]
    
    def enable_2fa(self, user_id: int, secret: str, backup_codes: List[str]) -> bool:
        """
        Enable 2FA for a user.
        
        Args:
            user_id: User's ID
            secret: TOTP secret key
            backup_codes: List of backup codes
            
        Returns:
            True if successful, False otherwise
        """
        try:
            cursor = self.db_connection.cursor()
            
            # Store backup codes as JSON
            backup_codes_json = json.dumps(backup_codes)
            
            query = """
                UPDATE users 
                SET two_factor_enabled = TRUE,
                    two_factor_secret = %s,
                    backup_codes = %s
                WHERE user_id = %s
            """
            
            cursor.execute(query, (secret, backup_codes_json, user_id))
            self.db_connection.commit()
            cursor.close()
            
            logger.info(f"2FA enabled for user_id: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error enabling 2FA: {e}")
            return False
    
    def disable_2fa(self, user_id: int) -> bool:
        """
        Disable 2FA for a user.
        
        Args:
            user_id: User's ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            cursor = self.db_connection.cursor()
            
            query = """
                UPDATE users 
                SET two_factor_enabled = FALSE,
                    two_factor_secret = NULL,
                    backup_codes = NULL
                WHERE user_id = %s
            """
            
            cursor.execute(query, (user_id,))
            self.db_connection.commit()
            cursor.close()
            
            logger.info(f"2FA disabled for user_id: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error disabling 2FA: {e}")
            return False
    
    def is_2fa_enabled(self, user_id: int) -> bool:
        """
        Check if 2FA is enabled for a user.
        
        Args:
            user_id: User's ID
            
        Returns:
            True if 2FA is enabled, False otherwise
        """
        try:
            cursor = self.db_connection.cursor()
            query = "SELECT two_factor_enabled FROM users WHERE user_id = %s"
            cursor.execute(query, (user_id,))
            result = cursor.fetchone()
            cursor.close()
            
            return result[0] if result else False
            
        except Exception as e:
            logger.error(f"Error checking 2FA status: {e}")
            return False
    
    def get_user_secret(self, user_id: int) -> Optional[str]:
        """
        Get user's TOTP secret.
        
        Args:
            user_id: User's ID
            
        Returns:
            TOTP secret or None
        """
        try:
            cursor = self.db_connection.cursor()
            query = "SELECT two_factor_secret FROM users WHERE user_id = %s"
            cursor.execute(query, (user_id,))
            result = cursor.fetchone()
            cursor.close()
            
            return result[0] if result else None
            
        except Exception as e:
            logger.error(f"Error getting user secret: {e}")
            return None
    
    def verify_backup_code(self, user_id: int, code: str) -> bool:
        """
        Verify and consume a backup code.
        
        Args:
            user_id: User's ID
            code: Backup code to verify
            
        Returns:
            True if code is valid, False otherwise
        """
        try:
            cursor = self.db_connection.cursor()
            
            # Get current backup codes
            query = "SELECT backup_codes FROM users WHERE user_id = %s"
            cursor.execute(query, (user_id,))
            result = cursor.fetchone()
            
            if not result or not result[0]:
                cursor.close()
                return False
            
            backup_codes = json.loads(result[0])
            
            # Check if code exists
            if code.upper() in backup_codes:
                # Remove used code
                backup_codes.remove(code.upper())
                
                # Update database
                update_query = "UPDATE users SET backup_codes = %s WHERE user_id = %s"
                cursor.execute(update_query, (json.dumps(backup_codes), user_id))
                self.db_connection.commit()
                cursor.close()
                
                logger.info(f"Backup code used for user_id: {user_id}")
                return True
            
            cursor.close()
            return False
            
        except Exception as e:
            logger.error(f"Error verifying backup code: {e}")
            return False
    
    def get_remaining_backup_codes(self, user_id: int) -> List[str]:
        """
        Get remaining backup codes for a user.
        
        Args:
            user_id: User's ID
            
        Returns:
            List of remaining backup codes
        """
        try:
            cursor = self.db_connection.cursor()
            query = "SELECT backup_codes FROM users WHERE user_id = %s"
            cursor.execute(query, (user_id,))
            result = cursor.fetchone()
            cursor.close()
            
            if result and result[0]:
                return json.loads(result[0])
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting backup codes: {e}")
            return []
