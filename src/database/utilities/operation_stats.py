"""
Database operation statistics tracking (simplified).
"""

import time
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class OperationStats:
    """Track database operation statistics with core metrics."""
    
    def __init__(self):
        """Initialize statistics tracking."""
        self.reset()
    
    def reset(self):
        """Reset all statistics."""
        self.stats = {
            'total_operations': 0,
            'total_records_processed': 0,
            'total_records_inserted': 0,
            'total_records_updated': 0,
            'total_records_deleted': 0,
            'total_records_failed': 0,
            'total_execution_time': 0.0,
            'operations_by_type': {},
            'operations_by_table': {},
            'errors': [],
            'start_time': None,
            'last_operation_time': None
        }
    
    def start_operation(self) -> float:
        """Start timing an operation. Returns start timestamp."""
        start_time = time.time()
        if self.stats['start_time'] is None:
            self.stats['start_time'] = start_time
        return start_time
    
    def end_operation(self, start_time: float, operation_type: str = 'unknown', 
                     table_name: str = None) -> float:
        """End timing an operation and record duration.
        
        Returns:
            Operation duration in seconds
        """
        end_time = time.time()
        duration = end_time - start_time
        
        self.stats['total_execution_time'] += duration
        self.stats['last_operation_time'] = end_time
        
        # Track by operation type
        if operation_type not in self.stats['operations_by_type']:
            self.stats['operations_by_type'][operation_type] = {
                'count': 0, 'total_time': 0.0, 'avg_time': 0.0
            }
        
        op_stats = self.stats['operations_by_type'][operation_type]
        op_stats['count'] += 1
        op_stats['total_time'] += duration
        op_stats['avg_time'] = op_stats['total_time'] / op_stats['count']
        
        # Track by table
        if table_name:
            if table_name not in self.stats['operations_by_table']:
                self.stats['operations_by_table'][table_name] = {
                    'operations': 0, 'records_processed': 0, 'total_time': 0.0
                }
            
            table_stats = self.stats['operations_by_table'][table_name]
            table_stats['operations'] += 1
            table_stats['total_time'] += duration
        
        return duration
    
    def add_operation(self, records_processed: int = 0, records_inserted: int = 0, 
                     records_updated: int = 0, records_deleted: int = 0, 
                     records_failed: int = 0, error: str = None,
                     operation_type: str = None, table_name: str = None):
        """Add operation results to statistics."""
        self.stats['total_operations'] += 1
        self.stats['total_records_processed'] += records_processed
        self.stats['total_records_inserted'] += records_inserted
        self.stats['total_records_updated'] += records_updated
        self.stats['total_records_deleted'] += records_deleted
        self.stats['total_records_failed'] += records_failed
        
        # Track by table
        if table_name:
            if table_name not in self.stats['operations_by_table']:
                self.stats['operations_by_table'][table_name] = {
                    'operations': 0, 'records_processed': 0, 'total_time': 0.0
                }
            
            self.stats['operations_by_table'][table_name]['records_processed'] += records_processed
        
        # Add error if provided
        if error:
            self.stats['errors'].append({
                'timestamp': datetime.now().isoformat(),
                'error': error,
                'operation_type': operation_type,
                'table_name': table_name
            })
    
    def get_stats(self) -> Dict:
        """Get copy of current statistics."""
        return self.stats.copy()
    
    def get_summary(self) -> str:
        """Get human-readable summary. Returns one-line stats string."""
        stats = self.stats
        
        lines = [
            f"Operations: {stats['total_operations']}",
            f"Processed: {stats['total_records_processed']}",
            f"Inserted: {stats['total_records_inserted']}",
            f"Updated: {stats['total_records_updated']}",
            f"Failed: {stats['total_records_failed']}",
            f"Time: {stats['total_execution_time']:.2f}s"
        ]
        
        if stats['errors']:
            lines.append(f"Errors: {len(stats['errors'])}")
        
        return " | ".join(lines)
