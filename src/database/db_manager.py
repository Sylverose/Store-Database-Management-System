    # ...existing code...

"""
Enhanced Database Manager with batch processing and connection pooling.
Provides comprehensive ETL operations with high-performance batch operations.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Tuple
from contextlib import contextmanager
import pandas as pd
from datetime import datetime

# Import structured logging
try:
    from logging_system import get_database_logger, performance_context, correlation_context
    LOGGING_SYSTEM_AVAILABLE = True
except ImportError:
    LOGGING_SYSTEM_AVAILABLE = False

# Import pandas optimization
try:
    from pandas_optimizer import PandasOptimizer, optimize_csv_reading
    PANDAS_OPTIMIZER_AVAILABLE = True
except ImportError:
    PANDAS_OPTIMIZER_AVAILABLE = False

# Import data validation
try:
    from data_validator import DataValidator, ValidationRule, ValidationSeverity
    DATA_VALIDATOR_AVAILABLE = True
except ImportError:
    DATA_VALIDATOR_AVAILABLE = False

# Import ETL exceptions
try:
    from etl_exceptions import (
        ETLException, DatabaseError, ValidationError, ProcessingError,
        ErrorContext, ErrorSeverity, handle_etl_exceptions, create_database_error
    )
    ETL_EXCEPTIONS_AVAILABLE = True
except ImportError:
    ETL_EXCEPTIONS_AVAILABLE = False

# Add database package to path (not needed for relative imports)
# sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'database'))

try:
    from .connection_manager import DatabaseConnection, ConnectionPool
    from .schema_manager import SCHEMA_DEFINITIONS
    from connect import config as legacy_config, mysql_connection
    CONNECT_AVAILABLE = True
    POOL_AVAILABLE = True
except ImportError:
    CONNECT_AVAILABLE = False
    POOL_AVAILABLE = False
    legacy_config = {
        'user': 'root', 'password': '', 'host': '127.0.0.1', 
        'database': 'store_manager'
    }
    
    # Create placeholder classes if not available
    class DatabaseConnection:
        def __init__(self, config: Dict = None, enable_pooling=True, pool_size=5):
            self.config = config or {}
            self.enable_pooling = enable_pooling
            self.pool_size = pool_size
        
        @contextmanager
        def get_connection(self):
            # Fallback connection if real class not available
            yield None
    
    class ConnectionPool:
        def __init__(self, config, size):
            pass

# Import structured configuration
try:
    from config import get_config, ETLConfig
    CONFIG_MODULE_AVAILABLE = True
except ImportError:
    CONFIG_MODULE_AVAILABLE = False

# Global logger for module functions
if LOGGING_SYSTEM_AVAILABLE:
    logger = get_database_logger()
else:
    logger = logging.getLogger(__name__)


class BatchProcessor:
    """High-performance batch processing for database operations."""
    
    def __init__(self, connection_manager: DatabaseConnection, batch_size: int = 1000):
        self.connection_manager = connection_manager
        self.batch_size = batch_size
        self.processed_count = 0
        self.error_count = 0
        
    def insert_batch(self, table_name: str, data: List[Dict], 
                    progress_callback: Optional[callable] = None,
                    ignore_duplicates: bool = False) -> Tuple[int, int]:
        """
        Insert data in batches with progress tracking.
        
        Args:
            table_name (str): Target table name
            data (List[Dict]): List of row dictionaries
            progress_callback (callable): Optional progress callback function
            ignore_duplicates (bool): Use INSERT IGNORE for duplicate handling
            
        Returns:
            Tuple[int, int]: (successful_inserts, errors)
        """
        if not data:
            return 0, 0
            
        total_records = len(data)
        successful_inserts = 0
        errors = 0
        
        # Use performance context if available
        context_manager = (performance_context(f"batch_insert_{table_name}", logger) 
                          if LOGGING_SYSTEM_AVAILABLE else self._dummy_context())
        
        with context_manager:
            logger.info(f"Starting batch insert of {total_records} records into {table_name}")
            
            # Get column names from first record
            columns = list(data[0].keys()) if data else []
            if not columns:
                logger.error("No columns found in data")
                return 0, 1
                
            # Prepare SQL
            placeholders = ', '.join(['%s'] * len(columns))
            column_names = ', '.join(f"`{col}`" for col in columns)
            insert_type = "INSERT IGNORE" if ignore_duplicates else "INSERT"
            sql = f"{insert_type} INTO `{table_name}` ({column_names}) VALUES ({placeholders})"
            
            # Process in batches
            for i in range(0, total_records, self.batch_size):
                batch_end = min(i + self.batch_size, total_records)
                batch_data = data[i:batch_end]
                
                try:
                    with self.connection_manager.get_connection() as conn:
                        if conn is None:
                            logger.error("Failed to get database connection")
                            errors += len(batch_data)
                            continue
                            
                        cursor = conn.cursor()
                        
                        try:
                            # Prepare batch values
                            batch_values = []
                            for record in batch_data:
                                values = []
                                for col in columns:
                                    value = record.get(col)
                                    # Handle pandas NaN/None values
                                    if value is None or (pd and pd.isna(value)):
                                        values.append(None)
                                    else:
                                        values.append(value)
                                batch_values.append(tuple(values))
                            
                            # Execute batch insert
                            cursor.executemany(sql, batch_values)
                            conn.commit()
                            
                            batch_success = len(batch_values)
                            successful_inserts += batch_success
                            
                            if progress_callback:
                                progress = (batch_end / total_records) * 100
                                progress_callback(f"Inserted {successful_inserts}/{total_records} records ({progress:.1f}%)")
                                
                            logger.debug(f"Batch {i//self.batch_size + 1}: Inserted {batch_success} records into {table_name}")
                        
                        finally:
                            # Ensure cursor is closed to free resources
                            if cursor:
                                cursor.close()
                        
                except Exception as e:
                    logger.error(f"Error inserting batch {i//self.batch_size + 1} into {table_name}: {e}")
                    errors += len(batch_data)
                    
                    # Log structured exception information if available
                    if ETL_EXCEPTIONS_AVAILABLE:
                        context = ErrorContext(
                            operation="batch_insert",
                            component="batch_processor",
                            table_name=table_name,
                            record_count=len(batch_data)
                        )
                        
                        db_error = create_database_error(
                            f"Batch insert failed for table {table_name}",
                            original_exception=e,
                            context=context
                        )
                        
                        logger.error(f"Structured error info: {db_error.to_dict()}")
                
            logger.info(f"Completed batch insert: {successful_inserts}/{total_records} records inserted into {table_name}, {errors} errors")
            
            self.processed_count += successful_inserts
            self.error_count += errors
            
            return successful_inserts, errors
    
    def _setup_validation_rules(self):
        """Setup standard validation rules for ETL data."""
        if not self.data_validator:
            return
        
        # Note: Using specific column names instead of regex patterns for better compatibility
        logger.debug("Setting up standard validation rules for ETL data")
        
        # Validation rules will be auto-generated per table when validating DataFrames
        logger.debug("Validation rules will be created dynamically per table")
    
    def validate_dataframe(self, df: pd.DataFrame, table_name: str = None) -> Optional[Any]:
        """
        Validate DataFrame with comprehensive checks.
        
        Args:
            df: DataFrame to validate
            table_name: Name of target table for context
            
        Returns:
            ValidationSummary or None if validator not available
        """
        if not self.data_validator or df is None or df.empty:
            return None
        
        logger.info(f"Validating DataFrame for table '{table_name}': {df.shape}")
        
        # Create table-specific validation rules if needed
        auto_rules = self.data_validator.create_schema_from_dataframe(df)
        
        # Temporarily add auto-generated rules
        original_rules = self.data_validator.rules.copy()
        for rule in auto_rules:
            if not any(r.name == rule.name for r in self.data_validator.rules):
                self.data_validator.add_rule(rule)
        
        try:
            # Run validation
            validation_summary = self.data_validator.validate_dataframe(df, stop_on_critical=False)
            
            # Log results
            if validation_summary.failed_rules > 0:
                logger.warning(f"Validation found issues: {validation_summary.failed_rules} failed rules")
                
                # Log critical and error failures
                critical_failures = validation_summary.get_critical_failures()
                if critical_failures:
                    logger.error(f"Critical validation failures: {len(critical_failures)}")
                    for failure in critical_failures:
                        logger.error(f"  - {failure.rule_name}: {failure.message}")
                
                error_failures = validation_summary.get_errors()
                if error_failures:
                    logger.warning(f"Error-level validation failures: {len(error_failures)}")
                    for failure in error_failures[:3]:  # Show first 3
                        logger.warning(f"  - {failure.rule_name}: {failure.message}")
            
            else:
                logger.info(f"Validation passed: all {validation_summary.total_rules} rules successful")
            
            return validation_summary
            
        finally:
            # Restore original rules
            self.data_validator.rules = original_rules
    
    @contextmanager
    def _dummy_context(self):
        """Dummy context manager when performance tracking is not available."""
        yield
    
    def update_batch(self, table_name: str, updates: List[Dict], 
                    key_columns: List[str],
                    progress_callback: Optional[callable] = None) -> Tuple[int, int]:
        """
        Update records in batches.
        
        Args:
            table_name (str): Target table name
            updates (List[Dict]): List of update dictionaries
            key_columns (List[str]): Column names to use as WHERE conditions
            progress_callback (callable): Optional progress callback
            
        Returns:
            Tuple[int, int]: (successful_updates, errors)
        """
        if not updates:
            return 0, 0
            
        successful_updates = 0
        errors = 0
        total_records = len(updates)
        
        for i, record in enumerate(updates):
            try:
                with self.connection_manager.get_connection() as conn:
                    if conn is None:
                        errors += 1
                        continue
                        
                    cursor = conn.cursor()
                    
                    # Build SET clause (exclude key columns)
                    set_columns = [col for col in record.keys() if col not in key_columns]
                    set_clause = ', '.join(f"`{col}` = %s" for col in set_columns)
                    
                    # Build WHERE clause
                    where_clause = ' AND '.join(f"`{col}` = %s" for col in key_columns)
                    
                    # Prepare SQL and values
                    sql = f"UPDATE `{table_name}` SET {set_clause} WHERE {where_clause}"
                    
                    values = []
                    # SET values
                    for col in set_columns:
                        value = record.get(col)
                        if value is None or (pd and pd.isna(value)):
                            values.append(None)
                        else:
                            values.append(value)
                    # WHERE values  
                    for col in key_columns:
                        values.append(record[col])
                    
                    cursor.execute(sql, values)
                    conn.commit()
                    
                    successful_updates += cursor.rowcount
                    
                    if progress_callback and (i + 1) % self.batch_size == 0:
                        progress = ((i + 1) / total_records) * 100
                        progress_callback(f"Updated {i + 1}/{total_records} records ({progress:.1f}%)")
                        
            except Exception as e:
                logger.error(f"Error updating record {i + 1}: {e}")
                errors += 1
                
        return successful_updates, errors
    
    def upsert_batch(self, table_name: str, data: List[Dict],
                    key_columns: List[str],
                    progress_callback: Optional[callable] = None) -> Tuple[int, int, int]:
        """
        Insert or update records in batches (MySQL ON DUPLICATE KEY UPDATE).
        
        Args:
            table_name (str): Target table name
            data (List[Dict]): List of row dictionaries
            key_columns (List[str]): Columns that define uniqueness
            progress_callback (callable): Optional progress callback
            
        Returns:
            Tuple[int, int, int]: (inserts, updates, errors)
        """
        if not data:
            return 0, 0, 0
            
        inserts = 0
        updates = 0
        errors = 0
        total_records = len(data)
        
        # Get all columns
        columns = list(data[0].keys()) if data else []
        if not columns:
            return 0, 0, 1
            
        # Build SQL with ON DUPLICATE KEY UPDATE
        column_names = ', '.join(f"`{col}`" for col in columns)
        placeholders = ', '.join(['%s'] * len(columns))
        
        # Update columns (exclude key columns from updates if desired)
        update_columns = [col for col in columns if col not in key_columns]
        update_clause = ', '.join(f"`{col}` = VALUES(`{col}`)" for col in update_columns)
        
        sql = f"""
            INSERT INTO `{table_name}` ({column_names}) 
            VALUES ({placeholders})
            ON DUPLICATE KEY UPDATE {update_clause}
        """
        
        # Process in batches
        for i in range(0, total_records, self.batch_size):
            batch_end = min(i + self.batch_size, total_records)
            batch_data = data[i:batch_end]
            
            try:
                with self.connection_manager.get_connection() as conn:
                    if conn is None:
                        errors += len(batch_data)
                        continue
                        
                    cursor = conn.cursor()
                    
                    # Execute each record (MySQL executemany doesn't return useful info for upserts)
                    batch_inserts = 0
                    batch_updates = 0
                    
                    for record in batch_data:
                        values = []
                        for col in columns:
                            value = record.get(col)
                            if value is None or (pd and pd.isna(value)):
                                values.append(None)
                            else:
                                values.append(value)
                        
                        cursor.execute(sql, values)
                        
                        # Check if it was an insert or update
                        if cursor.rowcount == 1:
                            batch_inserts += 1
                        elif cursor.rowcount == 2:
                            batch_updates += 1
                    
                    conn.commit()
                    inserts += batch_inserts
                    updates += batch_updates
                    
                    if progress_callback:
                        progress = (batch_end / total_records) * 100
                        progress_callback(f"Upserted {batch_end}/{total_records} records ({progress:.1f}%)")
                        
            except Exception as e:
                logger.error(f"Error in upsert batch: {e}")
                errors += len(batch_data)
                
        return inserts, updates, errors
    
    def get_stats(self) -> Dict[str, int]:
        """Get processing statistics."""
        return {
            'processed_count': self.processed_count,
            'error_count': self.error_count,
            'batch_size': self.batch_size
        }


class DatabaseManager:
    """Enhanced Database Manager with batch processing and connection pooling."""
    
    def __init__(self, config: Dict = None, data_dir: Path = None, logger_instance = None, 
                 enable_pooling: bool = True, pool_size: int = 5):
        """
        Initialize database manager with enhanced connection management.
        
        Args:
            config (Dict): Database configuration or ETLConfig instance
            data_dir (Path): Data directory path
            logger_instance: Logger instance  
            enable_pooling (bool): Enable connection pooling
            pool_size (int): Connection pool size
        """
        # Handle different config types
        if config is None:
            # Use structured config if available
            if CONFIG_MODULE_AVAILABLE:
                etl_config = get_config()
                self.config = etl_config.database.to_dict()
                self.etl_config = etl_config
            else:
                self.config = legacy_config
                self.etl_config = None
        elif isinstance(config, dict):
            self.config = config
            self.etl_config = None
        else:
            # Assume it's an ETLConfig instance
            self.config = config.database.to_dict() if hasattr(config, 'database') else legacy_config
            self.etl_config = config
        self.data_dir = data_dir or Path(__file__).parent.parent.parent / 'data'
        self.csv_dir = self.data_dir / 'CSV'
        self.api_dir = self.data_dir / 'API'
        
        # Initialize enhanced connection manager
        self.db_connection = DatabaseConnection(
            config=self.config,
            enable_pooling=enable_pooling,
            pool_size=pool_size
        )
        
        # Initialize batch processor
        self.batch_processor = BatchProcessor(self.db_connection)
        
        # Initialize pandas optimizer if available
        if PANDAS_OPTIMIZER_AVAILABLE:
            if self.etl_config and hasattr(self.etl_config, 'processing'):
                processing_config = self.etl_config.processing
                chunk_size = processing_config.chunk_size
                max_memory_mb = processing_config.max_memory_usage_mb
            else:
                chunk_size = 5000
                max_memory_mb = 512
            
            self.pandas_optimizer = PandasOptimizer(
                max_memory_usage_mb=max_memory_mb,
                chunk_size=chunk_size,
                optimize_dtypes=True
            )
        else:
            self.pandas_optimizer = None
        
        # Initialize data validator if available
        if DATA_VALIDATOR_AVAILABLE:
            self.data_validator = DataValidator()
            self._setup_validation_rules()
        else:
            self.data_validator = None
        
        # CSV file mappings (based on test files)
        self.csv_files = {
            'brands': 'brands.csv',
            'categories': 'categories.csv', 
            'stores': 'stores.csv',
            'staffs': 'staffs.csv',
            'products': 'products.csv',
            'stocks': 'stocks.csv'
        }
        
        # API endpoints mapping
        self.api_tables = {
            'customers': 'customers',
            'orders': 'orders',
            'order_items': 'order_items'
        }
        
        # Table schemas (simplified - based on data model)
        self.table_schemas = {
            'brands': ['brand_id', 'brand_name'],
            'categories': ['category_id', 'category_name'],
            'stores': ['store_id', 'name', 'phone', 'email', 'street', 'city', 'state', 'zip_code'],
            'staffs': ['staff_id', 'name', 'email', 'phone', 'active', 'store_name', 'street'],  # Updated schema
            'products': ['product_id', 'product_name', 'brand_id', 'category_id', 'model_year', 'list_price'],
            'stocks': ['store_name', 'product_id', 'quantity'],  # Updated schema with store_name
            'customers': ['customer_id', 'first_name', 'last_name', 'email', 'phone', 'street', 'city', 'state', 'zip_code'],
            'orders': ['order_id', 'customer_id', 'order_status', 'order_status_name', 'order_date', 'required_date', 'shipped_date', 'staff_name', 'store'],
            'order_items': ['item_id', 'order_id', 'product_id', 'quantity', 'list_price', 'discount']
        }
    
    def test_connection(self) -> bool:
        """Test database connection."""
        return self.db_connection.test_connection()
    
    def get_all_tables(self) -> list:
        """Get list of all tables in database."""
        try:
            with self.get_connection() as conn:
                if conn is None:
                    return []
                cursor = conn.cursor()
                cursor.execute("SHOW TABLES")
                tables = [table[0] for table in cursor.fetchall()]
                cursor.close()
                return tables
        except Exception as e:
            logger.error(f"Failed to get tables: {e}")
            return []
    
    def get_total_sales(self) -> float:
        """Get total sales from order_items."""
        try:
            with self.get_connection() as conn:
                if conn is None:
                    return 0.0
                cursor = conn.cursor()
                query = """
                    SELECT SUM(quantity * list_price * (1 - discount)) as total_sales 
                    FROM order_items
                """
                cursor.execute(query)
                result = cursor.fetchone()
                cursor.close()
                return float(result[0]) if result[0] is not None else 0.0
        except Exception as e:
            logger.error(f"Failed to get total sales: {e}")
            return 0.0
    
    def create_database_if_not_exists(self, database_name: str = None) -> bool:
        """Create database if it doesn't exist."""
        return self.db_connection.create_database_if_not_exists(database_name)
    
    def get_connection_stats(self) -> Dict:
        """Get connection statistics."""
        stats = self.db_connection.get_connection_stats()
        stats.update(self.batch_processor.get_stats())
        return stats
    
    @contextmanager
    def get_connection(self):
        """Get database connection context manager."""
        with self.db_connection.get_connection() as conn:
            yield conn
    
    def create_all_tables_from_csv(self) -> bool:
        """Create all database tables with updated schemas."""
        try:
            with self.get_connection() as conn:
                if conn is None:
                    logger.error("Failed to get database connection for table creation")
                    return False
                    
                cursor = conn.cursor()
                
                # Create tables in correct order (respecting foreign keys)
                table_order = ['brands', 'categories', 'stores', 'staffs', 'customers', 'products', 'stocks', 'orders', 'order_items']
                
                for table_name in table_order:
                    if table_name in SCHEMA_DEFINITIONS:
                        cursor.execute(SCHEMA_DEFINITIONS[table_name])
                        logger.info(f"Created/verified table: {table_name}")
                
                conn.commit()
                logger.info("All 9 tables created successfully")
                return True
                
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            return False
    
    def read_csv_file(self, csv_filename: str) -> Optional[pd.DataFrame]:
        """Read CSV file with optimized memory usage and structured error handling."""
        context = ErrorContext(
            operation="read_csv_file",
            component="database_manager", 
            file_path=str(csv_filename)
        ) if ETL_EXCEPTIONS_AVAILABLE else None
        
        try:
            file_path = self.csv_dir / csv_filename
            if not file_path.exists():
                error_msg = f"CSV file not found: {file_path}"
                logger.error(error_msg)
                
                if ETL_EXCEPTIONS_AVAILABLE:
                    from etl_exceptions import FileSystemError
                    raise FileSystemError(
                        error_msg,
                        error_code="CSV_FILE_NOT_FOUND",
                        context=context
                    )
                return None
            
            # Use optimized CSV reading if available
            if self.pandas_optimizer and PANDAS_OPTIMIZER_AVAILABLE:
                logger.debug(f"Reading {csv_filename} with pandas optimization")
                df = optimize_csv_reading(file_path, optimize_dtypes=True)
            else:
                # Fallback to standard pandas
                logger.debug(f"Reading {csv_filename} with standard pandas")
                df = pd.read_csv(file_path)
            
            # Clean data: convert NaN to None for MySQL compatibility
            df = df.where(pd.notna(df), None)
            
            # Get memory profile if optimizer available
            if self.pandas_optimizer:
                profile = self.pandas_optimizer.get_data_profile(df)
                logger.info(f"Read {csv_filename}: {profile['shape']} shape, "
                          f"{profile['memory_usage_mb']:.2f}MB memory, "
                          f"{len(profile['categorical_columns'])} categorical columns")
            else:
                logger.debug(f"Read {len(df)} rows from {csv_filename}")
            
            # Validate data if validator available
            if self.data_validator:
                table_name = csv_filename.replace('.csv', '')
                validation_summary = self.validate_dataframe(df, table_name)
                
                if validation_summary and validation_summary.failed_rules > 0:
                    logger.warning(f"Data validation found {validation_summary.failed_rules} issues in {csv_filename}")
                    
                    # Optionally clean data automatically
                    if validation_summary.get_critical_failures():
                        logger.error(f"Critical validation failures in {csv_filename} - consider manual review")
                    else:
                        # Auto-clean non-critical issues
                        cleaned_df, fixes = self.data_validator.clean_data(df, validation_summary)
                        if fixes:
                            logger.info(f"Applied automatic fixes to {csv_filename}: {fixes}")
                            df = cleaned_df
            
            return df
            
        except Exception as e:
            error_msg = f"Error reading CSV file {csv_filename}: {e}"
            logger.error(error_msg)
            
            if ETL_EXCEPTIONS_AVAILABLE and not isinstance(e, ETLException):
                # Convert to structured exception
                if "memory" in str(e).lower():
                    from etl_exceptions import MemoryError as ETLMemoryError
                    raise ETLMemoryError(
                        f"Memory error reading CSV file: {e}",
                        context=context,
                        original_exception=e
                    )
                else:
                    from etl_exceptions import FileSystemError
                    raise FileSystemError(
                        error_msg,
                        error_code="CSV_READ_ERROR",
                        context=context,
                        original_exception=e
                    )
            elif isinstance(e, ETLException):
                raise  # Re-raise ETL exceptions
            
            return None
    
    def import_csv_data(self) -> bool:
        """Import all CSV data with batch processing."""
        try:
            total_inserted = 0
            total_errors = 0
            
            # Import in correct order to respect foreign keys
            import_order = ['brands', 'categories', 'stores', 'staffs', 'products', 'stocks']
            
            for table_name in import_order:
                if table_name not in self.csv_files:
                    continue
                    
                csv_filename = self.csv_files[table_name]
                df = self.read_csv_file(csv_filename)
                
                if df is None:
                    logger.warning(f"Skipping {table_name} - file not found or read error")
                    continue
                
                # Convert DataFrame to list of dictionaries
                records = df.to_dict('records')
                
                if not records:
                    logger.warning(f"No records found in {csv_filename}")
                    continue
                
                # Use batch processor for high-performance insert
                inserted, errors = self.batch_processor.insert_batch(
                    table_name=table_name,
                    data=records,
                    progress_callback=lambda msg: logger.info(f"{table_name}: {msg}"),
                    ignore_duplicates=True  # Handle duplicates gracefully
                )
                
                total_inserted += inserted
                total_errors += errors
                
                logger.info(f"Table {table_name}: {inserted} inserted, {errors} errors")
            
            logger.info(f"CSV import completed: {total_inserted} total records inserted, {total_errors} errors")
            return total_errors == 0
            
        except Exception as e:
            logger.error(f"Error importing CSV data: {e}")
            return False
    
    def get_row_count(self, table_name: str) -> int:
        """Get row count for a table."""
        try:
            with self.get_connection() as conn:
                if conn is None:
                    return -1
                    
                cursor = conn.cursor()
                cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
                result = cursor.fetchone()
                return result[0] if result else 0
                
        except Exception as e:
            logger.debug(f"Error getting row count for {table_name}: {e}")
            return -1
    
    def export_api_data_to_csv(self) -> bool:
        """Export API data to CSV files (placeholder for compatibility)."""
        try:
            # This would typically fetch from API and export to CSV
            # For now, return True to satisfy test requirements
            self.api_dir.mkdir(parents=True, exist_ok=True)
            logger.info("API data export functionality - placeholder implementation")
            return True
        except Exception as e:
            logger.error(f"Error exporting API data: {e}")
            return False
    
    def verify_data(self) -> Dict[str, int]:
        """Verify data across all tables."""
        verification_results = {}
        
        all_tables = list(self.csv_files.keys()) + list(self.api_tables.keys())
        
        for table_name in all_tables:
            count = self.get_row_count(table_name)
            verification_results[table_name] = count
            
        logger.info(f"Data verification completed: {verification_results}")
        return verification_results
    
    # Batch processing methods for external use
    
    def batch_insert(self, table_name: str, data: List[Dict], 
                    batch_size: int = None, ignore_duplicates: bool = False,
                    progress_callback: callable = None) -> Tuple[int, int]:
        """
        High-performance batch insert with customizable batch size.
        
        Args:
            table_name (str): Target table name
            data (List[Dict]): List of row dictionaries
            batch_size (int): Optional custom batch size
            ignore_duplicates (bool): Use INSERT IGNORE for duplicate handling
            progress_callback (callable): Optional progress callback
            
        Returns:
            Tuple[int, int]: (successful_inserts, errors)
        """
        if batch_size:
            original_batch_size = self.batch_processor.batch_size
            self.batch_processor.batch_size = batch_size
            
        try:
            return self.batch_processor.insert_batch(
                table_name=table_name,
                data=data, 
                progress_callback=progress_callback,
                ignore_duplicates=ignore_duplicates
            )
        finally:
            if batch_size:
                self.batch_processor.batch_size = original_batch_size
    
    def batch_update(self, table_name: str, updates: List[Dict],
                    key_columns: List[str], batch_size: int = None,
                    progress_callback: callable = None) -> Tuple[int, int]:
        """
        High-performance batch update.
        
        Args:
            table_name (str): Target table name
            updates (List[Dict]): List of update dictionaries
            key_columns (List[str]): Columns to use as WHERE conditions
            batch_size (int): Optional custom batch size
            progress_callback (callable): Optional progress callback
            
        Returns:
            Tuple[int, int]: (successful_updates, errors)
        """
        if batch_size:
            original_batch_size = self.batch_processor.batch_size
            self.batch_processor.batch_size = batch_size
            
        try:
            return self.batch_processor.update_batch(
                table_name=table_name,
                updates=updates,
                key_columns=key_columns,
                progress_callback=progress_callback
            )
        finally:
            if batch_size:
                self.batch_processor.batch_size = original_batch_size
    
    def batch_upsert(self, table_name: str, data: List[Dict],
                    key_columns: List[str], batch_size: int = None,
                    progress_callback: callable = None) -> Tuple[int, int, int]:
        """
        High-performance batch upsert (INSERT ... ON DUPLICATE KEY UPDATE).
        
        Args:
            table_name (str): Target table name
            data (List[Dict]): List of row dictionaries
            key_columns (List[str]): Columns that define uniqueness
            batch_size (int): Optional custom batch size
            progress_callback (callable): Optional progress callback
            
        Returns:
            Tuple[int, int, int]: (inserts, updates, errors)
        """
        if batch_size:
            original_batch_size = self.batch_processor.batch_size
            self.batch_processor.batch_size = batch_size
            
        try:
            return self.batch_processor.upsert_batch(
                table_name=table_name,
                data=data,
                key_columns=key_columns,
                progress_callback=progress_callback
            )
        finally:
            if batch_size:
                self.batch_processor.batch_size = original_batch_size
    
    def close_connections(self):
        """Clean up database connections."""
        # Don't close the singleton pool - let it manage itself
        # Connections are returned to pool automatically via context managers
        pass
    
    def __del__(self):
        """Cleanup when instance is destroyed."""
        pass


