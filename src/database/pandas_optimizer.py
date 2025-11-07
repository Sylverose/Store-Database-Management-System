"""
Compact pandas optimization utilities for memory-efficient ETL operations.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Union, Iterator
from pathlib import Path
import logging

# Try to import optional dependencies
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# Inline DataUtils functions
class DataUtils:
    @staticmethod
    def get_dataframe_memory_mb(df):
        try:
            return df.memory_usage(deep=True).sum() / 1024 / 1024
        except:
            return 0.0
    
    @staticmethod
    def should_be_categorical(series, threshold=0.5):
        try:
            unique_ratio = series.nunique() / len(series)
            return unique_ratio < threshold
        except:
            return False
    
    @staticmethod
    def create_stats_tracker():
        return {
            'memory_optimized': 0,
            'chunks_processed': 0,
            'rows_processed': 0,
            'memory_saved_mb': 0.0
        }
    
    @staticmethod
    def update_stats(stats, key, value):
        if key in stats:
            stats[key] += value
        else:
            stats[key] = value
    
    @staticmethod
    def force_cleanup():
        import gc
        gc.collect()

logger = logging.getLogger(__name__)

class PandasOptimizer:
    """Memory-efficient pandas operations with automatic optimization."""
    
    def __init__(self, max_memory_mb=512, chunk_size=10000, auto_optimize=True):
        """Initialize with optimization settings."""
        self.max_memory_mb = max_memory_mb
        self.chunk_size = chunk_size
        self.auto_optimize = auto_optimize
        self.stats = DataUtils.create_stats_tracker()
    
    def get_memory_usage_mb(self) -> float:
        """Get current memory usage in MB."""
        psutil_available = PSUTIL_AVAILABLE
        
        if PSUTIL_AVAILABLE:
            try:
                return psutil.Process().memory_info().rss / 1024 / 1024
            except:
                pass
        
        # Fallback
        try:
            import resource
            return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
        except:
            return 0.0
    
    def optimize_dtypes(self, df: pd.DataFrame, categorical_threshold=0.5) -> pd.DataFrame:
        """Optimize DataFrame data types for memory efficiency."""
        if not self.auto_optimize:
            return df
        
        original_memory = DataUtils.get_dataframe_memory_mb(df)
        optimized_df = df.copy()
        
        for col in optimized_df.columns:
            col_type = optimized_df[col].dtype
            
            # Downcast numeric types
            if col_type in ['int64', 'int32', 'int16', 'int8']:
                optimized_df[col] = pd.to_numeric(optimized_df[col], downcast='integer')
            elif col_type in ['float64', 'float32']:
                optimized_df[col] = pd.to_numeric(optimized_df[col], downcast='float')
            
            # Convert to categorical if beneficial
            elif col_type == 'object':
                if DataUtils.should_be_categorical(optimized_df[col], categorical_threshold):
                    optimized_df[col] = optimized_df[col].astype('category')
        
        optimized_memory = DataUtils.get_dataframe_memory_mb(optimized_df)
        memory_saved = original_memory - optimized_memory
        
        DataUtils.update_stats(self.stats, 'memory_optimized', 1)
        DataUtils.update_stats(self.stats, 'memory_saved_mb', memory_saved)
        
        logger.info(f"Memory: {original_memory:.2f}MB → {optimized_memory:.2f}MB "
                   f"(saved {memory_saved:.2f}MB)")
        
        return optimized_df
    
    def process_in_chunks(self, file_path: Union[str, Path], 
                         processor: callable, **read_kwargs) -> Iterator[Any]:
        """Process large CSV files in memory-efficient chunks."""
        read_params = {
            'chunksize': self.chunk_size,
            'low_memory': True,
            'engine': 'c',
            **read_kwargs
        }
        
        logger.info(f"Processing {file_path} in chunks of {self.chunk_size}")
        
        total_chunks, total_rows = 0, 0
        
        try:
            for chunk_num, chunk in enumerate(pd.read_csv(file_path, **read_params)):
                # Monitor memory
                if self.get_memory_usage_mb() > self.max_memory_mb:
                    logger.warning("Memory limit exceeded, forcing cleanup")
                    DataUtils.force_cleanup()
                
                # Optimize chunk
                if self.auto_optimize:
                    chunk = self.optimize_dtypes(chunk)
                
                result = processor(chunk)
                total_chunks += 1
                total_rows += len(chunk)
                
                yield result
            
            DataUtils.update_stats(self.stats, 'chunks_processed', total_chunks)
            DataUtils.update_stats(self.stats, 'rows_processed', total_rows)
            
            logger.info(f"Processed {total_chunks} chunks, {total_rows} total rows")
            
        except Exception as e:
            logger.error(f"Chunk processing failed: {e}")
            raise
    
    def efficient_groupby(self, df: pd.DataFrame, groupby_cols: List[str],
                         agg_funcs: Dict[str, Union[str, List[str]]], 
                         sort_result=False) -> pd.DataFrame:
        """Memory-efficient groupby operations."""
        original_memory = DataUtils.get_dataframe_memory_mb(df)
        
        # Optimize before groupby
        if self.auto_optimize:
            df = self.optimize_dtypes(df)
        
        # Perform efficient groupby
        result = df.groupby(groupby_cols, sort=sort_result, observed=True).agg(agg_funcs)
        
        if isinstance(result.index, pd.MultiIndex) or len(groupby_cols) == 1:
            result = result.reset_index()
        
        result_memory = DataUtils.get_dataframe_memory_mb(result)
        logger.info(f"Groupby: {len(df)} → {len(result)} rows, "
                   f"{original_memory:.2f}MB → {result_memory:.2f}MB")
        
        return result
    
    def efficient_merge(self, left: pd.DataFrame, right: pd.DataFrame,
                       on: Union[str, List[str]] = None, how='inner',
                       **kwargs) -> pd.DataFrame:
        """Memory-efficient merge operations."""
        left_mem = DataUtils.get_dataframe_memory_mb(left)
        right_mem = DataUtils.get_dataframe_memory_mb(right)
        
        logger.debug(f"Merging: left({len(left)} rows, {left_mem:.2f}MB) "
                    f"{how} right({len(right)} rows, {right_mem:.2f}MB)")
        
        # Optimize before merge
        if self.auto_optimize:
            left = self.optimize_dtypes(left)
            right = self.optimize_dtypes(right)
        
        result = pd.merge(left, right, on=on, how=how, **kwargs)
        result_mem = DataUtils.get_dataframe_memory_mb(result)
        
        logger.info(f"Merge complete: {len(result)} rows, {result_mem:.2f}MB")
        return result
    
    def get_data_profile(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get comprehensive DataFrame analysis."""
        return DataUtils.profile_dataframe(df)
    
    def suggest_optimizations(self, df: pd.DataFrame) -> List[str]:
        """Suggest DataFrame optimizations."""
        suggestions = []
        profile = self.get_data_profile(df)
        
        if profile['memory_usage_mb'] > self.max_memory_mb:
            suggestions.append(f"Memory usage ({profile['memory_usage_mb']:.1f}MB) "
                             f"exceeds limit ({self.max_memory_mb}MB)")
        
        for col in df.columns:
            col_type = df[col].dtype
            unique_count = df[col].nunique()
            total_count = len(df)
            
            if col_type == 'object' and unique_count / total_count < 0.5:
                suggestions.append(f"'{col}' could be categorical "
                                 f"({unique_count}/{total_count} unique)")
            
            if col_type in ['int64', 'float64']:
                suggestions.append(f"'{col}' ({col_type}) could be downcast")
        
        return suggestions
    
    def get_stats(self) -> Dict[str, Any]:
        """Get optimizer performance statistics."""
        return self.stats.copy()


