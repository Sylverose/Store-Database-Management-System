"""
Specialized processor for batch insert operations.
"""

import logging
from typing import Dict, List, Optional, Tuple, Callable
from .base_processor import BaseBatchProcessor
from ..utilities import DatabaseUtils, safe_operation

logger = logging.getLogger(__name__)


class InsertProcessor(BaseBatchProcessor):
    """Handle batch insert operations with specialized functionality."""
    
    def insert_batch(self, table_name: str, records: List[Dict], 
                    progress_callback: Optional[Callable] = None, 
                    ignore_duplicates: bool = True,
                    validate_data: bool = True) -> Tuple[int, int]:
        """Insert records in batches.
        
        Args:
            table_name: Target table name
            records: List of record dictionaries
            progress_callback: Optional progress callback function
            ignore_duplicates: Use INSERT IGNORE to skip duplicates
            validate_data: Validate data before insertion
            
        Returns:
            Tuple of (inserted_count, failed_count)
        """
        if not records:
            return 0, 0
        
        # Validate records if requested
        if validate_data:
            records, validation_errors = self.validate_records(records)
            if validation_errors:
                self.logger.warning(f"Data validation errors: {validation_errors}")
        
        with safe_operation(f"batch insert to {table_name}", self.logger):
            with self.connection_manager.get_connection() as conn:
                if not conn:
                    self.stats.add_operation(records_failed=len(records), 
                                           error="No database connection")
                    return 0, len(records)
                
                return self._execute_batch_insert(conn, table_name, records, 
                                                ignore_duplicates, progress_callback)
    
    def _execute_batch_insert(self, conn, table_name: str, records: List[Dict], 
                            ignore_duplicates: bool, progress_callback: Optional[Callable]) -> Tuple[int, int]:
        """Execute the actual batch insert operation."""
        cursor = conn.cursor()
        total_inserted = 0
        total_failed = 0
        
        try:
            # Generate SQL from first record
            sql = DatabaseUtils.generate_insert_sql(table_name, records[0], ignore_duplicates)
            columns = list(records[0].keys())
            
            # Process in batches
            batch_count = 0
            for i in range(0, len(records), self.batch_size):
                batch_count += 1
                batch = records[i:i + self.batch_size]
                
                try:
                    # Convert to tuples for SQL execution
                    data_tuples = DatabaseUtils.records_to_tuples(batch, columns)
                    
                    # Execute batch
                    inserted = DatabaseUtils.batch_execute(cursor, sql, data_tuples, self.batch_size)
                    total_inserted += inserted
                    
                    # Update progress
                    self.update_progress(i + len(batch), len(records), table_name, progress_callback)
                    
                    # Log batch result
                    self.log_batch_result("insert", batch_count, inserted)
                    
                except Exception as batch_error:
                    batch_failed = self.handle_batch_error(batch_error, len(batch), "insert")
                    total_failed += batch_failed
            
            # Update overall stats
            self.stats.add_operation(
                records_processed=len(records),
                records_inserted=total_inserted,
                records_failed=total_failed
            )
            
            self.logger.info(f"Batch insert complete: {total_inserted} inserted, {total_failed} failed")
            
        finally:
            cursor.close()
        
        return total_inserted, total_failed