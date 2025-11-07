"""
Base batch processor with common functionality.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple, Callable
from ..utilities import DatabaseUtils, DataUtils, safe_operation, OperationStats

logger = logging.getLogger(__name__)


class BaseBatchProcessor:
    """Base class for all batch processors with common functionality."""
    
    def __init__(self, connection_manager, data_validator=None, batch_size: int = 1000):
        """Initialize base batch processor.
        
        Args:
            connection_manager: Database connection manager
            data_validator: Optional data validator
            batch_size: Number of records per batch
        """
        self.connection_manager = connection_manager
        self.data_validator = data_validator
        self.batch_size = batch_size
        self.stats = OperationStats()
        self.logger = logger
    
    def validate_records(self, records: List[Dict]) -> Tuple[List[Dict], List[str]]:
        """Validate records if validator is available.
        
        Args:
            records: List of record dictionaries
            
        Returns:
            Tuple of (validated_records, validation_errors)
        """
        if self.data_validator:
            return DataUtils.validate_records(records)
        return records, []
    
    def update_progress(self, current: int, total: int, table_name: str, 
                       progress_callback: Optional[Callable] = None):
        """Update progress if callback is provided.
        
        Args:
            current: Current progress count
            total: Total items to process
            table_name: Name of the table being processed
            progress_callback: Optional callback function
        """
        if progress_callback:
            progress_callback(current, total, table_name)
    
    def log_batch_result(self, operation: str, batch_num: int, records_affected: int):
        """Log batch processing results.
        
        Args:
            operation: Type of operation (insert, update, etc.)
            batch_num: Batch number
            records_affected: Number of records affected
        """
        self.logger.debug(f"Batch {batch_num} {operation}: {records_affected} records affected")
    
    def handle_batch_error(self, error: Exception, batch_size: int, operation: str) -> int:
        """Handle batch processing errors.
        
        Args:
            error: The exception that occurred
            batch_size: Size of the failed batch
            operation: Type of operation that failed
            
        Returns:
            Number of failed records
        """
        error_msg = f"Batch {operation} failed: {error}"
        self.logger.error(error_msg)
        self.stats.add_operation(records_failed=batch_size, error=error_msg)
        return batch_size
    
    def get_stats(self) -> Dict:
        """Get processing statistics."""
        return self.stats.get_stats()
    
    def get_stats_summary(self) -> str:
        """Get human-readable statistics summary."""
        return self.stats.get_summary()
    
    def reset_stats(self):
        """Reset processing statistics."""
        self.stats.reset()