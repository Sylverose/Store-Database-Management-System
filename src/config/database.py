"""
Database-specific configuration utilities and presets.
"""

from dataclasses import dataclass
from typing import Dict, Any
from .import DatabaseConfig


@dataclass
class MySQLConfig(DatabaseConfig):
    """MySQL-specific configuration with optimized defaults."""
    
    # MySQL-specific settings
    charset: str = 'utf8mb4'
    collation: str = 'utf8mb4_unicode_ci'
    sql_mode: str = 'STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO'
    
    # InnoDB settings
    innodb_buffer_pool_size: str = '128M'
    innodb_log_file_size: str = '64M'
    
    # Performance settings
    max_connections: int = 151
    query_cache_size: str = '16M'
    tmp_table_size: str = '16M'
    max_heap_table_size: str = '16M'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with MySQL-specific settings."""
        base_dict = super().to_dict()
        base_dict.update({
            'charset': self.charset,
            'collation': self.collation,
            'init_command': f"SET sql_mode='{self.sql_mode}'"
        })
        return base_dict


def get_mysql_development_config() -> MySQLConfig:
    """Get MySQL configuration optimized for development."""
    return MySQLConfig(
        host='localhost',
        port=3306,
        database='store_manager_dev',
        pool_size=3,
        connect_timeout=10,
        query_cache_size='8M'
    )


def get_mysql_production_config() -> MySQLConfig:
    """Get MySQL configuration optimized for production."""
    return MySQLConfig(
        pool_size=20,
        connect_timeout=30,
        max_connections=500,
        query_cache_size='64M',
        innodb_buffer_pool_size='512M',
        innodb_log_file_size='256M'
    )


def get_mysql_testing_config() -> MySQLConfig:
    """Get MySQL configuration for testing environments."""
    return MySQLConfig(
        database='store_manager_test',
        pool_size=2,
        connect_timeout=5,
        autocommit=True,  # For faster test cleanup
        raise_on_warnings=False  # Less strict for testing
    )