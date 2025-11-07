"""
Session Timeout Manager
Handles automatic logout after inactivity period
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Callable
from PySide6.QtCore import QTimer, QObject, Signal

logger = logging.getLogger(__name__)


class SessionTimeoutManager(QObject):
    """Manages session timeout with inactivity tracking"""
    
    # Signals
    timeout_warning = Signal(int)  # seconds remaining
    timeout_occurred = Signal()  # session timed out
    
    def __init__(self, 
                 timeout_minutes: int = 30, 
                 warning_seconds: int = 60,
                 parent: Optional[QObject] = None):
        """
        Initialize session timeout manager
        
        Args:
            timeout_minutes: Minutes of inactivity before timeout
            warning_seconds: Seconds before timeout to show warning
            parent: Parent QObject
        """
        super().__init__(parent)
        
        self.timeout_minutes = timeout_minutes
        self.warning_seconds = warning_seconds
        self.last_activity: Optional[datetime] = None
        self.is_active = False
        
        # Timer to check for inactivity
        self.check_timer = QTimer(self)
        self.check_timer.timeout.connect(self._check_inactivity)
        self.check_timer.setInterval(1000)  # Check every second
        
        # Warning state
        self.warning_shown = False
        
        logger.info(f"Session timeout manager initialized: {timeout_minutes} min timeout, "
                   f"{warning_seconds}s warning")
    
    def start(self) -> None:
        """Start monitoring session activity"""
        self.last_activity = datetime.now()
        self.is_active = True
        self.warning_shown = False
        self.check_timer.start()
        logger.info("Session timeout monitoring started")
    
    def stop(self) -> None:
        """Stop monitoring session activity"""
        self.is_active = False
        self.check_timer.stop()
        self.warning_shown = False
        logger.info("Session timeout monitoring stopped")
    
    def reset(self) -> None:
        """Reset activity timer (user performed an action)"""
        self.last_activity = datetime.now()
        self.warning_shown = False
    
    def get_time_remaining(self) -> int:
        """Get seconds remaining before timeout"""
        if not self.is_active or not self.last_activity:
            return self.timeout_minutes * 60
        
        timeout_time = self.last_activity + timedelta(minutes=self.timeout_minutes)
        remaining = (timeout_time - datetime.now()).total_seconds()
        return max(0, int(remaining))
    
    def _check_inactivity(self) -> None:
        """Check if session has been inactive too long"""
        if not self.is_active or not self.last_activity:
            return
        
        remaining_seconds = self.get_time_remaining()
        
        # Timeout occurred
        if remaining_seconds <= 0:
            logger.warning("Session timeout occurred due to inactivity")
            self.stop()
            self.timeout_occurred.emit()
            return
        
        # Show warning if approaching timeout
        if remaining_seconds <= self.warning_seconds and not self.warning_shown:
            logger.info(f"Session timeout warning: {remaining_seconds}s remaining")
            self.warning_shown = True
            self.timeout_warning.emit(remaining_seconds)
    
    def get_inactive_duration(self) -> int:
        """Get seconds since last activity"""
        if not self.last_activity:
            return 0
        return int((datetime.now() - self.last_activity).total_seconds())
