"""
System-related exception classes.
Handles configuration, file system, memory, and infrastructure errors.
"""

from typing import Dict, Any, List, Optional
from .base_exceptions import ETLException, ErrorSeverity, ErrorCategory, ErrorContext


class ConfigurationError(ETLException):
    """Configuration-related errors."""
    
    def __init__(self, 
                 message: str,
                 error_code: str = "CONFIG_ERROR",
                 config_section: Optional[str] = None,
                 invalid_keys: Optional[List[str]] = None,
                 **kwargs):
        """
        Initialize configuration error.
        
        Args:
            message: Error message
            error_code: Configuration-specific error code
            config_section: Configuration section that failed
            invalid_keys: List of invalid configuration keys
            **kwargs: Additional arguments for ETLException
        """
        kwargs.setdefault('category', ErrorCategory.CONFIGURATION)
        kwargs.setdefault('severity', ErrorSeverity.HIGH)
        
        # Add configuration-specific context
        context = kwargs.get('context', ErrorContext())
        if config_section:
            context.additional_data.update({'config_section': config_section})
        if invalid_keys:
            context.additional_data.update({'invalid_keys': invalid_keys})
        kwargs['context'] = context
        
        # Default recovery suggestions for configuration errors
        if not kwargs.get('recovery_suggestions'):
            kwargs['recovery_suggestions'] = [
                "Review configuration file syntax",
                "Verify all required configuration keys are present",
                "Check configuration value types and formats",
                "Validate environment-specific settings",
                "Consult configuration documentation"
            ]
        
        super().__init__(message, error_code, **kwargs)


class FileSystemError(ETLException):
    """File system related errors."""
    
    def __init__(self, 
                 message: str,
                 error_code: str = "FILE_SYSTEM_ERROR",
                 file_path: Optional[str] = None,
                 **kwargs):
        """
        Initialize file system error.
        
        Args:
            message: Error message
            error_code: File system-specific error code
            file_path: Path to file that caused the error
            **kwargs: Additional arguments for ETLException
        """
        kwargs.setdefault('category', ErrorCategory.FILE_SYSTEM)
        kwargs.setdefault('severity', ErrorSeverity.MEDIUM)
        
        # Add file system-specific context
        context = kwargs.get('context', ErrorContext())
        if file_path:
            context.file_path = file_path
        kwargs['context'] = context
        
        # Default recovery suggestions for file system errors
        if not kwargs.get('recovery_suggestions'):
            kwargs['recovery_suggestions'] = [
                "Verify file path exists and is accessible",
                "Check file permissions (read/write access)",
                "Ensure sufficient disk space",
                "Validate file format and encoding",
                "Check for file locks or concurrent access"
            ]
        
        super().__init__(message, error_code, **kwargs)


class MemoryError(ETLException):
    """Memory-related errors."""
    
    def __init__(self, 
                 message: str,
                 error_code: str = "MEMORY_ERROR",
                 memory_usage_mb: Optional[float] = None,
                 **kwargs):
        """
        Initialize memory error.
        
        Args:
            message: Error message
            error_code: Memory-specific error code
            memory_usage_mb: Current memory usage in MB
            **kwargs: Additional arguments for ETLException
        """
        kwargs.setdefault('category', ErrorCategory.MEMORY)
        kwargs.setdefault('severity', ErrorSeverity.HIGH)
        
        # Add memory-specific context
        context = kwargs.get('context', ErrorContext())
        if memory_usage_mb:
            context.additional_data.update({'memory_usage_mb': memory_usage_mb})
        kwargs['context'] = context
        
        # Default recovery suggestions for memory errors
        if not kwargs.get('recovery_suggestions'):
            kwargs['recovery_suggestions'] = [
                "Implement chunked processing for large datasets",
                "Optimize data types to reduce memory usage",
                "Clear unnecessary variables and force garbage collection",
                "Increase available memory or use memory-efficient algorithms",
                "Consider streaming processing instead of loading all data"
            ]
        
        super().__init__(message, error_code, **kwargs)