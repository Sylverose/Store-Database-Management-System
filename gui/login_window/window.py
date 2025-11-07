"""
Login window for user authentication.
Provides login interface and handles authentication flow.
"""

import sys
import logging
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QMessageBox
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon

from .ui_components import LoginForm
from .worker import LoginWorker

logger = logging.getLogger(__name__)


class LoginWindow(QMainWindow):
    """Main login window for user authentication."""
    
    # Signal emitted when login is successful
    login_successful = Signal(object)  # user_data
    
    def __init__(self, user_manager, session_manager):
        """
        Initialize LoginWindow.
        
        Args:
            user_manager: UserManager instance for authentication
            session_manager: SessionManager instance for session handling
        """
        super().__init__()
        self.user_manager = user_manager
        self.session_manager = session_manager
        self.worker = None
        
        self.setup_ui()
        # Don't apply custom styles - use theme system
    
    def setup_ui(self):
        """Setup the login window UI."""
        self.setWindowTitle("Login - Store Database Management")
        self.setObjectName("login_window")
        self.setFixedSize(450, 500)
        
        # Center window on screen
        self.center_on_screen()
        
        # Create central widget
        central_widget = QWidget()
        central_widget.setObjectName("login_form")
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add login form
        self.login_form = LoginForm()
        self.login_form.login_requested.connect(self.on_login_requested)
        main_layout.addWidget(self.login_form)
    
    def center_on_screen(self):
        """Center the window on the screen."""
        from PySide6.QtGui import QGuiApplication
        screen = QGuiApplication.primaryScreen().geometry()
        window_geometry = self.frameGeometry()
        center_point = screen.center()
        window_geometry.moveCenter(center_point)
        self.move(window_geometry.topLeft())
    
    def on_login_requested(self, username: str, password: str):
        """
        Handle login request.
        
        Args:
            username: Username entered
            password: Password entered
        """
        logger.info(f"Login requested for username: {username}")
        
        # Create and start worker thread
        self.worker = LoginWorker(self.user_manager, username, password)
        self.worker.authentication_complete.connect(self.on_authentication_complete)
        self.worker.start()
    
    def on_authentication_complete(self, success: bool, user_data: object):
        """
        Handle authentication completion.
        
        Args:
            success: Whether authentication was successful
            user_data: User data if successful, None otherwise
        """
        # Reset login button
        self.login_form.reset_login_button()
        
        if success:
            logger.info(f"Login successful for user: {user_data.get('username')}")
            
            # Start session
            self.session_manager.login(user_data)
            
            # Show success message
            self.login_form.show_success("Login successful!")
            
            # Emit success signal
            self.login_successful.emit(user_data)
            
            # Close login window
            self.close()
        else:
            logger.warning("Login failed: Invalid credentials")
            self.login_form.show_error("Invalid username or password")
    
    def closeEvent(self, event):
        """Handle window close event."""
        # If worker is still running, wait for it
        if self.worker and self.worker.isRunning():
            self.worker.wait()
        event.accept()
