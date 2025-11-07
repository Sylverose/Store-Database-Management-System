"""
Specialized processor for batch upsert (INSERT ... ON DUPLICATE KEY UPDATE) operations.
"""

import logging
from typing import Dict, List, Optional, Tuple, Callable
from .base_processor import BaseBatchProcessor
from ..utilities import DatabaseUtils, safe_operation

logger = logging.getLogger(__name__)


class UpsertProcessor(BaseBatchProcessor):
    """Handle batch upsert operations with specialized functionality."""
    
    def upsert_batch(self, table_name: str, records: List[Dict], 
                    key_columns: List[str],
                    progress_callback: Optional[Callable] = None) -> Tuple[int, int, int]:
        """Upsert (INSERT ... ON DUPLICATE KEY UPDATE) records in batches.
        
        Args:
            table_name: Target table name
            records: List of record dictionaries
            key_columns: Columns that define uniqueness
            progress_callback: Optional progress callback function
            
        Returns:
            Tuple of (inserted_count, updated_count, failed_count)
        """
        if not records:
            return 0, 0, 0
        
        if not key_columns:
            raise ValueError("Key columns must be specified for upsert operations")
        
        with safe_operation(f"batch upsert to {table_name}", self.logger):
            with self.connection_manager.get_connection() as conn:
                if not conn:
                    self.stats.add_operation(records_failed=len(records),
                                           error="No database connection")
                    return 0, 0, len(records)
                
                return self._execute_batch_upsert(conn, table_name, records, 
                                                key_columns, progress_callback)
    
    def _execute_batch_upsert(self, conn, table_name: str, records: List[Dict],
                            key_columns: List[str], progress_callback: Optional[Callable]) -> Tuple[int, int, int]:
        """Execute the actual batch upsert operation."""
        cursor = conn.cursor()
        total_inserted = 0
        total_updated = 0
        total_failed = 0
        
        try:
            # Generate UPSERT SQL
            sample_record = records[0]
            columns = list(sample_record.keys())
            placeholders = ', '.join(['%s'] * len(columns))
            
            # UPDATE clause for non-key columns
            update_columns = [col for col in columns if col not in key_columns]
            if update_columns:
                update_clause = ', '.join([f"{col} = VALUES({col})" for col in update_columns])
                sql = (f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders}) "
                       f"ON DUPLICATE KEY UPDATE {update_clause}")
            else:
                # If no update columns, just ignore duplicates
                sql = f"INSERT IGNORE INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
            
            # Process in batches
            batch_count = 0
            for i in range(0, len(records), self.batch_size):
                batch_count += 1
                batch = records[i:i + self.batch_size]
                
                try:
                    # Convert to tuples for SQL execution
                    data_tuples = DatabaseUtils.records_to_tuples(batch, columns)
                    
                    # Execute batch
                    affected_rows = DatabaseUtils.batch_execute(cursor, sql, data_tuples, self.batch_size)
                    
                    # MySQL returns 1 for insert, 2 for update
                    # This is an approximation since we can't distinguish easily in batch mode
                    estimated_inserts = affected_rows // 2
                    estimated_updates = affected_rows - estimated_inserts
                    
                    total_inserted += estimated_inserts
                    total_updated += estimated_updates
                    
                    # Update progress
                    self.update_progress(i + len(batch), len(records), table_name, progress_callback)
                    
                    # Log batch result
                    self.log_batch_result("upsert", batch_count, affected_rows)
                    
                except Exception as batch_error:
                    batch_failed = self.handle_batch_error(batch_error, len(batch), "upsert")
                    total_failed += batch_failed
            
            # Update overall stats
            self.stats.add_operation(
                records_processed=len(records),
                records_inserted=total_inserted,
                records_updated=total_updated,
                records_failed=total_failed
            )
            
            self.logger.info(f"Batch upsert complete: {total_inserted} inserted, {total_updated} updated, {total_failed} failed")
            
        finally:
            cursor.close()
        
        return total_inserted, total_updated, total_failed