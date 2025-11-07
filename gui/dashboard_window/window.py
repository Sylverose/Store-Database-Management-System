"""Dashboard window class for ETL Pipeline Manager"""

import sys
import os
import subprocess
import logging
from datetime import datetime
from typing import Optional

sys.dont_write_bytecode = True
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

logger = logging.getLogger(__name__)

# Windows-specific flag to hide console window
if sys.platform == "win32":
    CREATE_NO_WINDOW = 0x08000000
else:
    CREATE_NO_WINDOW = 0

from PySide6.QtWidgets import (QMainWindow, QVBoxLayout, QWidget, QPushButton, 
                               QListWidget, QMessageBox, QApplication, QHBoxLayout,
                               QMenu, QToolBar, QComboBox, QLabel, QGroupBox)
from PySide6.QtCore import Qt, QSettings, Signal
from PySide6.QtGui import QFont, QAction

try:
    from qt_material import apply_stylesheet
    QT_MATERIAL_AVAILABLE = True
except ImportError:
    QT_MATERIAL_AVAILABLE = False

from .worker import DashboardWorker, MODULES_AVAILABLE
from .ui_components import (create_title_section, create_manage_section,
                            create_tables_section, create_theme_section)
from .gauge_widget import SalesGaugeWidget
from themes import ThemeManager
from auth.session import SessionManager  # type: ignore
from auth.permissions import PermissionManager  # type: ignore
from user_management import UserManagementDialog  # type: ignore
from two_factor_setup_dialog import TwoFactorSetupDialog  # type: ignore


