"""
Configuration management and validation utilities (simplified).
"""

import os
import logging
from typing import Dict, List, Tuple, Optional, Any

logger = logging.getLogger(__name__)


class ConfigUtils:
    """Configuration management utilities for database connections."""
    
    @staticmethod
    def merge_configs(*configs: Dict) -> Dict:
        """Merge multiple configuration dictionaries."""
        result = {}
        for cfg in configs:
            if cfg:
                result.update(cfg)
        return result
    
    @staticmethod
    def get_env_config(prefix: str = "DB_") -> Dict[str, str]:
        """Get database configuration from environment variables.
        
        Args:
            prefix: Environment variable prefix (default: "DB_")
            
        Returns:
            Configuration dictionary from environment variables
        """
        config = {}
        env_mapping = {
            f"{prefix}USER": "user", 
            f"{prefix}PASSWORD": "password", 
            f"{prefix}HOST": "host", 
            f"{prefix}PORT": "port", 
            f"{prefix}NAME": "database",
            f"{prefix}CHARSET": "charset"
        }
        
        for env_key, config_key in env_mapping.items():
            value = os.getenv(env_key)
            if value:
                if config_key == "port":
                    try:
                        config[config_key] = int(value)
                    except ValueError:
                        logger.warning(f"Invalid port value in {env_key}: {value}")
                        continue
                else:
                    config[config_key] = value
        
        return config
    
    @staticmethod
    def validate_config(config: Dict) -> Tuple[bool, List[str]]:
        """Validate database configuration.
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        required_fields = ['user', 'host', 'database']
        errors = []
        
        # Check required fields
        missing = [field for field in required_fields if not config.get(field)]
        if missing:
            errors.append(f"Missing required config fields: {missing}")
        
        # Validate field types and values
        if 'port' in config:
            port = config['port']
            if not isinstance(port, int) or port < 1 or port > 65535:
                errors.append(f"Invalid port value: {port} (must be integer 1-65535)")
        
        if 'host' in config and not config['host'].strip():
            errors.append("Host cannot be empty")
        
        if 'database' in config and not config['database'].strip():
            errors.append("Database name cannot be empty")
        
        if config.get('password') == '':
            logger.warning("Database password is empty - this may be insecure")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def get_default_config() -> Dict[str, Any]:
        """Get default database configuration."""
        return {
            'user': 'root',
            'password': '',
            'host': '127.0.0.1',
            'port': 3306,
            'database': 'store_manager',
            'charset': 'utf8mb4'
        }
    
    @staticmethod
    def mask_sensitive_config(config: Dict, sensitive_keys: List[str] = None) -> Dict:
        """Mask sensitive configuration values for logging."""
        if sensitive_keys is None:
            sensitive_keys = ['password', 'secret', 'key', 'token']
        
        masked_config = config.copy()
        
        for key, value in masked_config.items():
            if any(sensitive_key in key.lower() for sensitive_key in sensitive_keys):
                if isinstance(value, str) and value:
                    masked_config[key] = '*' * min(len(value), 8)
                else:
                    masked_config[key] = '***'
        
        return masked_config
