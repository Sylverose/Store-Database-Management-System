"""
Factory functions for creating exception instances.
Provides convenient ways to create appropriate exceptions based on context.
"""

from typing import Optional
from .database_exceptions import DatabaseError, ConnectionError, QueryError
from .validation_exceptions import ValidationError, SchemaValidationError, DataQualityError
from .api_exceptions import APIError


def create_database_error(message: str, original_exception: Exception = None, **kwargs) -> DatabaseError:
    """Factory function to create database errors with context from original exception."""
    if original_exception:
        kwargs['original_exception'] = original_exception
        
        # Try to extract additional context from common database exceptions
        error_str = str(original_exception).lower()
        
        if 'connection' in error_str or 'connect' in error_str:
            return ConnectionError(message, **kwargs)
        elif 'syntax' in error_str or 'query' in error_str:
            return QueryError(message, **kwargs)
    
    return DatabaseError(message, **kwargs)


def create_validation_error(message: str, validation_type: str = "general", **kwargs) -> ValidationError:
    """Factory function to create validation errors based on type."""
    if validation_type == "schema":
        return SchemaValidationError(message, **kwargs)
    elif validation_type == "data_quality":
        return DataQualityError(message, **kwargs)
    else:
        return ValidationError(message, **kwargs)


def create_api_error(message: str, status_code: Optional[int] = None, **kwargs) -> APIError:
    """Factory function to create API errors with appropriate error codes."""
    if status_code:
        if status_code == 401:
            kwargs.setdefault('error_code', 'API_UNAUTHORIZED')
        elif status_code == 403:
            kwargs.setdefault('error_code', 'API_FORBIDDEN')
        elif status_code == 404:
            kwargs.setdefault('error_code', 'API_NOT_FOUND')
        elif status_code == 429:
            kwargs.setdefault('error_code', 'API_RATE_LIMITED')
        elif status_code >= 500:
            kwargs.setdefault('error_code', 'API_SERVER_ERROR')
        else:
            kwargs.setdefault('error_code', f'API_HTTP_{status_code}')
    
    return APIError(message, status_code=status_code, **kwargs)