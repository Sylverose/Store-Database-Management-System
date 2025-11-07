"""
Convenience module that exports all ETL exception classes.
Allows importing exceptions from a single module.
"""

from exceptions.base_exceptions import (
    ETLException,
    ErrorSeverity,
    ErrorCategory,
    ErrorContext
)

from exceptions.database_exceptions import (
    DatabaseError,
    ConnectionError,
    QueryError
)

from exceptions.validation_exceptions import (
    ValidationError,
    SchemaValidationError,
    DataQualityError
)

from exceptions.processing_exceptions import (
    ProcessingError
)

from exceptions.system_exceptions import (
    ConfigurationError,
    FileSystemError,
    MemoryError
)

from exceptions.api_exceptions import (
    APIError
)

from exceptions.decorators import (
    handle_etl_exceptions
)

from exceptions.exception_factories import (
    create_database_error,
    create_validation_error,
    create_api_error
)

__all__ = [
    # Base exceptions
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
    
    # Processing exceptions
    'ProcessingError',
    
    # System exceptions
    'ConfigurationError',
    'FileSystemError',
    'MemoryError',
    
    # API exceptions
    'APIError',
    
    # Decorators
    'handle_etl_exceptions',
    
    # Factory functions
    'create_database_error',
    'create_validation_error',
    'create_api_error',
]
