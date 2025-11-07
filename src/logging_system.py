"""
Structured logging system for ETL operations.
Provides centralized logging with correlation IDs, performance metrics, and configurable outputs.
"""

import logging
import logging.handlers
import os
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Union
import json
import threading
from contextlib import contextmanager


class CorrelationFilter(logging.Filter):
    """Add correlation ID to log records for request tracking."""
    
    def __init__(self):
        super().__init__()
        self._local = threading.local()
    
    def set_correlation_id(self, correlation_id: str):
        """Set correlation ID for current thread."""
        self._local.correlation_id = correlation_id
    
    def get_correlation_id(self) -> str:
        """Get correlation ID for current thread."""
        return getattr(self._local, 'correlation_id', 'no-correlation')
    
    def filter(self, record):
        """Add correlation ID to log record."""
        record.correlation_id = self.get_correlation_id()
        return True


class PerformanceFilter(logging.Filter):
    """Add performance metrics to log records."""
    
    def __init__(self):
        super().__init__()
        self._local = threading.local()
    
    def start_timer(self, operation: str):
        """Start timing an operation."""
        if not hasattr(self._local, 'timers'):
            self._local.timers = {}
        self._local.timers[operation] = time.time()
    
    def end_timer(self, operation: str) -> float:
        """End timing an operation and return duration."""
        if not hasattr(self._local, 'timers') or operation not in self._local.timers:
            return 0.0
        duration = time.time() - self._local.timers[operation]
        del self._local.timers[operation]
        return duration
    
    def filter(self, record):
        """Add performance context to log record."""
        record.process_id = os.getpid()
        record.thread_id = threading.get_ident()
        return True


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record):
        """Format log record as JSON."""
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'correlation_id': getattr(record, 'correlation_id', 'no-correlation'),
            'process_id': getattr(record, 'process_id', os.getpid()),
            'thread_id': getattr(record, 'thread_id', threading.get_ident()),
        }
        
        # Add exception information if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields from record
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                          'filename', 'module', 'lineno', 'funcName', 'created', 'msecs',
                          'relativeCreated', 'thread', 'threadName', 'processName',
                          'process', 'getMessage', 'exc_info', 'exc_text', 'stack_info']:
                if key not in log_entry:  # Don't override existing fields
                    log_entry[key] = value
        
        return json.dumps(log_entry)


