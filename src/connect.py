"""MySQL connection module with retry mechanism and context manager."""

import logging
import os
import time
from contextlib import contextmanager

try:
    import mysql.connector
    MYSQL_CONNECTOR_AVAILABLE = True
except ImportError:
    MYSQL_CONNECTOR_AVAILABLE = False

try:
    import pymysql
    PYMYSQL_AVAILABLE = True
except ImportError:
    PYMYSQL_AVAILABLE = False

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import structured configuration
try:
    from config import get_config
    _etl_config = get_config()
    config = _etl_config.database.to_dict()
except ImportError:
    # Fallback to environment variables if config module not available
    config = {
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', ''),
        'host': os.getenv('DB_HOST', '127.0.0.1'),
        'database': os.getenv('DB_NAME', 'store_manager'),
        'port': int(os.getenv('DB_PORT', '3306'))
    }
    
    # Add mysql-connector specific settings if using that driver
    if MYSQL_CONNECTOR_AVAILABLE:
        config['raise_on_warnings'] = True

# Set up minimal logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)
handler = logging.StreamHandler()
logger.addHandler(handler)

def connect_to_mysql(config, attempts=3, delay=2):
    """
    Establish a connection to MySQL with retry mechanism.
    Uses PyMySQL as primary driver, falls back to mysql-connector-python.

    Args:
        config (dict): MySQL connection configuration
        attempts (int, optional): Number of connection attempts. Defaults to 3.
        delay (int, optional): Base delay between attempts in seconds. Defaults to 2.

    Returns:
        MySQL connection object if successful, None otherwise
    """
    attempt = 1
    last_error = None
    
    while attempt < attempts + 1:
        try:
            # Try PyMySQL first (more stable with Python 3.13)
            if PYMYSQL_AVAILABLE:
                # Create PyMySQL compatible config
                pymysql_config = config.copy()
                pymysql_config.pop('raise_on_warnings', None)  # Not supported by PyMySQL
                return pymysql.connect(**pymysql_config)
            
            # Fall back to mysql-connector-python
            elif MYSQL_CONNECTOR_AVAILABLE:
                return mysql.connector.connect(**config)
            
            else:
                logger.error("No MySQL driver available. Install pymysql or mysql-connector-python")
                return None
                
        except Exception as err:
            last_error = err
            if attempts == attempt:
                logger.error("Failed to connect: %s", err)
                return None
            logger.warning("Connection failed: %s. Retrying (%d/%d)...", err, attempt, attempts)
            # Progressive reconnect delay
            time.sleep(delay * attempt)
            attempt += 1
    return None

@contextmanager
def mysql_connection(config, attempts=3, delay=2):
    """
    Context manager for MySQL database connections.

    Args:
        config (dict): MySQL connection configuration
        attempts (int, optional): Number of connection attempts. Defaults to 3.
        delay (int, optional): Base delay between attempts in seconds. Defaults to 2.

    Yields:
        MySQLConnection: MySQL connection object if successful, None otherwise
    """
    conn = connect_to_mysql(config, attempts, delay)
    try:
        yield conn
    finally:
        if conn is not None:
            conn.close()
            