class DataFrameChunker:
    """Utility for processing large DataFrames in chunks."""
    
    def __init__(self, chunk_size=10000):
        self.chunk_size = chunk_size
    
    def chunk_dataframe(self, df: pd.DataFrame) -> Iterator[pd.DataFrame]:
        """Split DataFrame into memory-efficient chunks."""
        total_rows = len(df)
        total_chunks = (total_rows + self.chunk_size - 1) // self.chunk_size
        
        logger.info(f"Chunking: {total_rows} rows → {total_chunks} chunks")
        
        for i in range(0, total_rows, self.chunk_size):
            yield df.iloc[i:i + self.chunk_size]
    
    def process_chunks(self, df: pd.DataFrame, processor: callable,
                      combine_results=True) -> Union[List[Any], pd.DataFrame]:
        """Process DataFrame in chunks with optional result combination."""
        results = [processor(chunk) for chunk in self.chunk_dataframe(df)]
        
        if combine_results and all(isinstance(r, pd.DataFrame) for r in results):
            combined = pd.concat(results, ignore_index=True)
            logger.info(f"Combined {len(results)} chunks → {len(combined)} rows")
            return combined
        
        return results


# Convenience functions
def optimize_csv_reading(file_path: Union[str, Path], chunk_size=10000,
                        auto_optimize=True, **kwargs) -> pd.DataFrame:
    """Optimized CSV reading with automatic dtype optimization."""
    optimizer = PandasOptimizer(chunk_size=chunk_size, auto_optimize=auto_optimize)
    
    try:
        df = pd.read_csv(file_path, **kwargs)
        
        if auto_optimize:
            df = optimizer.optimize_dtypes(df)
        
        logger.info(f"Read and optimized {file_path}: {df.shape}")
        return df
        
    except MemoryError:
        logger.warning("Memory error, using chunked processing")
        chunks = list(optimizer.process_in_chunks(file_path, lambda x: x, **kwargs))
        
        result = pd.concat(chunks, ignore_index=True)
        logger.info(f"Chunked read complete: {result.shape}")
        return result


def get_memory_efficient_dtypes(df: pd.DataFrame) -> Dict[str, str]:
    """Get suggested memory-efficient dtypes for DataFrame columns."""
    return DataUtils.suggest_dtype_optimizations(df)


# Factory function for backward compatibility
def create_pandas_optimizer(max_memory_mb=512, chunk_size=10000, auto_optimize=True):
    """Create a PandasOptimizer instance."""
    return PandasOptimizer(max_memory_mb, chunk_size, auto_optimize)


if __name__ == '__main__':
    # Example usage
    print("Testing compact pandas optimizer...")
    
    # Create test data
    data = {
        'id': range(1000),
        'category': ['A', 'B', 'C'] * 334,
        'value': np.random.randn(1000),
        'score': np.random.randint(0, 100, 1000)
    }
    
    df = pd.DataFrame(data)
    optimizer = PandasOptimizer()
    
    print(f"Original: {df.shape}, {DataUtils.get_dataframe_memory_mb(df):.2f}MB")
    optimized_df = optimizer.optimize_dtypes(df)
    print(f"Optimized: {optimized_df.shape}, {DataUtils.get_dataframe_memory_mb(optimized_df):.2f}MB")
    
    print(f"Stats: {optimizer.get_stats()}")