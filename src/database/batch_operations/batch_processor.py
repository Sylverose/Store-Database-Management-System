"""
Main batch processor that coordinates all specialized batch operations.
Provides a unified interface while delegating to specialized processors.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple, Callable, Union
from .base_processor import BaseBatchProcessor
from .insert_processor import InsertProcessor
from .update_processor import UpdateProcessor
from .upsert_processor import UpsertProcessor
from .delete_processor import DeleteProcessor

logger = logging.getLogger(__name__)


class BatchProcessor(BaseBatchProcessor):
    """
    Main batch processor that coordinates specialized operation processors.
    
    This class provides a unified interface for all batch operations while
    delegating specific operations to specialized processor classes.
    """
    
    def __init__(self, connection_manager, data_validator=None, batch_size: int = 1000):
        """Initialize the main batch processor.
        
        Args:
            connection_manager: Database connection manager
            data_validator: Optional data validator
            batch_size: Number of records per batch
        """
        super().__init__(connection_manager, data_validator, batch_size)
        
        self.insert_processor = InsertProcessor(connection_manager, data_validator, batch_size)
        self.update_processor = UpdateProcessor(connection_manager, data_validator, batch_size)
        self.upsert_processor = UpsertProcessor(connection_manager, data_validator, batch_size)
        self.delete_processor = DeleteProcessor(connection_manager, data_validator, batch_size)
        
        self.processors = [
            self.insert_processor,
            self.update_processor,
            self.upsert_processor,
            self.delete_processor
        ]
    
    # ============================================================================
    # INSERT OPERATIONS - Delegate to InsertProcessor
    # ============================================================================
    
    def insert_batch(self, table_name: str, records: List[Dict], 
                    progress_callback: Optional[Callable] = None, 
                    ignore_duplicates: bool = True,
                    validate_data: bool = True) -> Tuple[int, int]:
        """Insert records in batches. Delegates to InsertProcessor."""
        return self.insert_processor.insert_batch(
            table_name, records, progress_callback, ignore_duplicates, validate_data
        )
    
    # ============================================================================
    # UPDATE OPERATIONS - Delegate to UpdateProcessor
    # ============================================================================
    
    def update_batch(self, table_name: str, records: List[Dict], 
                    key_columns: List[str], 
                    progress_callback: Optional[Callable] = None) -> Tuple[int, int]:
        """Update records in batches. Delegates to UpdateProcessor."""
        return self.update_processor.update_batch(table_name, records, key_columns, progress_callback)
    
    # ============================================================================
    # UPSERT OPERATIONS - Delegate to UpsertProcessor
    # ============================================================================
    
    def upsert_batch(self, table_name: str, records: List[Dict], 
                    key_columns: List[str],
                    progress_callback: Optional[Callable] = None) -> Tuple[int, int, int]:
        """Upsert records in batches. Delegates to UpsertProcessor."""
        return self.upsert_processor.upsert_batch(table_name, records, key_columns, progress_callback)
    
    # ============================================================================
    # DELETE OPERATIONS - Delegate to DeleteProcessor  
    # ============================================================================
    
    def delete_batch(self, table_name: str, conditions: List[Dict],
                    progress_callback: Optional[Callable] = None) -> Tuple[int, int]:
        """Delete records in batches. Delegates to DeleteProcessor."""
        return self.delete_processor.delete_batch(table_name, conditions, progress_callback)
    
    # ============================================================================
    # STATISTICS AND UTILITY METHODS
    # ============================================================================
    
    def get_stats(self) -> Dict:
        """Get aggregated statistics from all processors."""
        combined_stats = {
            'total_operations': 0,
            'total_records_processed': 0,
            'total_records_inserted': 0,
            'total_records_updated': 0,
            'total_records_failed': 0,
            'processor_stats': {}
        }
        
        for processor in self.processors:
            processor_name = processor.__class__.__name__
            processor_stats = processor.get_stats()
            combined_stats['processor_stats'][processor_name] = processor_stats
            
            combined_stats['total_operations'] += processor_stats.get('total_operations', 0)
            combined_stats['total_records_processed'] += processor_stats.get('total_records_processed', 0)
            combined_stats['total_records_inserted'] += processor_stats.get('total_records_inserted', 0)
            combined_stats['total_records_updated'] += processor_stats.get('total_records_updated', 0)
            combined_stats['total_records_failed'] += processor_stats.get('total_records_failed', 0)
        
        return combined_stats
    
    def get_stats_summary(self) -> str:
        """Get human-readable statistics summary."""
        stats = self.get_stats()
        
        summary_lines = [
            "=== Batch Processor Statistics ===",
            f"Total Operations: {stats['total_operations']}",
            f"Records Processed: {stats['total_records_processed']}",
            f"Records Inserted: {stats['total_records_inserted']}",
            f"Records Updated: {stats['total_records_updated']}",
            f"Records Failed: {stats['total_records_failed']}",
            "",
            "=== Per-Processor Statistics ==="
        ]
        
        for processor_name, processor_stats in stats['processor_stats'].items():
            if processor_stats.get('total_operations', 0) > 0:
                summary_lines.extend([
                    f"{processor_name}:",
                    f"  Operations: {processor_stats.get('total_operations', 0)}",
                    f"  Processed: {processor_stats.get('total_records_processed', 0)}",
                    f"  Inserted: {processor_stats.get('total_records_inserted', 0)}",
                    f"  Updated: {processor_stats.get('total_records_updated', 0)}",
                    f"  Failed: {processor_stats.get('total_records_failed', 0)}",
                    ""
                ])
        
        return "\n".join(summary_lines)
    
    def reset_stats(self):
        """Reset statistics for all processors."""
        for processor in self.processors:
            processor.reset_stats()
        self.stats.reset()
    
    def get_processor_by_operation(self, operation_type: str):
        """Get specific processor by operation type.
        
        Args:
            operation_type: Type of operation ('insert', 'update', 'upsert', 'delete')
            
        Returns:
            Specialized processor instance
        """
        processor_map = {
            'insert': self.insert_processor,
            'update': self.update_processor,
            'upsert': self.upsert_processor,
            'delete': self.delete_processor
        }
        
        if operation_type not in processor_map:
            raise ValueError(f"Unknown operation type: {operation_type}")
        
        return processor_map[operation_type]
    
    def set_batch_size(self, batch_size: int):
        """Update batch size for all processors.
        
        Args:
            batch_size: New batch size
        """
        self.batch_size = batch_size
        for processor in self.processors:
            processor.batch_size = batch_size
    
    def get_operation_summary(self) -> Dict[str, int]:
        """Get summary of operations performed by type."""
        summary = {
            'insert_operations': 0,
            'update_operations': 0,
            'upsert_operations': 0,
            'delete_operations': 0
        }
        
        stats = self.get_stats()
        for processor_name, processor_stats in stats['processor_stats'].items():
            operations = processor_stats.get('total_operations', 0)
            if 'Insert' in processor_name:
                summary['insert_operations'] += operations
            elif 'Update' in processor_name:
                summary['update_operations'] += operations
            elif 'Upsert' in processor_name:
                summary['upsert_operations'] += operations
            elif 'Delete' in processor_name:
                summary['delete_operations'] += operations
        
        return summary