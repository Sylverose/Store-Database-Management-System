"""
Example usage and testing for the ETL exception system.
Demonstrates how to use the various exception classes and utilities.
"""

from .base_exceptions import ErrorContext
from .database_exceptions import DatabaseError
from .exception_factories import create_database_error, create_api_error
from .decorators import handle_etl_exceptions


def run_examples():
    """Run example usage and testing."""
    print("Testing ETL exception system...")
    
    # Test basic exception
    try:
        context = ErrorContext(
            operation="test_operation",
            component="test_component",
            table_name="test_table"
        )
        
        raise DatabaseError(
            "Connection failed to MySQL server",
            error_code="DB_CONNECTION_FAILED",
            context=context
        )
    
    except DatabaseError as e:
        print(f"Caught ETL exception: {e}")
        print(f"Error code: {e.error_code}")
        print(f"Severity: {e.severity.value}")
        print(f"Category: {e.category.value}")
        print(f"Recovery suggestions: {e.recovery_suggestions}")
        print(f"Exception dict: {e.to_dict()}")
    
    # Test exception factory
    try:
        original_error = Exception("MySQL server has gone away")
        raise create_database_error(
            "Database connection lost during operation",
            original_exception=original_error
        )
    
    except DatabaseError as e:
        print(f"\nFactory-created exception: {e}")
        print(f"Original exception: {e.original_exception}")
    
    # Test decorator
    @handle_etl_exceptions("csv_processing", "file_reader")
    def process_csv_file(filename):
        # Simulate file error
        raise FileNotFoundError(f"Could not find file: {filename}")
    
    try:
        process_csv_file("nonexistent.csv")
    except Exception as e:
        print(f"\nDecorator-handled exception: {e}")
        print(f"Context: {e.context.to_dict()}")
    
    # Test API error factory
    try:
        raise create_api_error(
            "API request failed",
            status_code=404,
            endpoint="/api/customers"
        )
    except Exception as e:
        print(f"\nAPI error example: {e}")
        print(f"Status code context: {e.context.additional_data}")
    
    print("\nETL exception system test complete!")


if __name__ == '__main__':
    run_examples()