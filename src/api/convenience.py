"""
Convenience functions for common API operations.
"""

from typing import List, Dict, Optional

from .api_models import APIRequest, APIResponse, RequestMethod
from .api_client import AsyncAPIClient
from .retry_handler import RetryConfig


async def fetch_json_data(urls: List[str],
                         headers: Dict[str, str] = None,
                         max_concurrent: int = 10,
                         retry_config: RetryConfig = None) -> List[APIResponse]:
    """
    Convenience function to fetch JSON data from multiple URLs.
    
    Args:
        urls: List of URLs to fetch
        headers: Optional headers
        max_concurrent: Maximum concurrent requests
        retry_config: Retry configuration
        
    Returns:
        List of API responses
    """
    # Create requests
    requests = [
        APIRequest(
            url=url,
            method=RequestMethod.GET,
            headers=headers or {}
        )
        for url in urls
    ]
    
    # Execute with API client
    async with AsyncAPIClient(
        default_headers=headers or {},
        max_concurrent=max_concurrent,
        retry_config=retry_config or RetryConfig()
    ) as client:
        return await client.batch_requests(requests)