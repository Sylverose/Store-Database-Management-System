"""
Centralized environment configuration using .env file
Provides secure access to environment variables with fallback defaults
"""

import os
from pathlib import Path
from typing import Optional

# Try to load dotenv, but don't fail if not available
try:
    from dotenv import load_dotenv
    # Load .env from project root
    project_root = Path(__file__).parent.parent
    env_path = project_root / '.env'
    load_dotenv(env_path)
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    print("Warning: python-dotenv not installed. Using system environment variables only.")


class EnvConfig:
    """Centralized environment configuration"""
    
    @staticmethod
    def get(key: str, default: Optional[str] = None) -> Optional[str]:
        """Get environment variable with optional default"""
        return os.getenv(key, default)
    
    @staticmethod
    def get_int(key: str, default: int) -> int:
        """Get environment variable as integer"""
        value = os.getenv(key)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            return default
    
    @staticmethod
    def get_bool(key: str, default: bool) -> bool:
        """Get environment variable as boolean"""
        value = os.getenv(key)
        if value is None:
            return default
        return value.lower() in ('true', '1', 'yes', 'on')
    
    # Database Configuration
    @property
    def db_host(self) -> str:
        return self.get('DB_HOST', 'localhost')
    
    @property
    def db_port(self) -> int:
        return self.get_int('DB_PORT', 3306)
    
    @property
    def db_name(self) -> str:
        return self.get('DB_NAME', 'store_manager')
    
    @property
    def db_user(self) -> str:
        return self.get('DB_USER', 'root')
    
    @property
    def db_password(self) -> str:
        return self.get('DB_PASSWORD', '')
    
    # API Configuration
    @property
    def api_url(self) -> str:
        return self.get('API_URL', 'https://etl-server.fly.dev')
    
    @property
    def api_key(self) -> Optional[str]:
        return self.get('API_KEY')
    
    # Security Settings
    @property
    def session_timeout_minutes(self) -> int:
        return self.get_int('SESSION_TIMEOUT_MINUTES', 30)
    
    @property
    def max_login_attempts(self) -> int:
        return self.get_int('MAX_LOGIN_ATTEMPTS', 5)
    
    @property
    def lockout_duration_minutes(self) -> int:
        return self.get_int('LOCKOUT_DURATION_MINUTES', 15)
    
    # Application Settings
    @property
    def environment(self) -> str:
        return self.get('ENVIRONMENT', 'development')
    
    @property
    def debug(self) -> bool:
        return self.get_bool('DEBUG', True)
    
    @property
    def log_level(self) -> str:
        return self.get('LOG_LEVEL', 'INFO')


# Singleton instance
env_config = EnvConfig()
