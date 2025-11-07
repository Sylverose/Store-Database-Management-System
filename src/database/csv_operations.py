"""
CSV import operations for database manager.
Extracted from db_manager for better modularity.
"""

import logging
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from .utilities import DataUtils, safe_operation
from .batch_operations import BatchProcessor

logger = logging.getLogger(__name__)


class CSVImporter:
    """Handle CSV file import operations."""
    
    def __init__(self, connection_manager, data_dir: Path, table_columns: Dict[str, List[str]], 
                 pandas_optimizer=None, batch_size: int = 1000):
        """Initialize CSV importer.
        
        Args:
            connection_manager: Database connection manager
            data_dir: Path to data directory containing CSV files
            table_columns: Mapping of table names to column lists
            pandas_optimizer: Optional pandas optimizer for efficient reading
            batch_size: Batch size for database operations
        """
        self.connection_manager = connection_manager
        self.data_dir = data_dir
        self.table_columns = table_columns
        self.pandas_optimizer = pandas_optimizer
        self.batch_processor = BatchProcessor(connection_manager, batch_size=batch_size)
        self.logger = logger
    
    def discover_csv_files(self, schema_definitions: Dict[str, str]) -> Dict[str, str]:
        """Discover available CSV files based on schema definitions.
        
        Args:
            schema_definitions: Schema definition dictionary
            
        Returns:
            Dictionary mapping table names to CSV filenames
        """
        csv_files = {}
        csv_dir = self.data_dir / 'CSV'
        
        if not csv_dir.exists():
            self.logger.warning(f"CSV directory not found: {csv_dir}")
            return csv_files
        
        for table_name in schema_definitions.keys():
            csv_file = f"{table_name}.csv"
            csv_path = csv_dir / csv_file
            
            if csv_path.exists():
                csv_files[table_name] = csv_file
                self.logger.debug(f"Found CSV file for {table_name}: {csv_file}")
            else:
                self.logger.debug(f"No CSV file found for {table_name}")
        
        return csv_files
    
    def import_all_csv_data(self, csv_files: Dict[str, str], 
                           import_order: Optional[List[str]] = None,
                           progress_callback: Optional[Callable] = None) -> bool:
        """Import all CSV data with proper ordering for foreign key constraints.
        
        Args:
            csv_files: Dictionary mapping table names to CSV filenames
            import_order: Optional custom import order (respects foreign keys)
            progress_callback: Optional progress callback function
            
        Returns:
            True if all imports successful, False otherwise
        """
        # Default import order respecting foreign key constraints
        default_order = ['brands', 'categories', 'stores', 'staffs', 'products', 'stocks', 
                        'customers', 'orders', 'order_items']
        
        order = import_order or default_order
        
        with safe_operation("CSV import all", self.logger):
            total_records = 0
            successful_imports = 0
            
            for table_name in order:
                if table_name not in csv_files:
                    self.logger.debug(f"Skipping {table_name} - no CSV file available")
                    continue
                
                try:
                    records_imported = self.import_csv_file(
                        table_name, 
                        csv_files[table_name], 
                        progress_callback
                    )
                    
                    if records_imported > 0:
                        total_records += records_imported
                        successful_imports += 1
                        self.logger.info(f"✅ {table_name}: {records_imported} records imported")
                    else:
                        self.logger.warning(f"⚠️ {table_name}: No records imported")
                
                except Exception as e:
                    self.logger.error(f"❌ {table_name}: Import failed - {e}")
                    # Continue with other tables rather than failing completely
            
            self.logger.info(f"CSV import complete: {successful_imports} tables, {total_records} total records")
            return successful_imports > 0
    
    def import_csv_file(self, table_name: str, csv_filename: str, 
                       progress_callback: Optional[Callable] = None) -> int:
        """Import a single CSV file into specified table.
        
        Args:
            table_name: Target database table name
            csv_filename: CSV filename to import
            progress_callback: Optional progress callback function
            
        Returns:
            Number of records imported
        """
        csv_path = self.data_dir / 'CSV' / csv_filename
        
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        
        with safe_operation(f"CSV import {table_name}", self.logger):
            # Read CSV with optimization
            df = self._read_csv_optimized(csv_path)
            if df is None or df.empty:
                self.logger.warning(f"No data found in {csv_filename}")
                return 0
            
            df = DataUtils.clean_dataframe(df)
            schema = self.table_columns.get(table_name, [])
            records = DataUtils.dataframe_to_records(df, schema)
            
            if not records:
                self.logger.warning(f"No valid records found in {csv_filename}")
                return 0
            
            inserted, failed = self.batch_processor.insert_batch(
                table_name, 
                records, 
                progress_callback=progress_callback,
                ignore_duplicates=True
            )
            
            if failed > 0:
                self.logger.warning(f"{table_name}: {failed} records failed to import")
            
            return inserted
    
    def _read_csv_optimized(self, csv_path: Path) -> Optional[pd.DataFrame]:
        """Read CSV with pandas optimization if available.
        
        Args:
            csv_path: Path to CSV file
            
        Returns:
            DataFrame or None if reading failed
        """
        try:
            # Use pandas optimizer if available
            if self.pandas_optimizer and hasattr(self.pandas_optimizer, 'optimize_csv_reading'):
                return self.pandas_optimizer.optimize_csv_reading(csv_path, auto_optimize=True)
            else:
                return pd.read_csv(csv_path)
                
        except Exception as e:
            self.logger.error(f"Failed to read {csv_path}: {e}")
            return None
    
    def validate_csv_file(self, csv_filename: str, table_schema: List[str]) -> tuple[bool, List[str]]:
        """Validate CSV file structure against table schema.
        
        Args:
            csv_filename: CSV filename to validate
            table_schema: Expected column schema
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        csv_path = self.data_dir / 'CSV' / csv_filename
        
        if not csv_path.exists():
            return False, [f"CSV file not found: {csv_filename}"]
        
        try:
            # Read just the header
            df = pd.read_csv(csv_path, nrows=0)
            csv_columns = list(df.columns)
            
            errors = []
            
            # Check for missing required columns
            missing_columns = [col for col in table_schema if col not in csv_columns]
            if missing_columns:
                errors.append(f"Missing required columns: {missing_columns}")
            
            # Check for unexpected columns
            extra_columns = [col for col in csv_columns if col not in table_schema]
            if extra_columns:
                errors.append(f"Unexpected columns: {extra_columns}")
            
            return len(errors) == 0, errors
            
        except Exception as e:
            return False, [f"Failed to validate CSV structure: {e}"]
    
    def get_csv_info(self, csv_filename: str) -> Dict[str, Any]:
        """Get information about a CSV file.
        
        Args:
            csv_filename: CSV filename to analyze
            
        Returns:
            Dictionary with CSV file information
        """
        csv_path = self.data_dir / 'CSV' / csv_filename
        
        info = {
            'filename': csv_filename,
            'path': str(csv_path),
            'exists': csv_path.exists(),
            'size_bytes': 0,
            'row_count': 0,
            'columns': [],
            'errors': []
        }
        
        if not csv_path.exists():
            info['errors'].append("File not found")
            return info
        
        try:
            # Get file size
            info['size_bytes'] = csv_path.stat().st_size
            
            # Read CSV for analysis
            df = pd.read_csv(csv_path)
            info['row_count'] = len(df)
            info['columns'] = list(df.columns)
            
            # Additional statistics
            info['null_counts'] = df.isnull().sum().to_dict()
            info['data_types'] = df.dtypes.astype(str).to_dict()
            
        except Exception as e:
            info['errors'].append(f"Analysis failed: {e}")
        
        return info
    
    def get_import_statistics(self) -> Dict[str, Any]:
        """Get import statistics from batch processor.
        
        Returns:
            Dictionary with import statistics
        """
        return self.batch_processor.get_stats()
    
    def reset_statistics(self):
        """Reset import statistics."""
        self.batch_processor.reset_stats()