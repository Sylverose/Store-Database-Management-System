"""
Account Lockout Manager
Handles account locking after failed login attempts
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class LockoutInfo:
    """Information about account lockout status"""
    is_locked: bool
    failed_attempts: int
    locked_until: Optional[datetime]
    last_failed_attempt: Optional[datetime]
    
    def time_remaining(self) -> int:
        """Get seconds remaining in lockout"""
        if not self.is_locked or not self.locked_until:
            return 0
        remaining = (self.locked_until - datetime.now()).total_seconds()
        return max(0, int(remaining))
    
    def is_lockout_expired(self) -> bool:
        """Check if lockout period has expired"""
        if not self.is_locked or not self.locked_until:
            return False
        return datetime.now() >= self.locked_until


class AccountLockoutManager:
    """Manages account lockout after failed login attempts"""
    
    def __init__(self, 
                 max_attempts: int = 5,
                 lockout_duration_minutes: int = 15,
                 db_manager=None):
        """
        Initialize account lockout manager
        
        Args:
            max_attempts: Maximum failed login attempts before lockout
            lockout_duration_minutes: Duration of lockout in minutes
            db_manager: Database manager for persistent storage
        """
        self.max_attempts = max_attempts
        self.lockout_duration_minutes = lockout_duration_minutes
        self.db_manager = db_manager
        
        # In-memory cache for lockout info (username -> LockoutInfo)
        self._lockout_cache: Dict[str, LockoutInfo] = {}
        
        logger.info(f"Account lockout manager initialized: {max_attempts} attempts, "
                   f"{lockout_duration_minutes} min lockout")
    
    def record_failed_attempt(self, username: str) -> LockoutInfo:
        """
        Record a failed login attempt
        
        Args:
            username: Username that failed login
            
        Returns:
            LockoutInfo with updated status
        """
        info = self.get_lockout_info(username)
        
        # Increment failed attempts
        info.failed_attempts += 1
        info.last_failed_attempt = datetime.now()
        
        # Lock account if max attempts exceeded
        if info.failed_attempts >= self.max_attempts:
            info.is_locked = True
            info.locked_until = datetime.now() + timedelta(minutes=self.lockout_duration_minutes)
            logger.warning(f"Account '{username}' locked after {info.failed_attempts} failed attempts. "
                          f"Locked until {info.locked_until}")
        else:
            logger.info(f"Failed login attempt for '{username}': "
                       f"{info.failed_attempts}/{self.max_attempts}")
        
        # Update cache and database
        self._lockout_cache[username] = info
        self._persist_lockout_info(username, info)
        
        return info
    
    def record_successful_login(self, username: str) -> None:
        """
        Record successful login and clear failed attempts
        
        Args:
            username: Username that logged in successfully
        """
        info = LockoutInfo(
            is_locked=False,
            failed_attempts=0,
            locked_until=None,
            last_failed_attempt=None
        )
        
        self._lockout_cache[username] = info
        self._persist_lockout_info(username, info)
        
        logger.info(f"Successful login for '{username}', lockout info cleared")
    
    def get_lockout_info(self, username: str) -> LockoutInfo:
        """
        Get current lockout info for username
        
        Args:
            username: Username to check
            
        Returns:
            LockoutInfo for the user
        """
        # Check cache first
        if username in self._lockout_cache:
            info = self._lockout_cache[username]
            
            # Check if lockout has expired
            if info.is_locked and info.is_lockout_expired():
                logger.info(f"Lockout expired for '{username}', resetting")
                info.is_locked = False
                info.failed_attempts = 0
                info.locked_until = None
                self._persist_lockout_info(username, info)
            
            return info
        
        # Load from database if available
        if self.db_manager:
            info = self._load_lockout_info(username)
            if info:
                self._lockout_cache[username] = info
                return info
        
        # Return default (not locked)
        return LockoutInfo(
            is_locked=False,
            failed_attempts=0,
            locked_until=None,
            last_failed_attempt=None
        )
    
    def is_account_locked(self, username: str) -> bool:
        """
        Check if account is currently locked
        
        Args:
            username: Username to check
            
        Returns:
            True if account is locked, False otherwise
        """
        info = self.get_lockout_info(username)
        return info.is_locked and not info.is_lockout_expired()
    
    def unlock_account(self, username: str) -> None:
        """
        Manually unlock account (admin function)
        
        Args:
            username: Username to unlock
        """
        info = LockoutInfo(
            is_locked=False,
            failed_attempts=0,
            locked_until=None,
            last_failed_attempt=None
        )
        
        self._lockout_cache[username] = info
        self._persist_lockout_info(username, info)
        
        logger.info(f"Account '{username}' manually unlocked by administrator")
    
    def _persist_lockout_info(self, username: str, info: LockoutInfo) -> None:
        """Save lockout info to database"""
        if not self.db_manager:
            return
        
        try:
            # Store in users table (failed_login_attempts, locked_until columns)
            query = """
                UPDATE users 
                SET failed_login_attempts = %s,
                    locked_until = %s,
                    last_failed_attempt = %s
                WHERE username = %s
            """
            
            params = (
                info.failed_attempts,
                info.locked_until,
                info.last_failed_attempt,
                username
            )
            
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to persist lockout info for '{username}': {e}")
    
    def _load_lockout_info(self, username: str) -> Optional[LockoutInfo]:
        """Load lockout info from database"""
        if not self.db_manager:
            return None
        
        try:
            query = """
                SELECT failed_login_attempts, locked_until, last_failed_attempt
                FROM users
                WHERE username = %s
            """
            
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (username,))
                row = cursor.fetchone()
                
                if row:
                    failed_attempts, locked_until, last_failed_attempt = row
                    
                    return LockoutInfo(
                        is_locked=locked_until is not None and datetime.now() < locked_until,
                        failed_attempts=failed_attempts or 0,
                        locked_until=locked_until,
                        last_failed_attempt=last_failed_attempt
                    )
        except Exception as e:
            logger.error(f"Failed to load lockout info for '{username}': {e}")
        
        return None
    
    def get_attempts_remaining(self, username: str) -> int:
        """
        Get number of login attempts remaining before lockout
        
        Args:
            username: Username to check
            
        Returns:
            Number of attempts remaining
        """
        info = self.get_lockout_info(username)
        return max(0, self.max_attempts - info.failed_attempts)
