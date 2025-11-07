"""
Retry handling and configuration for API requests.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class RetryConfig:
    """Configuration for retry mechanisms."""
    
    max_retries: int = 3
    base_delay: float = 1.0  # Base delay in seconds
    max_delay: float = 60.0  # Maximum delay in seconds
    backoff_multiplier: float = 2.0  # Exponential backoff multiplier
    retry_on_status: List[int] = field(default_factory=lambda: [429, 500, 502, 503, 504])
    
    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for retry attempt with exponential backoff."""
        delay = self.base_delay * (self.backoff_multiplier ** attempt)
        return min(delay, self.max_delay)