"""
Permission management for role-based access control.
Defines role permissions and provides permission checking functions.
"""

import logging
from typing import Optional, Set
from enum import Enum

logger = logging.getLogger(__name__)


class Role(Enum):
    """User role enumeration."""
    EMPLOYEE = "Employee"
    MANAGER = "Manager"
    ADMINISTRATOR = "Administrator"


class Permission(Enum):
    """Permission enumeration."""
    # Dashboard permissions
    VIEW_DASHBOARD = "view_dashboard"
    
    # Database management permissions
    MANAGE_DATABASE = "manage_database"
    
    # Data permissions
    VIEW_DATA = "view_data"
    EXPORT_DATA = "export_data"
    IMPORT_DATA = "import_data"
    MODIFY_DATA = "modify_data"
    DELETE_DATA = "delete_data"
    
    # User management permissions
    VIEW_USERS = "view_users"
    CREATE_USERS = "create_users"
    MODIFY_USERS = "modify_users"
    DELETE_USERS = "delete_users"
    
    # System permissions
    VIEW_LOGS = "view_logs"
    SYSTEM_SETTINGS = "system_settings"


# Role-permission mappings
ROLE_PERMISSIONS = {
    Role.EMPLOYEE: {
        Permission.VIEW_DASHBOARD,
        Permission.VIEW_DATA,
        Permission.EXPORT_DATA,
    },
    Role.MANAGER: {
        Permission.VIEW_DASHBOARD,
        Permission.VIEW_DATA,
        Permission.EXPORT_DATA,
        Permission.IMPORT_DATA,
        Permission.MODIFY_DATA,
        Permission.VIEW_USERS,
        Permission.VIEW_LOGS,
    },
    Role.ADMINISTRATOR: {
        Permission.VIEW_DASHBOARD,
        Permission.MANAGE_DATABASE,
        Permission.VIEW_DATA,
        Permission.EXPORT_DATA,
        Permission.IMPORT_DATA,
        Permission.MODIFY_DATA,
        Permission.DELETE_DATA,
        Permission.VIEW_USERS,
        Permission.CREATE_USERS,
        Permission.MODIFY_USERS,
        Permission.DELETE_USERS,
        Permission.VIEW_LOGS,
        Permission.SYSTEM_SETTINGS,
    }
}


class PermissionManager:
    """Manages role-based permissions."""
    
    @staticmethod
    def get_role_permissions(role: str) -> Set[Permission]:
        """
        Get all permissions for a role.
        
        Args:
            role: Role name as string
            
        Returns:
            Set of Permission enum values
        """
        try:
            role_enum = Role(role)
            return ROLE_PERMISSIONS.get(role_enum, set())
        except ValueError:
            logger.error(f"Invalid role: {role}")
            return set()
    
    @staticmethod
    def has_permission(role: str, permission: Permission) -> bool:
        """
        Check if a role has a specific permission.
        
        Args:
            role: Role name as string
            permission: Permission to check
            
        Returns:
            bool: True if role has permission
        """
        permissions = PermissionManager.get_role_permissions(role)
        return permission in permissions
    
    @staticmethod
    def can_manage_database(role: str) -> bool:
        """Check if role can access database management."""
        return PermissionManager.has_permission(role, Permission.MANAGE_DATABASE)
    
    @staticmethod
    def can_view_dashboard(role: str) -> bool:
        """Check if role can view dashboard."""
        return PermissionManager.has_permission(role, Permission.VIEW_DASHBOARD)
    
    @staticmethod
    def can_modify_data(role: str) -> bool:
        """Check if role can modify data."""
        return PermissionManager.has_permission(role, Permission.MODIFY_DATA)
    
    @staticmethod
    def can_delete_data(role: str) -> bool:
        """Check if role can delete data."""
        return PermissionManager.has_permission(role, Permission.DELETE_DATA)
    
    @staticmethod
    def can_manage_users(role: str) -> bool:
        """Check if role can manage users."""
        return PermissionManager.has_permission(role, Permission.CREATE_USERS)
    
    @staticmethod
    def can_import_data(role: str) -> bool:
        """Check if role can import data."""
        return PermissionManager.has_permission(role, Permission.IMPORT_DATA)
    
    @staticmethod
    def can_export_data(role: str) -> bool:
        """Check if role can export data."""
        return PermissionManager.has_permission(role, Permission.EXPORT_DATA)