class DashboardMainWindow(QMainWindow):
    """Dashboard window with clean architecture and theme support"""
    
    logout_requested = Signal()  # Signal emitted when user clicks logout
    admin_window_requested = Signal()  # Signal to open admin window in tab
    user_management_requested = Signal()  # Signal to open user management in tab
    
    def __init__(self, theme_manager=None):
        super().__init__()
        self.current_worker: Optional[DashboardWorker] = None
        self.admin_window_process: Optional[subprocess.Popen] = None
        self.settings = QSettings("ETL Solutions", "ETL Pipeline Dashboard")
        
        # Use provided theme manager or create new one (for standalone use)
        self.theme_manager = theme_manager if theme_manager else ThemeManager()
        self._owns_theme_manager = theme_manager is None
        
        self._setup_ui()
        self._load_settings()
        self._initialize_dashboard()
    
    def _setup_ui(self):
        """Set up the user interface"""
        self.setWindowTitle("ETL Pipeline Dashboard")
        self.setGeometry(100, 100, 1050, 850)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        self._create_ui_sections(main_layout)
        self._create_toolbar()
        
        main_layout.addStretch()
        
        self.statusBar().showMessage("Ready")
    
    def _create_ui_sections(self, layout: QVBoxLayout):
        """Create all UI sections"""
        # Title section moved to toolbar
        
        # Combined section: Data Management buttons + Customer Report
        manage_group = QGroupBox("Database Management")
        manage_layout = QHBoxLayout(manage_group)
        
        # Manage Database button
        self.manage_db_btn = QPushButton("Manage Database")
        self.manage_db_btn.setObjectName("manage_db_btn")
        self.manage_db_btn.clicked.connect(self.open_admin_window)
        manage_layout.addWidget(self.manage_db_btn)
        
        # Manage Users button (only for Administrators)
        self.manage_users_btn = QPushButton("Manage Users")
        self.manage_users_btn.setObjectName("manage_users_btn")
        self.manage_users_btn.clicked.connect(self.open_user_management)
        manage_layout.addWidget(self.manage_users_btn)
        
        # Check if user is Administrator
        session = SessionManager()
        user_role = session.get_role()
        
        if user_role != "Administrator":
            # Hide Manage Users button for non-Administrators
            self.manage_users_btn.hide()
        
        # Add spacer to push customer report to the right
        manage_layout.addStretch()
        
        # Customer Report Section (inline on the right)
        report_label = QLabel("Customer Report:")
        manage_layout.addWidget(report_label)
        
        # Customer dropdown with search
        self.customer_combo = QComboBox()
        self.customer_combo.setEditable(True)  # Enable search/filter
        self.customer_combo.setPlaceholderText("Search customer...")
        self.customer_combo.setMinimumWidth(250)
        manage_layout.addWidget(self.customer_combo)
        
        # Generate PDF button
        self.generate_pdf_btn = QPushButton("Generate PDF")
        self.generate_pdf_btn.setObjectName("generate_pdf_btn")
        self.generate_pdf_btn.clicked.connect(self.generate_customer_pdf)
        manage_layout.addWidget(self.generate_pdf_btn)
        
        layout.addWidget(manage_group)
        
        # Employee List Section (Manager/Admin only)
        session = SessionManager()
        user_role = session.get_role()
        if user_role in ["Manager", "Administrator"]:
            self._create_employee_list_section(layout)
        
        # Create horizontal layout for gauge and tables side by side
        content_layout = QHBoxLayout()
        
        # Left side: Tables list (takes up more space)
        tables_container = QVBoxLayout()
        self.tables_list = QListWidget()
        create_tables_section(tables_container, self.tables_list)
        
        # Right side: Sales gauge chart (fixed width)
        gauge_container = QVBoxLayout()
        self.sales_gauge = SalesGaugeWidget()
        self.sales_gauge.setMinimumSize(350, 350)
        self.sales_gauge.setMaximumWidth(400)
        gauge_container.addWidget(self.sales_gauge)
        gauge_container.addStretch()  # Push gauge to top
        
        # Add both sides to horizontal layout
        # Tables take 60% of width, gauge takes 40%
        content_layout.addLayout(tables_container, 60)
        content_layout.addLayout(gauge_container, 40)
        
        # Add the horizontal layout to main layout
        layout.addLayout(content_layout)
        
        # Theme section removed - now in settings menu
        
        # Logout button
        self.logout_btn = QPushButton("Logout")
        self.logout_btn.setObjectName("logout_btn")
        self.logout_btn.clicked.connect(self.logout)
        self._create_logout_section(layout, self.logout_btn)
    
    def _create_logout_section(self, layout: QVBoxLayout, logout_btn: QPushButton):
        """Create logout button section"""
        from PySide6.QtWidgets import QGroupBox
        
        logout_group = QGroupBox("Session")
        logout_layout = QHBoxLayout(logout_group)
        
        # Show current user info
        session = SessionManager()
        username = session.get_username()
        role = session.get_role()
        
        from PySide6.QtWidgets import QLabel
        user_info_label = QLabel(f"Logged in as: {username} ({role})")
        user_info_label.setObjectName("user_info_label")
        
        logout_layout.addWidget(user_info_label)
        logout_layout.addStretch()
        logout_layout.addWidget(logout_btn)
        
        layout.addWidget(logout_group)
    
    def _create_employee_list_section(self, layout: QVBoxLayout):
        """Create employee list section (Manager/Admin only)"""
        from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
        
        employee_group = QGroupBox("Employee Users")
        employee_layout = QVBoxLayout(employee_group)
        
        # Create table widget
        self.employee_table = QTableWidget()
        self.employee_table.setColumnCount(2)
        self.employee_table.setHorizontalHeaderLabels(['Name', 'Email'])
        
        # Configure table
        self.employee_table.setAlternatingRowColors(True)
        self.employee_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.employee_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.employee_table.horizontalHeader().setStretchLastSection(True)
        self.employee_table.setMaximumHeight(200)
        
        # Auto-resize columns to content
        header = self.employee_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        employee_layout.addWidget(self.employee_table)
        
        layout.addWidget(employee_group)
    
    def _create_toolbar(self):
        """Create toolbar with title on left, settings on right"""
        from PySide6.QtWidgets import QSizePolicy
        
        toolbar = self.addToolBar("Main Toolbar")
        toolbar.setMovable(False)
        
        # Title label on the left
        title_label = QLabel("ETL Pipeline Dashboard")
        title_label.setObjectName("toolbar_title_label")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("padding: 5px 10px;")
        toolbar.addWidget(title_label)
        
        # Add spacer to push settings to the right
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)
        
        # Settings action with gear icon only - no hover effects
        settings_action = QAction("⚙", self)
        settings_action.setObjectName("settings_action")
        settings_action.triggered.connect(self.show_settings_menu)
        toolbar.addAction(settings_action)
        
        self.toolbar = toolbar
    
    def show_settings_menu(self):
        """Show settings menu when toolbar button is clicked"""
        from PySide6.QtCore import QPoint
        
        menu = QMenu(self)
        
        # Theme toggle action
        theme_action = QAction("Toggle Theme", self)
        theme_action.triggered.connect(self.toggle_theme)
        menu.addAction(theme_action)
        
        # Security Settings action (2FA)
        security_action = QAction("Security Settings (2FA)", self)
        security_action.triggered.connect(self.show_security_settings)
        menu.addAction(security_action)
        
        # Get the settings action widget position
        for action in self.toolbar.actions():
            if action.text() == "⚙":
                widget = self.toolbar.widgetForAction(action)
                if widget:
                    # Show menu directly below the button
                    pos = widget.mapToGlobal(QPoint(0, widget.height()))
                    menu.exec(pos)
                    return
        
        # Fallback: show at toolbar position
        menu.exec(self.toolbar.mapToGlobal(self.toolbar.rect().topRight()))
    
    def _load_settings(self):
        """Load user settings"""
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        
        # Only load theme settings if we own the theme manager (standalone mode)
        if self._owns_theme_manager:
            saved_theme = self.settings.value("theme/current_theme", "dark", type=str)
            self.theme_manager.set_theme(saved_theme)
            self._apply_theme()
    
    def _save_settings(self):
        """Save user settings"""
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("theme/current_theme", self.theme_manager.get_current_theme_name())
    
    def _initialize_dashboard(self):
        """Initialize dashboard and load table list"""
        if MODULES_AVAILABLE:
            self.statusBar().showMessage("Loading database tables...")
            self._start_operation("fetch_tables")
            # Also fetch sales data for gauge
            self._fetch_sales_data()
            # Load customers for dropdown
            self._load_customers()
            # Load employees for Manager/Admin
            session = SessionManager()
            user_role = session.get_role()
            if user_role in ["Manager", "Administrator"]:
                self._load_employees()
        else:
            self.tables_list.addItem("⚠️ Database modules not available")
            self.statusBar().showMessage("Database modules not available")
    
    def _load_customers(self):
        """Load customers into dropdown"""
        logger.info("Starting customer load...")
        worker = DashboardWorker("fetch_customers")
        worker.customers_loaded.connect(self._on_customers_loaded)
        worker.error.connect(lambda msg: logger.error(f"Customer fetch error: {msg}"))
        worker.finished.connect(worker.deleteLater)
        worker.start()
    
    def _on_customers_loaded(self, customers: list):
        """Handle customers data loaded"""
        logger.info(f"Customer data received: {len(customers)} customers")
        self.customer_combo.clear()
        self.customer_combo.addItem("-- Select a customer --", None)
        for customer in customers:
            customer_id = customer['customer_id']
            name = f"{customer['first_name']} {customer['last_name']}"
            display_text = f"{name} (ID: {customer_id})"
            self.customer_combo.addItem(display_text, customer_id)
        logger.info("Customer dropdown populated successfully")
    
    def _load_employees(self):
        """Load employees into table"""
        worker = DashboardWorker("fetch_employees")
        worker.employees_loaded.connect(self._on_employees_loaded)
        worker.error.connect(lambda msg: logger.error(f"Employee fetch error: {msg}"))
        worker.finished.connect(worker.deleteLater)
        worker.start()
    
    def _on_employees_loaded(self, employees: list):
        """Handle employees data loaded"""
        from PySide6.QtWidgets import QTableWidgetItem
        
        self.employee_table.setRowCount(len(employees))
        
        for row, emp in enumerate(employees):
            name = f"{emp.get('name', '')} {emp.get('last_name', '')}"
            self.employee_table.setItem(row, 0, QTableWidgetItem(name))
            self.employee_table.setItem(row, 1, QTableWidgetItem(emp.get('email', 'N/A')))
    
    def generate_customer_pdf(self):
        """Generate PDF report for selected customer"""
        customer_id = self.customer_combo.currentData()
        if not customer_id:
            QMessageBox.warning(self, "No Customer Selected", "Please select a customer from the dropdown.")
            return
        
        # Start worker to generate PDF
        self.statusBar().showMessage(f"Generating PDF report for customer {customer_id}...")
        worker = DashboardWorker("generate_customer_pdf", customer_id)
        worker.pdf_generated.connect(self._on_pdf_generated)
        worker.error.connect(lambda msg: QMessageBox.critical(self, "PDF Generation Failed", msg))
        worker.finished.connect(worker.deleteLater)
        worker.start()
    
    def _on_pdf_generated(self, filepath: str):
        """Handle PDF generation complete"""
        self.statusBar().showMessage(f"PDF report generated successfully!", 5000)
        
        # Ask if user wants to open the PDF
        reply = QMessageBox.question(
            self,
            "PDF Generated",
            f"Report saved to:\n{filepath}\n\nWould you like to open it?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            import os
            import subprocess
            if sys.platform == "win32":
                os.startfile(filepath)
            elif sys.platform == "darwin":  # macOS
                subprocess.run(["open", filepath])
            else:  # linux
                subprocess.run(["xdg-open", filepath])
    
    def _fetch_sales_data(self):
        """Fetch sales data for gauge chart"""
        worker = DashboardWorker("fetch_sales")
        worker.sales_data_loaded.connect(self._on_sales_loaded)
        worker.error.connect(lambda msg: logger.error(f"Sales fetch error: {msg}"))
        worker.finished.connect(worker.deleteLater)
        worker.start()
    
    def _on_sales_loaded(self, total_sales: float):
        """Handle sales data loaded"""
        self.sales_gauge.set_sales_data(total_sales)
    
    def _apply_theme(self):
        """Apply current theme using theme manager"""
        app = QApplication.instance()
        self.theme_manager.apply_current_theme(app)
    
    def toggle_theme(self):
        """Toggle between light and dark theme"""
        self.theme_manager.toggle_theme()
        self._apply_theme()
        self.update()
        self.repaint()
        theme_name = self.theme_manager.get_current_theme_name()
        self.statusBar().showMessage(f"Switched to {theme_name} theme")
    
    def show_security_settings(self):
        """Show 2FA security settings dialog"""
        session = SessionManager()
        user_id = session.get_user_id()
        username = session.get_username()
        
        if not user_id:
            QMessageBox.warning(self, "Error", "Unable to determine current user")
            return
        
        # Get database connection from connect module
        from connect import connect_to_mysql
        from config import DatabaseConfig
        
        try:
            db_config = DatabaseConfig().to_dict()
            db_conn = connect_to_mysql(db_config)
            
            if not db_conn:
                QMessageBox.warning(self, "Error", "Could not connect to database")
                return
            
            # Open 2FA setup dialog
            dialog = TwoFactorSetupDialog(user_id, username, db_conn, self)
            dialog.setup_completed.connect(self._on_2fa_setup_completed)
            dialog.exec()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to open security settings: {str(e)}")
    
    def _on_2fa_setup_completed(self, enabled: bool):
        """Handle 2FA setup completion"""
        if enabled:
            self.statusBar().showMessage("Two-Factor Authentication enabled successfully")
        else:
            self.statusBar().showMessage("Two-Factor Authentication disabled")
    
    def open_admin_window(self):
        """Request to open admin window as tab."""
        self.admin_window_requested.emit()
        self.statusBar().showMessage("Opening admin window...")
    
    def open_user_management(self):
        """Request to open user management as tab (Administrator only)."""
        # Double-check permissions
        session = SessionManager()
        user_role = session.get_role()
        
        if user_role != "Administrator":
            QMessageBox.warning(
                self,
                "Access Denied",
                "Only Administrators can manage users."
            )
            return
        
        self.user_management_requested.emit()
        self.statusBar().showMessage("Opening user management...")
    
    def _start_operation(self, operation: str):
        """Start background operation"""
        if self.current_worker and self.current_worker.isRunning():
            return
        
        self.current_worker = DashboardWorker(operation)
        self.current_worker.progress.connect(self._on_progress)
        self.current_worker.finished.connect(self._on_operation_finished)
        self.current_worker.error.connect(self._on_operation_error)
        
        if operation == "fetch_tables":
            self.current_worker.tables_loaded.connect(self._on_tables_loaded)
        
        self.current_worker.start()
    
    def _on_progress(self, message: str):
        """Handle progress updates"""
        self.statusBar().showMessage(message)
    
    def _on_operation_finished(self, message: str):
        """Handle operation completion"""
        self.statusBar().showMessage(message)
        self._cleanup_operation()
    
    def _on_operation_error(self, message: str):
        """Handle operation error"""
        self.statusBar().showMessage(f"Error: {message}")
        
        # If database connection failed, show expected tables from schema
        try:
            from src.database.schema_manager import SCHEMA_DEFINITIONS
            self.tables_list.clear()
            self.tables_list.addItem("⚠️ Database connection failed - Showing expected tables:")
            for table_name in SCHEMA_DEFINITIONS.keys():
                self.tables_list.addItem(f"📊 {table_name} (not connected)")
        except Exception:
            self.tables_list.clear()
            self.tables_list.addItem(f"⚠️ {message}")
        
        self._cleanup_operation()
    
    def _on_tables_loaded(self, tables: list):
        """Handle tables list loaded"""
        self.tables_list.clear()
        if tables:
            for table in tables:
                self.tables_list.addItem(f"📁 {table}")
        else:
            self.tables_list.addItem("No tables found")
    
    def _cleanup_operation(self):
        """Clean up after operation completion"""
        if self.current_worker:
            # Disconnect all signals before deleting
            try:
                self.current_worker.progress.disconnect()
                self.current_worker.finished.disconnect()
                self.current_worker.error.disconnect()
                if hasattr(self.current_worker, 'tables_loaded'):
                    self.current_worker.tables_loaded.disconnect()
            except:
                pass
            self.current_worker.deleteLater()
            self.current_worker = None
    
    def _show_error(self, title: str, message: str):
        """Show error dialog"""
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec()
    
    def logout(self):
        """Handle logout - clear session and emit signal to return to login"""
        reply = QMessageBox.question(
            self,
            "Confirm Logout",
            "Are you sure you want to logout?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Clear session
            session = SessionManager()
            session.logout()
            
            logger.info("User confirmed logout")
            
            # Emit signal to notify application (let run_app.py handle window closing)
            self.logout_requested.emit()
    
    def closeEvent(self, event):
        """Handle application close with cleanup"""
        if self.current_worker and self.current_worker.isRunning():
            # Disconnect signals to prevent issues during shutdown
            try:
                self.current_worker.progress.disconnect()
                self.current_worker.finished.disconnect()
                self.current_worker.error.disconnect()
                if hasattr(self.current_worker, 'tables_loaded'):
                    self.current_worker.tables_loaded.disconnect()
            except:
                pass
            
            # Cancel and stop the thread
            self.current_worker.cancel()
            self.current_worker.quit()
            if not self.current_worker.wait(2000):
                # Force terminate if it doesn't stop gracefully
                self.current_worker.terminate()
                self.current_worker.wait(500)
        
        self._save_settings()
        event.accept()
