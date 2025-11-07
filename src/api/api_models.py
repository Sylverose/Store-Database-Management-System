"""
Data models and enums for API operations.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional, Union
from datetime import datetime


class RequestMethod(Enum):
    """HTTP request methods."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"


@dataclass
class APIRequest:
    """API request configuration."""
    
    url: str
    method: RequestMethod = RequestMethod.GET
    headers: Dict[str, str] = field(default_factory=dict)
    params: Dict[str, Any] = field(default_factory=dict)
    data: Optional[Union[Dict, str]] = None
    timeout: float = 30.0
    metadata: Dict[str, Any] = field(default_factory=dict)  # For tracking/context


@dataclass
class APIResponse:
    """API response wrapper."""
    
    status: int
    data: Any
    headers: Dict[str, str]
    url: str
    request_time: float
    response_time: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def success(self) -> bool:
        """Check if request was successful."""
        return 200 <= self.status < 300
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'status': self.status,
            'data': self.data,
            'headers': dict(self.headers),
            'url': self.url,
            'request_time': self.request_time,
            'response_time': self.response_time.isoformat(),
            'success': self.success,
            'metadata': self.metadata
        }