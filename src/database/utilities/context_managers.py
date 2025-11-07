"""
Context managers for safe database operations and transactions.
Core managers for database safety and transaction handling.
"""

import logging
from contextlib import contextmanager
from typing import Optional, Any

logger = logging.getLogger(__name__)


@contextmanager
def safe_operation(operation_name: str, logger_instance: Optional[Any] = None):
    """Context manager for safe database operations with logging.
    
    Args:
        operation_name: Name of the operation for logging
        logger_instance: Optional logger instance to use
        
    Yields:
        None - just provides exception handling and logging
        
    Example:
        with safe_operation("insert batch", logger):
            # Your database operation code here
            cursor.execute(sql, data)
    """
    log = logger_instance or logger
    try:
        log.info(f"Starting {operation_name}")
        yield
        log.info(f"Completed {operation_name}")
    except Exception as e:
        log.error(f"Failed {operation_name}: {e}")
        raise


@contextmanager
def db_transaction(connection, logger_instance: Optional[Any] = None):
    """Context manager for database transactions with rollback on error.
    
    Args:
        connection: Database connection object
        logger_instance: Optional logger instance to use
        
    Yields:
        connection: The database connection for use in the transaction
        
    Example:
        with db_transaction(conn, logger) as transaction_conn:
            cursor = transaction_conn.cursor()
            cursor.execute("INSERT INTO ...")
            cursor.execute("UPDATE ...")
            # Automatically commits on success, rolls back on exception
    """
    log = logger_instance or logger
    try:
        log.debug("Starting database transaction")
        yield connection
        connection.commit()
        log.debug("Transaction committed successfully")
    except Exception as e:
        try:
            connection.rollback()
            log.warning(f"Transaction rolled back due to error: {e}")
        except Exception as rollback_error:
            log.error(f"Failed to rollback transaction: {rollback_error}")
        raise


@contextmanager
def managed_cursor(connection, logger_instance: Optional[Any] = None):
    """Context manager for database cursors with automatic cleanup.
    
    Args:
        connection: Database connection object
        logger_instance: Optional logger instance to use
        
    Yields:
        cursor: Database cursor for operations
        
    Example:
        with managed_cursor(conn, logger) as cursor:
            cursor.execute("SELECT * FROM table")
            results = cursor.fetchall()
    """
    log = logger_instance or logger
    cursor = None
    try:
        cursor = connection.cursor()
        yield cursor
    except Exception as e:
        log.error(f"Cursor operation failed: {e}")
        raise
    finally:
        if cursor:
            try:
                cursor.close()
            except Exception as e:
                log.warning(f"Error closing cursor: {e}")