"""
Specialized processor for batch update operations.
"""

import logging
from typing import Dict, List, Optional, Tuple, Callable
from .base_processor import BaseBatchProcessor
from ..utilities import safe_operation

logger = logging.getLogger(__name__)


class UpdateProcessor(BaseBatchProcessor):
    """Handle batch update operations with specialized functionality."""
    
    def update_batch(self, table_name: str, records: List[Dict], 
                    key_columns: List[str], 
                    progress_callback: Optional[Callable] = None) -> Tuple[int, int]:
        """Update records in batches.
        
        Args:
            table_name: Target table name
            records: List of record dictionaries
            key_columns: Columns to use for WHERE clause
            progress_callback: Optional progress callback function
            
        Returns:
            Tuple of (updated_count, failed_count)
        """
        if not records:
            return 0, 0
        
        if not key_columns:
            raise ValueError("Key columns must be specified for update operations")
        
        with safe_operation(f"batch update to {table_name}", self.logger):
            with self.connection_manager.get_connection() as conn:
                if not conn:
                    self.stats.add_operation(records_failed=len(records),
                                           error="No database connection")
                    return 0, len(records)
                
                return self._execute_batch_update(conn, table_name, records, 
                                                key_columns, progress_callback)
    
    def _execute_batch_update(self, conn, table_name: str, records: List[Dict],
                            key_columns: List[str], progress_callback: Optional[Callable]) -> Tuple[int, int]:
        """Execute the actual batch update operation."""
        cursor = conn.cursor()
        total_updated = 0
        total_failed = 0
        
        try:
            # Generate UPDATE SQL
            sample_record = records[0]
            update_columns = [col for col in sample_record.keys() if col not in key_columns]
            
            if not update_columns:
                raise ValueError("No columns to update (all columns are keys)")
            
            set_clause = ', '.join([f"{col} = %s" for col in update_columns])
            where_clause = ' AND '.join([f"{col} = %s" for col in key_columns])
            sql = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"
            
            # Process records individually (updates are typically not batchable in MySQL)
            for i, record in enumerate(records):
                try:
                    # Prepare data: update values + key values
                    update_values = [record.get(col) for col in update_columns]
                    key_values = [record.get(col) for col in key_columns]
                    
                    # Validate that key values exist
                    if None in key_values:
                        missing_keys = [key_columns[j] for j, val in enumerate(key_values) if val is None]
                        raise ValueError(f"Missing key values for columns: {missing_keys}")
                    
                    data = tuple(update_values + key_values)
                    
                    cursor.execute(sql, data)
                    if cursor.rowcount > 0:
                        total_updated += 1
                    
                    # Update progress periodically
                    if (i + 1) % self.batch_size == 0 or i == len(records) - 1:
                        self.update_progress(i + 1, len(records), table_name, progress_callback)
                        self.log_batch_result("update", (i // self.batch_size) + 1, cursor.rowcount)
                    
                except Exception as update_error:
                    total_failed += 1
                    error_msg = f"Update failed for record {i}: {update_error}"
                    self.logger.error(error_msg)
                    self.stats.add_operation(records_failed=1, error=error_msg)
            
            # Update stats
            self.stats.add_operation(
                records_processed=len(records),
                records_updated=total_updated,
                records_failed=total_failed
            )
            
            self.logger.info(f"Batch update complete: {total_updated} updated, {total_failed} failed")
            
        finally:
            cursor.close()
        
        return total_updated, total_failed