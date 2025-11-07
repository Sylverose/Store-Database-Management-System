"""
Specialized processor for batch delete operations.
"""

import logging
from typing import Dict, List, Optional, Tuple, Callable, Union
from .base_processor import BaseBatchProcessor
from ..utilities import safe_operation

logger = logging.getLogger(__name__)


class DeleteProcessor(BaseBatchProcessor):
    """Handle batch delete operations with specialized functionality."""
    
    def delete_batch(self, table_name: str, conditions: List[Dict],
                    progress_callback: Optional[Callable] = None) -> Tuple[int, int]:
        """Delete records in batches based on conditions.
        
        Args:
            table_name: Target table name
            conditions: List of condition dictionaries (column: value pairs)
            progress_callback: Optional progress callback function
            
        Returns:
            Tuple of (deleted_count, failed_count)
        """
        if not conditions:
            return 0, 0
        
        with safe_operation(f"batch delete from {table_name}", self.logger):
            with self.connection_manager.get_connection() as conn:
                if not conn:
                    self.stats.add_operation(records_failed=len(conditions),
                                           error="No database connection")
                    return 0, len(conditions)
                
                return self._execute_batch_delete(conn, table_name, conditions, progress_callback)
    
    def _execute_batch_delete(self, conn, table_name: str, conditions: List[Dict],
                            progress_callback: Optional[Callable]) -> Tuple[int, int]:
        """Execute the actual batch delete operation."""
        cursor = conn.cursor()
        total_deleted = 0
        total_failed = 0
        
        try:
            for i, condition in enumerate(conditions):
                try:
                    # Build WHERE clause
                    where_parts = []
                    values = []
                    for col, value in condition.items():
                        if value is None:
                            where_parts.append(f"{col} IS NULL")
                        else:
                            where_parts.append(f"{col} = %s")
                            values.append(value)
                    
                    where_clause = " AND ".join(where_parts)
                    sql = f"DELETE FROM {table_name} WHERE {where_clause}"
                    
                    cursor.execute(sql, tuple(values))
                    deleted_count = cursor.rowcount
                    total_deleted += deleted_count
                    
                    # Update progress periodically
                    if (i + 1) % self.batch_size == 0 or i == len(conditions) - 1:
                        self.update_progress(i + 1, len(conditions), table_name, progress_callback)
                        self.log_batch_result("delete", (i // self.batch_size) + 1, deleted_count)
                    
                except Exception as delete_error:
                    total_failed += 1
                    error_msg = f"Delete failed for condition {condition}: {delete_error}"
                    self.logger.error(error_msg)
                    self.stats.add_operation(records_failed=1, error=error_msg)
            
            # Update stats
            self.stats.add_operation(
                records_processed=len(conditions),
                records_updated=total_deleted,  # Using updated counter for deletes
                records_failed=total_failed
            )
            
            self.logger.info(f"Batch delete complete: {total_deleted} deleted, {total_failed} failed")
            
        finally:
            cursor.close()
        
        return total_deleted, total_failed