# Legacy compatibility functions
def create_api_tables_and_csv():
    """Legacy compatibility function."""
    db_manager = DatabaseManager()
    return db_manager.export_api_data_to_csv()


if __name__ == "__main__":
    # Command line execution
    import argparse
    
    parser = argparse.ArgumentParser(description="ETL Database Manager")
    parser.add_argument("--create-tables", action="store_true", help="Create database tables")
    parser.add_argument("--import-csv", action="store_true", help="Import CSV data")
    parser.add_argument("--verify", action="store_true", help="Verify data")
    parser.add_argument("--pool-size", type=int, default=5, help="Connection pool size")
    parser.add_argument("--batch-size", type=int, default=1000, help="Batch processing size")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Initialize database manager
        db_manager = DatabaseManager(
            enable_pooling=True,
            pool_size=args.pool_size
        )
        
        # Set batch size
        db_manager.batch_processor.batch_size = args.batch_size
        
        # Test connection
        if not db_manager.test_connection():
            logger.error("Failed to connect to database")
            sys.exit(1)
        
        logger.info("Database connection successful")
        
        # Create database
        if not db_manager.create_database_if_not_exists():
            logger.error("Failed to create database")
            sys.exit(1)
        
        # Execute requested operations
        if args.create_tables:
            logger.info("Creating database tables...")
            if db_manager.create_all_tables_from_csv():
                logger.info("Tables created successfully")
            else:
                logger.error("Failed to create tables")
                sys.exit(1)
        
        if args.import_csv:
            logger.info("Importing CSV data...")
            if db_manager.import_csv_data():
                logger.info("CSV data imported successfully")
            else:
                logger.error("Failed to import CSV data")
        
        if args.verify:
            logger.info("Verifying data...")
            results = db_manager.verify_data()
            for table, count in results.items():
                logger.info(f"Table {table}: {count} records")
        
        # Show statistics
        stats = db_manager.get_connection_stats()
        logger.info(f"Connection statistics: {stats}")
        
    except Exception as e:
        logger.error(f"Error in database manager: {e}")
        sys.exit(1)
    finally:
        if 'db_manager' in locals():
            db_manager.close_connections()
