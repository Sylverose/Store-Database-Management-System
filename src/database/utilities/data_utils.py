"""
Data processing and cleaning utilities.
"""

import math
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class DataUtils:
    """Data processing and cleaning utilities for database operations."""
    
    @staticmethod
    def clean_dataframe(df: pd.DataFrame, null_replacements: Dict = None) -> pd.DataFrame:
        """Clean DataFrame for database compatibility.
        
        Args:
            df: DataFrame to clean
            null_replacements: Dictionary of column: replacement_value for nulls
            
        Returns:
            Cleaned DataFrame
        """
        if df is None or df.empty:
            return df
        
        # Replace NaN values with None for MySQL compatibility
        df = df.replace({np.nan: None})
        
        # Replace inf values with None as well
        df = df.replace([np.inf, -np.inf], None)
        
        # Apply custom null replacements if provided
        if null_replacements:
            for column, replacement in null_replacements.items():
                if column in df.columns:
                    df[column] = df[column].fillna(replacement)
        
        return df
    
    @staticmethod
    def dataframe_to_records(df: pd.DataFrame, table_schema: List[str] = None) -> List[Dict]:
        """Convert DataFrame to clean records for database insertion.
        
        Args:
            df: DataFrame to convert
            table_schema: Optional list of column names to filter by
            
        Returns:
            List of clean record dictionaries
        """
        if df is None or df.empty:
            return []
        
        # Clean the dataframe first
        df = DataUtils.clean_dataframe(df)
        
        # Filter to schema columns if provided
        if table_schema:
            available_columns = [col for col in table_schema if col in df.columns]
            df = df[available_columns]
        
        # Convert to records and ensure no NaN values remain
        records = df.to_dict('records')
        
        # Additional cleanup to ensure no NaN values in the final records
        cleaned_records = []
        for record in records:
            cleaned_record = {}
            for key, value in record.items():
                # Check for NaN values (works for both numpy.nan and math.nan)
                if value is not None and not (isinstance(value, float) and math.isnan(value)):
                    cleaned_record[key] = value
                else:
                    cleaned_record[key] = None
            cleaned_records.append(cleaned_record)
        
        return cleaned_records
    
    @staticmethod
    def validate_records(records: List[Dict], required_fields: List[str] = None) -> Tuple[List[Dict], List[str]]:
        """Validate records and return valid records and error messages.
        
        Args:
            records: List of record dictionaries to validate
            required_fields: Optional list of required field names
            
        Returns:
            Tuple of (valid_records, error_messages)
        """
        valid_records = []
        errors = []
        
        for i, record in enumerate(records):
            if required_fields:
                missing_fields = [field for field in required_fields if field not in record or record[field] is None]
                if missing_fields:
                    errors.append(f"Record {i}: Missing required fields: {missing_fields}")
                    continue
            
            valid_records.append(record)
        
        return valid_records, errors
    
    @staticmethod
    def normalize_column_names(df: pd.DataFrame, naming_convention: str = 'snake_case') -> pd.DataFrame:
        """Normalize DataFrame column names to a consistent format.
        
        Args:
            df: DataFrame to normalize
            naming_convention: 'snake_case', 'camelCase', or 'PascalCase'
            
        Returns:
            DataFrame with normalized column names
        """
        import re
        
        if df is None or df.empty:
            return df
        
        normalized_columns = []
        for col in df.columns:
            if naming_convention == 'snake_case':
                # Convert to snake_case
                normalized = re.sub('([A-Z])', r'_\1', col).lower().strip('_')
                normalized = re.sub(r'[^\w]', '_', normalized)
                normalized = re.sub(r'_+', '_', normalized)
            elif naming_convention == 'camelCase':
                # Convert to camelCase
                words = re.split(r'[^\w]', col)
                normalized = words[0].lower() + ''.join(word.capitalize() for word in words[1:])
            elif naming_convention == 'PascalCase':
                # Convert to PascalCase
                words = re.split(r'[^\w]', col)
                normalized = ''.join(word.capitalize() for word in words)
            else:
                normalized = col
            
            normalized_columns.append(normalized)
        
        df.columns = normalized_columns
        return df
    
    @staticmethod
    def detect_data_types(df: pd.DataFrame) -> Dict[str, str]:
        """Detect appropriate database data types for DataFrame columns.
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            Dictionary mapping column names to suggested SQL data types
        """
        type_mapping = {}
        
        for col in df.columns:
            series = df[col].dropna()
            
            if series.empty:
                type_mapping[col] = 'TEXT'
                continue
            
            # Check if it's numeric
            if pd.api.types.is_numeric_dtype(series):
                if pd.api.types.is_integer_dtype(series):
                    max_val = series.max()
                    min_val = series.min()
                    
                    if min_val >= -128 and max_val <= 127:
                        type_mapping[col] = 'TINYINT'
                    elif min_val >= -32768 and max_val <= 32767:
                        type_mapping[col] = 'SMALLINT'
                    elif min_val >= -2147483648 and max_val <= 2147483647:
                        type_mapping[col] = 'INT'
                    else:
                        type_mapping[col] = 'BIGINT'
                else:
                    type_mapping[col] = 'DECIMAL(10,2)'
            
            # Check if it's datetime
            elif pd.api.types.is_datetime64_any_dtype(series):
                type_mapping[col] = 'DATETIME'
            
            # Check if it's boolean
            elif pd.api.types.is_bool_dtype(series):
                type_mapping[col] = 'BOOLEAN'
            
            # Default to text with appropriate length
            else:
                max_length = series.astype(str).str.len().max()
                if max_length <= 255:
                    type_mapping[col] = f'VARCHAR({min(max_length * 2, 255)})'
                else:
                    type_mapping[col] = 'TEXT'
        
        return type_mapping
    
    @staticmethod
    def split_dataframe_chunks(df: pd.DataFrame, chunk_size: int = 1000) -> List[pd.DataFrame]:
        """Split DataFrame into smaller chunks for processing.
        
        Args:
            df: DataFrame to split
            chunk_size: Size of each chunk
            
        Returns:
            List of DataFrame chunks
        """
        if df is None or df.empty:
            return []
        
        chunks = []
        for i in range(0, len(df), chunk_size):
            chunks.append(df.iloc[i:i + chunk_size].copy())
        
        return chunks
    
    @staticmethod
    def merge_dataframes_safe(dfs: List[pd.DataFrame], how: str = 'outer') -> pd.DataFrame:
        """Safely merge multiple DataFrames with error handling.
        
        Args:
            dfs: List of DataFrames to merge
            how: Type of merge ('outer', 'inner', 'left', 'right')
            
        Returns:
            Merged DataFrame or empty DataFrame if error
        """
        try:
            if not dfs:
                return pd.DataFrame()
            
            if len(dfs) == 1:
                return dfs[0].copy()
            
            result = dfs[0].copy()
            for df in dfs[1:]:
                # Find common columns for merging
                common_cols = list(set(result.columns) & set(df.columns))
                if common_cols:
                    result = pd.merge(result, df, on=common_cols, how=how, suffixes=('', '_dup'))
                else:
                    # If no common columns, concatenate
                    result = pd.concat([result, df], ignore_index=True, sort=False)
            
            return result
        
        except Exception as e:
            logger.error(f"Error merging DataFrames: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def remove_duplicate_records(records: List[Dict], key_fields: List[str] = None) -> List[Dict]:
        """Remove duplicate records based on key fields.
        
        Args:
            records: List of record dictionaries
            key_fields: Fields to use for duplicate detection (all fields if None)
            
        Returns:
            List of unique records
        """
        if not records:
            return records
        
        seen = set()
        unique_records = []
        
        for record in records:
            # Create key for duplicate detection
            if key_fields:
                key = tuple(record.get(field) for field in key_fields)
            else:
                key = tuple(sorted(record.items()))
            
            if key not in seen:
                seen.add(key)
                unique_records.append(record)
        
        return unique_records