class ETLFormatter(logging.Formatter):
    """Enhanced formatter for ETL operations with correlation IDs and performance metrics."""
    
    def __init__(self):
        super().__init__(
            fmt='%(asctime)s | %(levelname)-8s | %(correlation_id)s | %(name)-20s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    def format(self, record):
        """Format log record with ETL-specific information."""
        # Ensure correlation_id exists
        if not hasattr(record, 'correlation_id'):
            record.correlation_id = 'no-correlation'
        
        # Truncate correlation ID for readability
        if len(record.correlation_id) > 8:
            record.correlation_id = record.correlation_id[:8]
        
        return super().format(record)


class LoggerManager:
    """Centralized logger management for ETL operations."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern for logger manager."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize logger manager."""
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self.correlation_filter = CorrelationFilter()
        self.performance_filter = PerformanceFilter()
        self._loggers = {}
        self._log_dir = Path('logs')
        self._log_dir.mkdir(exist_ok=True)
        
        # Configure root logger
        self._setup_root_logger()
    
    def _setup_root_logger(self):
        """Setup root logger configuration."""
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Add console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(ETLFormatter())
        console_handler.addFilter(self.correlation_filter)
        console_handler.addFilter(self.performance_filter)
        root_logger.addHandler(console_handler)
        
        # Add main log file handler
        main_file_handler = logging.handlers.RotatingFileHandler(
            self._log_dir / 'etl_main.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        main_file_handler.setLevel(logging.DEBUG)
        main_file_handler.setFormatter(ETLFormatter())
        main_file_handler.addFilter(self.correlation_filter)
        main_file_handler.addFilter(self.performance_filter)
        root_logger.addHandler(main_file_handler)
        
        # Add JSON log file handler for structured logging
        json_file_handler = logging.handlers.RotatingFileHandler(
            self._log_dir / 'etl_structured.json',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        json_file_handler.setLevel(logging.INFO)
        json_file_handler.setFormatter(JSONFormatter())
        json_file_handler.addFilter(self.correlation_filter)
        json_file_handler.addFilter(self.performance_filter)
        root_logger.addHandler(json_file_handler)
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get or create a logger with the specified name."""
        if name not in self._loggers:
            logger = logging.getLogger(name)
            
            # Add component-specific file handler if needed
            if '.' in name:  # Component logger (e.g., 'etl.database', 'etl.api')
                component = name.split('.')[1]
                component_file_handler = logging.handlers.RotatingFileHandler(
                    self._log_dir / f'etl_{component}.log',
                    maxBytes=5*1024*1024,  # 5MB
                    backupCount=3
                )
                component_file_handler.setLevel(logging.DEBUG)
                component_file_handler.setFormatter(ETLFormatter())
                component_file_handler.addFilter(self.correlation_filter)
                component_file_handler.addFilter(self.performance_filter)
                logger.addHandler(component_file_handler)
            
            self._loggers[name] = logger
        
        return self._loggers[name]
    
    @contextmanager
    def correlation_context(self, correlation_id: str = None):
        """Context manager for correlation ID."""
        if correlation_id is None:
            correlation_id = str(uuid.uuid4())
        
        old_id = self.correlation_filter.get_correlation_id()
        self.correlation_filter.set_correlation_id(correlation_id)
        try:
            yield correlation_id
        finally:
            self.correlation_filter.set_correlation_id(old_id)
    
    @contextmanager
    def performance_context(self, operation: str, logger: logging.Logger = None):
        """Context manager for performance measurement."""
        if logger is None:
            logger = self.get_logger('etl.performance')
        
        self.performance_filter.start_timer(operation)
        start_time = time.time()
        
        logger.info(f"Starting operation: {operation}")
        try:
            yield
            duration = self.performance_filter.end_timer(operation)
            logger.info(f"Completed operation: {operation}", extra={
                'operation': operation,
                'duration_seconds': duration,
                'status': 'success'
            })
        except Exception as e:
            duration = self.performance_filter.end_timer(operation)
            logger.error(f"Failed operation: {operation}", extra={
                'operation': operation,
                'duration_seconds': duration,
                'status': 'error',
                'error': str(e)
            }, exc_info=True)
            raise
    
    def configure_from_config(self, logging_config: Dict[str, Any]):
        """Configure logging from configuration dictionary."""
        # Set log levels
        if 'level' in logging_config:
            level = getattr(logging, logging_config['level'].upper(), logging.INFO)
            logging.getLogger().setLevel(level)
        
        # Configure console logging
        if 'console' in logging_config:
            console_config = logging_config['console']
            for handler in logging.getLogger().handlers:
                if isinstance(handler, logging.StreamHandler) and handler.stream == sys.stdout:
                    if 'enabled' in console_config and not console_config['enabled']:
                        logging.getLogger().removeHandler(handler)
                    elif 'level' in console_config:
                        handler.setLevel(getattr(logging, console_config['level'].upper(), logging.INFO))
        
        # Configure file logging
        if 'file' in logging_config:
            file_config = logging_config['file']
            if 'directory' in file_config:
                self._log_dir = Path(file_config['directory'])
                self._log_dir.mkdir(exist_ok=True)
                # Re-setup root logger with new directory
                self._setup_root_logger()


# Global logger manager instance
_logger_manager = LoggerManager()


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name."""
    return _logger_manager.get_logger(name)


def configure_logging(logging_config: Dict[str, Any]):
    """Configure logging from configuration dictionary."""
    _logger_manager.configure_from_config(logging_config)


@contextmanager
def correlation_context(correlation_id: str = None):
    """Context manager for correlation ID."""
    with _logger_manager.correlation_context(correlation_id) as cid:
        yield cid


@contextmanager
def performance_context(operation: str, logger: logging.Logger = None):
    """Context manager for performance measurement."""
    with _logger_manager.performance_context(operation, logger):
        yield


# Convenience functions for common loggers
def get_database_logger() -> logging.Logger:
    """Get logger for database operations."""
    return get_logger('etl.database')


def get_api_logger() -> logging.Logger:
    """Get logger for API operations."""
    return get_logger('etl.api')


def get_processing_logger() -> logging.Logger:
    """Get logger for data processing operations."""
    return get_logger('etl.processing')


def get_validation_logger() -> logging.Logger:
    """Get logger for data validation operations."""
    return get_logger('etl.validation')


if __name__ == '__main__':
    # Example usage
    logger = get_logger('etl.example')
    
    with correlation_context() as correlation_id:
        logger.info(f"Starting example with correlation ID: {correlation_id}")
        
        with performance_context('example_operation', logger):
            logger.info("Performing some work...")
            time.sleep(1)  # Simulate work
            logger.info("Work completed")
        
        logger.info("Example finished")