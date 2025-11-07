"""
API response data processing for ETL pipelines.
"""

import logging
from typing import List, Any, Callable, Dict

from .api_models import APIResponse

logger = logging.getLogger(__name__)


class APIDataProcessor:
    """Processor for handling API response data in ETL pipelines."""
    
    def __init__(self):
        """Initialize API data processor."""
        self.processed_count = 0
        self.error_count = 0
    
    async def process_responses(self,
                              responses: List[APIResponse],
                              processor_func: Callable[[Any], Any],
                              batch_size: int = 100) -> List[Any]:
        """
        Process API responses with custom processing function.
        
        Args:
            responses: List of API responses
            processor_func: Function to process each response
            batch_size: Batch size for processing
            
        Returns:
            List of processed data
        """
        logger.info(f"Processing {len(responses)} API responses in batches of {batch_size}")
        
        processed_data = []
        
        for i in range(0, len(responses), batch_size):
            batch = responses[i:i + batch_size]
            batch_results = []
            
            for response in batch:
                try:
                    if response.success:
                        result = processor_func(response.data)
                        batch_results.append(result)
                        self.processed_count += 1
                    else:
                        logger.warning(f"Skipping failed response: {response.status}")
                        self.error_count += 1
                        
                except Exception as e:
                    logger.error(f"Error processing response: {e}")
                    self.error_count += 1
            
            processed_data.extend(batch_results)
            
            if (i + batch_size) % 1000 == 0:  # Log progress every 1000 items
                logger.debug(f"Processed {i + batch_size}/{len(responses)} responses")
        
        logger.info(f"Response processing complete: {self.processed_count} processed, {self.error_count} errors")
        return processed_data
    
    def get_stats(self) -> Dict[str, int]:
        """Get processing statistics."""
        return {
            'processed_count': self.processed_count,
            'error_count': self.error_count
        }