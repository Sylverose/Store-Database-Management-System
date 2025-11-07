"""
Data validation exception classes.
Handles schema validation, data quality, and validation rule errors.
"""

from typing import Dict, List, Optional
from .base_exceptions import ETLException, ErrorSeverity, ErrorCategory, ErrorContext


class ValidationError(ETLException):
    """Data validation errors."""
    
    def __init__(self, 
                 message: str,
                 error_code: str = "VALIDATION_ERROR",
                 failed_records: Optional[List[Dict]] = None,
                 validation_rules: Optional[List[str]] = None,
                 **kwargs):
        """
        Initialize validation error.
        
        Args:
            message: Error message
            error_code: Validation-specific error code
            failed_records: Records that failed validation
            validation_rules: List of failed validation rules
            **kwargs: Additional arguments for ETLException
        """
        kwargs.setdefault('category', ErrorCategory.VALIDATION)
        kwargs.setdefault('severity', ErrorSeverity.MEDIUM)
        
        # Add validation-specific context
        context = kwargs.get('context', ErrorContext())
        if failed_records:
            context.additional_data.update({'failed_records': failed_records})
        if validation_rules:
            context.additional_data.update({'validation_rules': validation_rules})
        kwargs['context'] = context
        
        # Default recovery suggestions for validation errors
        if not kwargs.get('recovery_suggestions'):
            kwargs['recovery_suggestions'] = [
                "Review data quality and format requirements",
                "Check for null values in required fields",
                "Validate data types and ranges",
                "Apply data cleansing rules",
                "Update validation rules if needed"
            ]
        
        super().__init__(message, error_code, **kwargs)


class SchemaValidationError(ValidationError):
    """Schema validation specific errors."""
    
    def __init__(self, message: str, **kwargs):
        kwargs.setdefault('error_code', 'SCHEMA_VALIDATION_ERROR')
        kwargs.setdefault('recovery_suggestions', [
            "Verify column names match expected schema",
            "Check data types are compatible",
            "Ensure required columns are present",
            "Review schema documentation",
            "Update data mapping configuration"
        ])
        super().__init__(message, **kwargs)


class DataQualityError(ValidationError):
    """Data quality specific errors."""
    
    def __init__(self, message: str, **kwargs):
        kwargs.setdefault('error_code', 'DATA_QUALITY_ERROR')
        kwargs.setdefault('recovery_suggestions', [
            "Apply data cleansing transformations",
            "Remove or fix invalid records",
            "Update validation thresholds",
            "Implement data normalization",
            "Review data source quality"
        ])
        super().__init__(message, **kwargs)