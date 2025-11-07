"""
API-specific configuration utilities and presets.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from .import APIConfig


@dataclass
class RESTAPIConfig(APIConfig):
    """REST API specific configuration."""
    
    # REST-specific settings
    default_format: str = 'json'
    pagination_limit: int = 100
    max_page_size: int = 1000
    
    # Endpoint configurations
    endpoints: Dict[str, str] = None
    
    def __post_init__(self):
        if self.endpoints is None:
            self.endpoints = {
                'customers': '/api/customers',
                'orders': '/api/orders',
                'order_items': '/api/order_items',
                'products': '/api/products',
                'health': '/health'
            }
    
    def get_endpoint_url(self, endpoint: str) -> str:
        """Get full URL for an endpoint."""
        if endpoint in self.endpoints:
            return f"{self.base_url.rstrip('/')}{self.endpoints[endpoint]}"
        return f"{self.base_url.rstrip('/')}/{endpoint}"


@dataclass 
class GraphQLAPIConfig(APIConfig):
    """GraphQL API specific configuration."""
    
    # GraphQL-specific settings
    endpoint: str = '/graphql'
    introspection_enabled: bool = True
    
    # Query settings
    max_query_depth: int = 10
    query_timeout: int = 30
    
    def get_graphql_url(self) -> str:
        """Get GraphQL endpoint URL."""
        return f"{self.base_url.rstrip('/')}{self.endpoint}"


@dataclass
class AsyncAPIConfig(APIConfig):
    """Async API configuration with advanced concurrency settings."""
    
    # Async-specific settings
    connector_limit: int = 100
    connector_limit_per_host: int = 30
    total_timeout: float = 300.0
    
    # Retry settings for async
    async_retry_attempts: int = 3
    async_backoff_factor: float = 0.1
    async_max_backoff: float = 10.0
    
    # Circuit breaker settings
    enable_circuit_breaker: bool = True
    failure_threshold: int = 5
    recovery_timeout: int = 60
    expected_exception_types: List[str] = None
    
    def __post_init__(self):
        if self.expected_exception_types is None:
            self.expected_exception_types = [
                'aiohttp.ClientError',
                'asyncio.TimeoutError',
                'ConnectionError'
            ]


# Predefined API configurations

def get_etl_server_config() -> RESTAPIConfig:
    """Get configuration for ETL server API."""
    return RESTAPIConfig(
        base_url='https://etl-server.fly.dev',
        timeout=30,
        retries=3,
        pagination_limit=500,
        max_concurrent_requests=10
    )


def get_jsonplaceholder_config() -> RESTAPIConfig:
    """Get configuration for JSONPlaceholder demo API."""
    return RESTAPIConfig(
        base_url='https://jsonplaceholder.typicode.com',
        timeout=15,
        retries=2,
        pagination_limit=100,
        endpoints={
            'posts': '/posts',
            'users': '/users', 
            'comments': '/comments',
            'albums': '/albums',
            'photos': '/photos'
        }
    )


def get_local_dev_config() -> RESTAPIConfig:
    """Get configuration for local development API."""
    return RESTAPIConfig(
        base_url='http://localhost:8000',
        timeout=10,
        retries=1,
        max_concurrent_requests=5,
        rate_limit_calls=1000  # More lenient for local dev
    )


def get_async_production_config() -> AsyncAPIConfig:
    """Get async configuration for production environments."""
    return AsyncAPIConfig(
        max_concurrent_requests=50,
        semaphore_limit=25,
        connector_limit=200,
        connector_limit_per_host=50,
        total_timeout=600.0,
        enable_circuit_breaker=True,
        failure_threshold=10
    )