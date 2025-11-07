"""
Base exception classes and core enums for ETL operations.
Provides the foundation for all ETL-specific exceptions.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
import traceback
from datetime import datetime


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high" 
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error category types."""
    DATABASE = "database"
    VALIDATION = "validation"
    CONFIGURATION = "configuration"
    API = "api"
    PROCESSING = "processing"
    AUTHENTICATION = "authentication"
    NETWORK = "network"
    FILE_SYSTEM = "file_system"
    MEMORY = "memory"


@dataclass
class ErrorContext:
    """Context information for errors."""
    
    operation: str = ""
    component: str = ""
    table_name: Optional[str] = None
    file_path: Optional[str] = None
    record_count: Optional[int] = None
    additional_data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'operation': self.operation,
            'component': self.component,
            'table_name': self.table_name,
            'file_path': self.file_path,
            'record_count': self.record_count,
            'additional_data': self.additional_data,
            'timestamp': self.timestamp.isoformat()
        }


class ETLException(Exception):
    """Base exception for all ETL operations."""
    
    def __init__(self, 
                 message: str,
                 error_code: str = "ETL_UNKNOWN",
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                 category: ErrorCategory = ErrorCategory.PROCESSING,
                 context: Optional[ErrorContext] = None,
                 recovery_suggestions: Optional[List[str]] = None,
                 original_exception: Optional[Exception] = None):
        """
        Initialize ETL exception.
        
        Args:
            message: Error message
            error_code: Unique error code
            severity: Error severity level
            category: Error category
            context: Additional context information
            recovery_suggestions: List of recovery suggestions
            original_exception: Original exception that caused this error
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.severity = severity
        self.category = category
        self.context = context or ErrorContext()
        self.recovery_suggestions = recovery_suggestions or []
        self.original_exception = original_exception
        self.traceback_info = traceback.format_exc() if original_exception else None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging/serialization."""
        return {
            'error_type': self.__class__.__name__,
            'message': self.message,
            'error_code': self.error_code,
            'severity': self.severity.value,
            'category': self.category.value,
            'context': self.context.to_dict(),
            'recovery_suggestions': self.recovery_suggestions,
            'original_exception': str(self.original_exception) if self.original_exception else None,
            'traceback': self.traceback_info
        }
    
    def __str__(self) -> str:
        """String representation with context."""
        base_msg = f"[{self.error_code}] {self.message}"
        
        if self.context.operation:
            base_msg += f" (Operation: {self.context.operation})"
        
        if self.context.component:
            base_msg += f" (Component: {self.context.component})"
        
        if self.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            base_msg += f" [SEVERITY: {self.severity.value.upper()}]"
        
        return base_msg