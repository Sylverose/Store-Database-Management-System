"""
Core asynchronous HTTP client with connection pooling and error handling.
"""

import asyncio
import aiohttp
import time
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from contextlib import nullcontext

from .api_models import APIRequest, APIResponse, RequestMethod
from .rate_limiter import RateLimitConfig, RateLimiter
from .retry_handler import RetryConfig

# Import structured logging
try:
    from ..logging_system import get_api_logger, performance_context
    LOGGING_AVAILABLE = True
except ImportError:
    LOGGING_AVAILABLE = False
    logging.basicConfig(level=logging.INFO)

# Import ETL exceptions
try:
    from ..exceptions import APIError, ErrorContext, create_api_error
    ETL_EXCEPTIONS_AVAILABLE = True
except ImportError:
    ETL_EXCEPTIONS_AVAILABLE = False

# Get logger
logger = get_api_logger() if LOGGING_AVAILABLE else logging.getLogger(__name__)


class AsyncAPIClient:
    """Asynchronous API client with connection pooling and advanced features."""
    
    def __init__(self,
                 base_url: str = "",
                 default_headers: Dict[str, str] = None,
                 timeout: float = 30.0,
                 retry_config: RetryConfig = None,
                 rate_limit_config: RateLimitConfig = None,
                 max_concurrent: int = 10):
        """
        Initialize async API client.
        
        Args:
            base_url: Base URL for API requests
            default_headers: Default headers for all requests
            timeout: Default timeout for requests
            retry_config: Retry configuration
            rate_limit_config: Rate limiting configuration
            max_concurrent: Maximum concurrent requests
        """
        self.base_url = base_url.rstrip('/')
        self.default_headers = default_headers or {}
        self.timeout = timeout
        self.retry_config = retry_config or RetryConfig()
        self.rate_limit_config = rate_limit_config or RateLimitConfig()
        self.max_concurrent = max_concurrent
        
        # Rate limiter
        self.rate_limiter = RateLimiter(self.rate_limit_config)
        
        # Semaphore for concurrent request limiting
        self.semaphore = asyncio.Semaphore(max_concurrent)
        
        # Session will be created when first needed
        self._session: Optional[aiohttp.ClientSession] = None
        
        # Statistics
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'retried_requests': 0,
            'total_response_time': 0.0,
            'rate_limited_waits': 0
        }
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def _ensure_session(self):
        """Ensure aiohttp session exists."""
        if self._session is None or self._session.closed:
            # Configure connection pooling
            connector = aiohttp.TCPConnector(
                limit=100,  # Total connection pool size
                limit_per_host=30,  # Per-host connection limit
                ttl_dns_cache=300,  # DNS cache TTL
                use_dns_cache=True,
                keepalive_timeout=60,
                enable_cleanup_closed=True
            )
            
            # Create timeout configuration
            timeout_config = aiohttp.ClientTimeout(
                total=self.timeout,
                connect=10.0,
                sock_read=self.timeout
            )
            
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout_config,
                headers=self.default_headers
            )
            
            logger.debug("Created new aiohttp session with connection pooling")
    
    async def close(self):
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
            logger.debug("Closed aiohttp session")
    
    async def request(self, api_request: APIRequest) -> APIResponse:
        """
        Execute single API request with retry and rate limiting.
        
        Args:
            api_request: API request configuration
            
        Returns:
            APIResponse object
        """
        await self._ensure_session()
        
        # Rate limiting
        wait_time = await self.rate_limiter.acquire()
        if wait_time > 0:
            logger.debug(f"Rate limiting: waiting {wait_time:.2f} seconds")
            await asyncio.sleep(wait_time)
            self.stats['rate_limited_waits'] += 1
        
        # Concurrent request limiting
        async with self.semaphore:
            return await self._execute_request_with_retry(api_request)
    
    async def _execute_request_with_retry(self, api_request: APIRequest) -> APIResponse:
        """Execute request with retry mechanism."""
        last_exception = None
        
        for attempt in range(self.retry_config.max_retries + 1):
            try:
                start_time = time.time()
                
                # Prepare request
                url = self._build_url(api_request.url)
                headers = {**self.default_headers, **api_request.headers}
                
                # Execute request
                async with self._session.request(
                    method=api_request.method.value,
                    url=url,
                    headers=headers,
                    params=api_request.params,
                    json=api_request.data if isinstance(api_request.data, dict) else None,
                    data=api_request.data if isinstance(api_request.data, str) else None,
                    timeout=aiohttp.ClientTimeout(total=api_request.timeout)
                ) as response:
                    
                    # Read response data
                    try:
                        if response.content_type == 'application/json':
                            response_data = await response.json()
                        else:
                            response_data = await response.text()
                    except Exception:
                        response_data = await response.text()
                    
                    request_time = time.time() - start_time
                    
                    # Update statistics
                    self.stats['total_requests'] += 1
                    self.stats['total_response_time'] += request_time
                    
                    # Create response object
                    api_response = APIResponse(
                        status=response.status,
                        data=response_data,
                        headers=dict(response.headers),
                        url=str(response.url),
                        request_time=request_time,
                        response_time=datetime.now(),
                        metadata=api_request.metadata.copy()
                    )
                    
                    # Check if retry is needed
                    if response.status in self.retry_config.retry_on_status and attempt < self.retry_config.max_retries:
                        logger.warning(f"Request failed with status {response.status}, retrying (attempt {attempt + 1})")
                        self.stats['retried_requests'] += 1
                        
                        # Wait before retry
                        delay = self.retry_config.calculate_delay(attempt)
                        await asyncio.sleep(delay)
                        continue
                    
                    # Update success/failure stats
                    if api_response.success:
                        self.stats['successful_requests'] += 1
                    else:
                        self.stats['failed_requests'] += 1
                        
                        # Create structured exception for failed requests
                        if ETL_EXCEPTIONS_AVAILABLE:
                            context = ErrorContext(
                                operation="api_request",
                                component="async_api_client",
                                additional_data={
                                    'url': url,
                                    'method': api_request.method.value,
                                    'status_code': response.status
                                }
                            )
                            
                            raise create_api_error(
                                f"API request failed with status {response.status}",
                                status_code=response.status,
                                endpoint=url,
                                context=context,
                                response_data=response_data
                            )
                    
                    return api_response
                    
            except asyncio.TimeoutError as e:
                last_exception = e
                logger.warning(f"Request timeout (attempt {attempt + 1}): {api_request.url}")
                
                if attempt < self.retry_config.max_retries:
                    delay = self.retry_config.calculate_delay(attempt)
                    await asyncio.sleep(delay)
                    continue
                
            except aiohttp.ClientError as e:
                last_exception = e
                logger.warning(f"Client error (attempt {attempt + 1}): {e}")
                
                if attempt < self.retry_config.max_retries:
                    delay = self.retry_config.calculate_delay(attempt)
                    await asyncio.sleep(delay)
                    continue
                
            except Exception as e:
                last_exception = e
                logger.error(f"Unexpected error (attempt {attempt + 1}): {e}")
                
                if attempt < self.retry_config.max_retries:
                    delay = self.retry_config.calculate_delay(attempt)
                    await asyncio.sleep(delay)
                    continue
        
        # All retries failed
        self.stats['failed_requests'] += 1
        
        if ETL_EXCEPTIONS_AVAILABLE:
            context = ErrorContext(
                operation="api_request_with_retry",
                component="async_api_client",
                additional_data={
                    'url': api_request.url,
                    'method': api_request.method.value,
                    'max_retries': self.retry_config.max_retries
                }
            )
            
            raise APIError(
                f"API request failed after {self.retry_config.max_retries} retries: {last_exception}",
                error_code="API_MAX_RETRIES_EXCEEDED",
                context=context,
                original_exception=last_exception
            )
        else:
            raise last_exception
    
    async def batch_requests(self, 
                           requests: List[APIRequest],
                           progress_callback: Optional[Callable] = None) -> List[APIResponse]:
        """
        Execute multiple API requests concurrently.
        
        Args:
            requests: List of API requests to execute
            progress_callback: Optional progress callback function
            
        Returns:
            List of API responses
        """
        context_manager = (performance_context("batch_api_requests", logger)
                          if LOGGING_AVAILABLE else nullcontext())
        
        with context_manager:
            logger.info(f"Starting batch execution of {len(requests)} API requests")
            
            # Create tasks for concurrent execution
            tasks = []
            for i, request in enumerate(requests):
                # Add index to metadata for tracking
                request.metadata['batch_index'] = i
                task = asyncio.create_task(self.request(request))
                tasks.append(task)
            
            # Execute with progress tracking
            responses = []
            completed = 0
            
            for coro in asyncio.as_completed(tasks):
                try:
                    response = await coro
                    responses.append(response)
                    completed += 1
                    
                    if progress_callback:
                        progress = (completed / len(requests)) * 100
                        progress_callback(progress, f"Completed {completed}/{len(requests)} requests")
                    
                    if completed % 10 == 0:  # Log every 10 completions
                        logger.debug(f"Completed {completed}/{len(requests)} requests")
                        
                except Exception as e:
                    logger.error(f"Request failed in batch: {e}")
                    # Create a failed response
                    failed_response = APIResponse(
                        status=0,
                        data={'error': str(e)},
                        headers={},
                        url="unknown",
                        request_time=0.0,
                        response_time=datetime.now()
                    )
                    responses.append(failed_response)
                    completed += 1
            
            # Sort responses by original order
            responses.sort(key=lambda r: r.metadata.get('batch_index', 0))
            
            logger.info(f"Batch execution complete: {len(responses)} responses")
            return responses
    
    async def paginated_requests(self,
                               base_request: APIRequest,
                               page_param: str = "page",
                               size_param: str = "size",
                               page_size: int = 100,
                               max_pages: Optional[int] = None) -> List[APIResponse]:
        """
        Handle paginated API requests automatically.
        
        Args:
            base_request: Base request configuration
            page_param: Parameter name for page number
            size_param: Parameter name for page size
            page_size: Number of items per page
            max_pages: Maximum number of pages to fetch
            
        Returns:
            List of all page responses
        """
        logger.info(f"Starting paginated requests with page size {page_size}")
        
        responses = []
        page = 1
        
        while max_pages is None or page <= max_pages:
            # Create request for current page
            page_request = APIRequest(
                url=base_request.url,
                method=base_request.method,
                headers=base_request.headers.copy(),
                params={
                    **base_request.params,
                    page_param: page,
                    size_param: page_size
                },
                data=base_request.data,
                timeout=base_request.timeout,
                metadata={**base_request.metadata, 'page': page}
            )
            
            try:
                response = await self.request(page_request)
                responses.append(response)
                
                # Check if we should continue (implementation depends on API)
                if not self._should_continue_pagination(response, page_size):
                    break
                    
                page += 1
                
            except Exception as e:
                logger.error(f"Paginated request failed for page {page}: {e}")
                break
        
        logger.info(f"Paginated requests complete: {len(responses)} pages")
        return responses
    
    def _should_continue_pagination(self, response: APIResponse, expected_size: int) -> bool:
        """
        Determine if pagination should continue based on response.
        This is a simple implementation - override for specific APIs.
        """
        if not response.success:
            return False
        
        # If response data is a list and smaller than expected, we're done
        if isinstance(response.data, list):
            return len(response.data) >= expected_size
        
        # If response data has items field
        if isinstance(response.data, dict) and 'items' in response.data:
            items = response.data['items']
            if isinstance(items, list):
                return len(items) >= expected_size
        
        # Default: continue (let caller handle stop condition)
        return True
    
    def _build_url(self, path: str) -> str:
        """Build full URL from base URL and path."""
        if path.startswith(('http://', 'https://')):
            return path
        
        path = path.lstrip('/')
        if self.base_url:
            return f"{self.base_url}/{path}"
        
        return path
    
    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics."""
        stats = self.stats.copy()
        
        # Calculate additional metrics
        if stats['total_requests'] > 0:
            stats['success_rate'] = (stats['successful_requests'] / stats['total_requests']) * 100
            stats['average_response_time'] = stats['total_response_time'] / stats['total_requests']
        else:
            stats['success_rate'] = 0.0
            stats['average_response_time'] = 0.0
        
        return stats