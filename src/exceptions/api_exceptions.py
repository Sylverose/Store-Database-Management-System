"""
API-related exception classes.
Handles HTTP requests, API responses, and external service errors.
"""

from typing import Dict, Optional
from .base_exceptions import ETLException, ErrorSeverity, ErrorCategory, ErrorContext


class APIError(ETLException):
    """API-related errors."""
    
    def __init__(self, 
                 message: str,
                 error_code: str = "API_ERROR",
                 status_code: Optional[int] = None,
                 endpoint: Optional[str] = None,
                 response_data: Optional[Dict] = None,
                 **kwargs):
        """
        Initialize API error.
        
        Args:
            message: Error message
            error_code: API-specific error code
            status_code: HTTP status code
            endpoint: API endpoint that failed
            response_data: API response data
            **kwargs: Additional arguments for ETLException
        """
        kwargs.setdefault('category', ErrorCategory.API)
        
        # Set severity based on status code
        if status_code:
            if status_code >= 500:
                kwargs.setdefault('severity', ErrorSeverity.HIGH)
            elif status_code >= 400:
                kwargs.setdefault('severity', ErrorSeverity.MEDIUM)
            else:
                kwargs.setdefault('severity', ErrorSeverity.LOW)
        else:
            kwargs.setdefault('severity', ErrorSeverity.MEDIUM)
        
        # Add API-specific context
        context = kwargs.get('context', ErrorContext())
        if status_code:
            context.additional_data.update({'status_code': status_code})
        if endpoint:
            context.additional_data.update({'endpoint': endpoint})
        if response_data:
            context.additional_data.update({'response_data': response_data})
        kwargs['context'] = context
        
        # Default recovery suggestions for API errors
        if not kwargs.get('recovery_suggestions'):
            suggestions = [
                "Check API endpoint URL and method",
                "Verify API authentication credentials",
                "Review request parameters and headers",
                "Check network connectivity",
                "Implement retry logic with exponential backoff"
            ]
            
            # Add status code specific suggestions
            if status_code == 401:
                suggestions.insert(0, "Update or refresh authentication token")
            elif status_code == 403:
                suggestions.insert(0, "Verify API permissions and access rights")
            elif status_code == 404:
                suggestions.insert(0, "Confirm API endpoint exists and is accessible")
            elif status_code == 429:
                suggestions.insert(0, "Implement rate limiting and backoff strategy")
            elif status_code >= 500:
                suggestions.insert(0, "Server error - retry after waiting period")
            
            kwargs['recovery_suggestions'] = suggestions
        
        super().__init__(message, error_code, **kwargs)