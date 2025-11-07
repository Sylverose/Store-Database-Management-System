"""
Example usage of the split async API client modules.
"""

import asyncio
from . import (
    AsyncAPIClient, APIRequest, RequestMethod, 
    RetryConfig, RateLimitConfig, APIDataProcessor,
    fetch_json_data
)


async def example_usage():
    """Demonstrate how to use the split API modules."""
    
    print("Testing split async API modules...")
    
    # Configure retry and rate limiting
    retry_config = RetryConfig(
        max_retries=3,
        base_delay=1.0,
        backoff_multiplier=2.0
    )
    
    rate_limit_config = RateLimitConfig(
        requests_per_second=5.0,
        burst_size=10
    )
    
    # Create API client
    async with AsyncAPIClient(
        base_url="https://jsonplaceholder.typicode.com",
        retry_config=retry_config,
        rate_limit_config=rate_limit_config,
        max_concurrent=3
    ) as client:
        
        # Single request
        request = APIRequest(
            url="/posts/1",
            method=RequestMethod.GET
        )
        
        response = await client.request(request)
        print(f"Single request: Status {response.status}, Time: {response.request_time:.2f}s")
        
        # Batch requests
        batch_requests = [
            APIRequest(url=f"/posts/{i}", method=RequestMethod.GET)
            for i in range(1, 6)
        ]
        
        batch_responses = await client.batch_requests(batch_requests)
        print(f"Batch requests: {len(batch_responses)} responses")
        
        # Process responses
        processor = APIDataProcessor()
        
        def extract_title(data):
            """Extract title from post data."""
            if isinstance(data, dict) and 'title' in data:
                return data['title']
            return None
        
        titles = await processor.process_responses(batch_responses, extract_title)
        print(f"Extracted {len(titles)} titles")
        
        # Show statistics
        client_stats = client.get_stats()
        processor_stats = processor.get_stats()
        print(f"Client stats: {client_stats}")
        print(f"Processor stats: {processor_stats}")
    
    # Test convenience function
    print("\nTesting convenience function...")
    urls = [
        "https://jsonplaceholder.typicode.com/posts/1",
        "https://jsonplaceholder.typicode.com/posts/2"
    ]
    
    responses = await fetch_json_data(urls, max_concurrent=2)
    print(f"Convenience function: {len(responses)} responses")


if __name__ == '__main__':
    asyncio.run(example_usage())