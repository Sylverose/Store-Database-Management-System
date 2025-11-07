"""
Data processing exception classes.
Handles data transformation, ETL pipeline, and processing stage errors.
"""

from typing import Optional
from .base_exceptions import ETLException, ErrorSeverity, ErrorCategory, ErrorContext


class ProcessingError(ETLException):
    """Data processing errors."""
    
    def __init__(self, 
                 message: str,
                 error_code: str = "PROCESSING_ERROR",
                 processing_stage: Optional[str] = None,
                 **kwargs):
        """
        Initialize processing error.
        
        Args:
            message: Error message
            error_code: Processing-specific error code
            processing_stage: Stage of processing that failed
            **kwargs: Additional arguments for ETLException
        """
        kwargs.setdefault('category', ErrorCategory.PROCESSING)
        kwargs.setdefault('severity', ErrorSeverity.MEDIUM)
        
        # Add processing-specific context
        context = kwargs.get('context', ErrorContext())
        if processing_stage:
            context.additional_data.update({'processing_stage': processing_stage})
        kwargs['context'] = context
        
        # Default recovery suggestions for processing errors
        if not kwargs.get('recovery_suggestions'):
            kwargs['recovery_suggestions'] = [
                "Review data transformation logic",
                "Check for memory or resource constraints",
                "Validate input data format and structure",
                "Implement error handling for edge cases",
                "Consider batch processing for large datasets"
            ]
        
        super().__init__(message, error_code, **kwargs)