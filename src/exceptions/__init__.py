"""
ETL exception handling package.

This package provides a comprehensive exception hierarchy for ETL operations
with context information, recovery suggestions, and structured error handling.
"""

# Core exception classes and enums
from .base_exceptions import (
    ETLException,
    ErrorSeverity,
    ErrorCategory,
    ErrorContext
)

# Specific exception types
from .database_exceptions import (
    DatabaseError,
    ConnectionError,
    QueryError
)

from .validation_exceptions import (
    ValidationError,
    SchemaValidationError,
    DataQualityError
)

from .api_exceptions import APIError

from .processing_exceptions import ProcessingError

from .system_exceptions import (
    ConfigurationError,
    FileSystemError,
    MemoryError
)

# Factory functions and utilities
from .exception_factories import (
    create_database_error,
    create_validation_error,
    create_api_error
)

from .decorators import handle_etl_exceptions

# Export all public classes and functions
__all__ = [
    # Core classes
    'ETLException',
    'ErrorSeverity',
    'ErrorCategory', 
    'ErrorContext',
    
    # Database exceptions
    'DatabaseError',
    'ConnectionError',
    'QueryError',
    
    # Validation exceptions
    'ValidationError',
    'SchemaValidationError',
    'DataQualityError',
    
    # API exceptions
    'APIError',
    
    # Processing exceptions
    'ProcessingError',
    
    # System exceptions
    'ConfigurationError',
    'FileSystemError',
    'MemoryError',
    
    # Factory functions
    'create_database_error',
    'create_validation_error',
    'create_api_error',
    
    # Decorators
    'handle_etl_exceptions'
]