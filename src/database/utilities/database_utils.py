"""
Core database operation utilities.
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class DatabaseUtils:
    """Database operation utilities for SQL generation and execution."""
    
    @staticmethod
    def batch_execute(cursor, sql: str, data: List, batch_size: int = 1000) -> int:
        """Execute SQL in batches for better performance.
        
        Args:
            cursor: Database cursor
            sql: SQL statement to execute
            data: List of data tuples to execute
            batch_size: Number of records per batch
            
        Returns:
            Total number of affected rows
        """
        total_affected = 0
        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]
            cursor.executemany(sql, batch)
            total_affected += cursor.rowcount
        return total_affected
    
    @staticmethod
    def generate_insert_sql(table_name: str, sample_record: Dict, ignore_duplicates: bool = True) -> str:
        """Generate INSERT SQL statement from sample record.
        
        Args:
            table_name: Target table name
            sample_record: Sample record to determine columns
            ignore_duplicates: Use INSERT IGNORE to skip duplicates
            
        Returns:
            Generated INSERT SQL statement
        """
        columns = list(sample_record.keys())
        placeholders = ', '.join(['%s'] * len(columns))
        insert_type = "INSERT IGNORE" if ignore_duplicates else "INSERT"
        return f"{insert_type} INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
    
    @staticmethod
    def generate_update_sql(table_name: str, update_columns: List[str], key_columns: List[str]) -> str:
        """Generate UPDATE SQL statement.
        
        Args:
            table_name: Target table name
            update_columns: Columns to update
            key_columns: Columns for WHERE clause
            
        Returns:
            Generated UPDATE SQL statement
        """
        set_clause = ', '.join([f"{col} = %s" for col in update_columns])
        where_clause = ' AND '.join([f"{col} = %s" for col in key_columns])
        return f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"
    
    @staticmethod
    def generate_upsert_sql(table_name: str, columns: List[str], update_columns: List[str]) -> str:
        """Generate INSERT ... ON DUPLICATE KEY UPDATE SQL statement.
        
        Args:
            table_name: Target table name
            columns: All columns for INSERT
            update_columns: Columns to update on duplicate
            
        Returns:
            Generated UPSERT SQL statement
        """
        placeholders = ', '.join(['%s'] * len(columns))
        update_clause = ', '.join([f"{col} = VALUES({col})" for col in update_columns])
        return (f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders}) "
                f"ON DUPLICATE KEY UPDATE {update_clause}")
    
    @staticmethod
    def generate_delete_sql(table_name: str, condition_columns: List[str]) -> str:
        """Generate DELETE SQL statement.
        
        Args:
            table_name: Target table name
            condition_columns: Columns for WHERE clause
            
        Returns:
            Generated DELETE SQL statement
        """
        where_clause = ' AND '.join([f"{col} = %s" for col in condition_columns])
        return f"DELETE FROM {table_name} WHERE {where_clause}"
    
    @staticmethod
    def records_to_tuples(records: List[Dict], columns: List[str]) -> List[tuple]:
        """Convert record dicts to tuples for SQL execution.
        
        Args:
            records: List of record dictionaries
            columns: Column names in order
            
        Returns:
            List of tuples for SQL execution
        """
        return [tuple(record.get(col) for col in columns) for record in records]
    
    @staticmethod
    def test_table_exists(cursor, table_name: str) -> bool:
        """Check if table exists in database.
        
        Args:
            cursor: Database cursor
            table_name: Name of table to check
            
        Returns:
            True if table exists, False otherwise
        """
        try:
            cursor.execute(f"SHOW TABLES LIKE %s", (table_name,))
            return cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"Error checking table existence: {e}")
            return False
    
    @staticmethod
    def get_table_row_count(cursor, table_name: str) -> int:
        """Get row count for a table.
        
        Args:
            cursor: Database cursor
            table_name: Name of table to count
            
        Returns:
            Number of rows in table, 0 if error
        """
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Error getting row count: {e}")
            return 0
    
    @staticmethod
    def get_table_columns(cursor, table_name: str) -> List[str]:
        """Get column names for a table.
        
        Args:
            cursor: Database cursor
            table_name: Name of table
            
        Returns:
            List of column names
        """
        try:
            cursor.execute(f"DESCRIBE {table_name}")
            return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting table columns: {e}")
            return []
    
    @staticmethod
    def execute_with_retry(cursor, sql: str, params: tuple = None, max_retries: int = 3) -> bool:
        """Execute SQL with retry logic.
        
        Args:
            cursor: Database cursor
            sql: SQL statement to execute
            params: Parameters for SQL statement
            max_retries: Maximum number of retry attempts
            
        Returns:
            True if successful, False otherwise
        """
        import time
        
        for attempt in range(max_retries + 1):
            try:
                if params:
                    cursor.execute(sql, params)
                else:
                    cursor.execute(sql)
                return True
            except Exception as e:
                if attempt == max_retries:
                    logger.error(f"SQL execution failed after {max_retries} retries: {e}")
                    return False
                
                logger.warning(f"SQL execution attempt {attempt + 1} failed, retrying: {e}")
                time.sleep(1.0)  # Wait 1 second before retry
        
        return False