"""
Decorators for automatic exception handling and conversion.
Provides convenient decorators to wrap functions with ETL exception handling.
"""

from .base_exceptions import ETLException, ErrorContext
from .database_exceptions import DatabaseError
from .api_exceptions import APIError
from .system_exceptions import FileSystemError, MemoryError
from .processing_exceptions import ProcessingError
from .exception_factories import create_database_error


def handle_etl_exceptions(operation_name: str, component: str = "unknown"):
    """
    Decorator to automatically handle and convert exceptions to ETL exceptions.
    
    Args:
        operation_name: Name of the operation being performed
        component: Component name for context
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ETLException:
                # Re-raise ETL exceptions as-is
                raise
            except Exception as e:
                # Convert other exceptions to ETL exceptions
                context = ErrorContext(
                    operation=operation_name,
                    component=component
                )
                
                # Try to determine appropriate exception type
                error_str = str(e).lower()
                
                if any(db_keyword in error_str for db_keyword in ['mysql', 'database', 'connection', 'sql']):
                    raise create_database_error(
                        f"Database error in {operation_name}: {str(e)}",
                        original_exception=e,
                        context=context
                    )
                elif any(api_keyword in error_str for api_keyword in ['http', 'api', 'request', 'response']):
                    raise APIError(
                        f"API error in {operation_name}: {str(e)}",
                        original_exception=e,
                        context=context
                    )
                elif any(file_keyword in error_str for file_keyword in ['file', 'directory', 'path']):
                    raise FileSystemError(
                        f"File system error in {operation_name}: {str(e)}",
                        original_exception=e,
                        context=context
                    )
                elif 'memory' in error_str:
                    raise MemoryError(
                        f"Memory error in {operation_name}: {str(e)}",
                        original_exception=e,
                        context=context
                    )
                else:
                    # Generic processing error
                    raise ProcessingError(
                        f"Processing error in {operation_name}: {str(e)}",
                        original_exception=e,
                        context=context
                    )
        
        return wrapper
    return decorator