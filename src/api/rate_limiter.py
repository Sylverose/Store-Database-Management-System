"""
Rate limiting functionality for API requests.
"""

import asyncio
import time
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    
    requests_per_second: float = 10.0
    requests_per_minute: int = 600
    burst_size: int = 50  # Maximum burst requests
    
    @property
    def request_interval(self) -> float:
        """Minimum interval between requests in seconds."""
        return 1.0 / self.requests_per_second


class RateLimiter:
    """Token bucket rate limiter for API requests."""
    
    def __init__(self, config: RateLimitConfig):
        """
        Initialize rate limiter.
        
        Args:
            config: Rate limiting configuration
        """
        self.config = config
        self.tokens = float(config.burst_size)
        self.last_update = time.time()
        self.lock = asyncio.Lock()
    
    async def acquire(self, tokens_needed: int = 1) -> float:
        """
        Acquire tokens for rate limiting.
        
        Args:
            tokens_needed: Number of tokens needed
            
        Returns:
            Wait time in seconds (0 if no wait needed)
        """
        async with self.lock:
            now = time.time()
            
            # Add tokens based on time elapsed
            time_elapsed = now - self.last_update
            tokens_to_add = time_elapsed * self.config.requests_per_second
            self.tokens = min(self.config.burst_size, self.tokens + tokens_to_add)
            self.last_update = now
            
            if self.tokens >= tokens_needed:
                self.tokens -= tokens_needed
                return 0.0
            else:
                # Calculate wait time
                tokens_deficit = tokens_needed - self.tokens
                wait_time = tokens_deficit / self.config.requests_per_second
                return wait_time