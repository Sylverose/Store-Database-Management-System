"""
Standalone database connection manager - no external utility dependencies.
"""

import logging
from contextlib import contextmanager
from typing import Dict, Optional
import threading

logger = logging.getLogger(__name__)

# Try to import database dependencies directly
try:
    import mysql.connector
    import mysql.connector.pooling as pooling
    MYSQL_AVAILABLE = True
    POOLING_AVAILABLE = True
except ImportError:
    mysql = None
    pooling = None
    MYSQL_AVAILABLE = False
    POOLING_AVAILABLE = False

try:
    from connect import mysql_connection, config as default_config, connect_to_mysql
    CONNECT_AVAILABLE = True
except ImportError:
    CONNECT_AVAILABLE = False
    default_config = {'user': 'root', 'password': '', 'host': '127.0.0.1', 'database': 'store_manager'}

class ConnectionPool:
    """Thread-safe MySQL connection pool."""
    
    def __init__(self, config, pool_size=5):
        self.config = config.copy()
        self.pool_size = pool_size
        self._pool = []
        self._used = set()
        self._lock = threading.Lock()
        
        # Get database dependencies directly
        self.mysql = mysql.connector if MYSQL_AVAILABLE else None
        self.pooling = pooling if POOLING_AVAILABLE else None
        self.connect_fn = connect_to_mysql if CONNECT_AVAILABLE else None
        
        # Initialize pool
        self._init_pool()
    
    def _init_pool(self):
        """Initialize connection pool."""
        try:
            if self.pooling and self.connect_fn:
                # Use native pooling if available
                self._native_pool = self.pooling.MySQLConnectionPool(
                    pool_name="etl_pool", pool_size=self.pool_size,
                    pool_reset_session=True, **self._clean_config()
                )
                self._pool_type = 'native'
                logger.info(f"Native pool initialized: {self.pool_size} connections")
            else:
                self._pool_type = 'manual'
                self._create_manual_pool()
        except Exception as e:
            logger.warning(f"Pool init failed: {e}, using manual pool")
            self._pool_type = 'manual'
            self._create_manual_pool()
    
    def _clean_config(self):
        """Remove problematic config keys."""
        config = self.config.copy()
        config.pop('raise_on_warnings', None)
        return config
    
    def _create_manual_pool(self):
        """Create manual connection pool."""
        with self._lock:
            for _ in range(self.pool_size):
                conn = self._create_connection()
                if conn:
                    self._pool.append(conn)
            logger.info(f"Manual pool: {len(self._pool)} connections")
    
    def _create_connection(self):
        """Create a new database connection."""
        try:
            if self.connect_fn:
                return self.connect_fn(self.config)
            return self.mysql.connect(**self.config)
        except Exception as e:
            logger.error(f"Connection creation failed: {e}")
            return None
    
    @contextmanager
    def get_connection(self):
        """Get connection from pool with automatic cleanup."""
        conn = None
        try:
            conn = self._acquire()
            yield conn
        finally:
            if conn:
                self._release(conn)
    
    def _acquire(self):
        """Acquire connection from pool."""
        if self._pool_type == 'native':
            try:
                return self._native_pool.get_connection()
            except Exception as e:
                logger.error(f"Native pool acquire failed: {e}")
                return None
        
        # Manual pool
        with self._lock:
            if self._pool:
                conn = self._pool.pop()
                self._used.add(conn)
                return self._test_connection(conn)
            return self._create_connection()
    
    def _test_connection(self, conn):
        """Test and repair connection if needed."""
        try:
            if hasattr(conn, 'is_connected') and not conn.is_connected():
                conn.reconnect()
            elif hasattr(conn, 'ping'):
                conn.ping(reconnect=True)
            return conn
        except Exception as e:
            logger.warning(f"Connection test failed: {e}")
            self._used.discard(conn)
            return self._create_connection()
    
    def _release(self, conn):
        """Release connection back to pool."""
        if not conn or self._pool_type == 'native':
            return
        
        with self._lock:
            self._used.discard(conn)
            if len(self._pool) < self.pool_size:
                try:
                    if hasattr(conn, 'is_connected') and conn.is_connected():
                        self._pool.append(conn)
                    else:
                        self._safe_close(conn)
                except:
                    self._safe_close(conn)
            else:
                self._safe_close(conn)
    
    def _safe_close(self, conn):
        """Safely close connection."""
        try:
            if conn:
                conn.close()
        except:
            pass
    
    def close_all(self):
        """Close all pool connections."""
        with self._lock:
            for conn in self._pool + list(self._used):
                self._safe_close(conn)
            self._pool.clear()
            self._used.clear()
    
    def get_stats(self):
        """Get pool statistics."""
        with self._lock:
            return {
                'type': self._pool_type,
                'size': self.pool_size,
                'available': len(self._pool),
                'used': len(self._used)
            }


class DatabaseConnection:
    """Enhanced database connection manager with pooling."""
    
    _pool = None
    _pool_lock = threading.Lock()
    
    def __init__(self, config: Dict = None, enable_pooling=True, pool_size=5):
        self.config = config or self._get_default_config()
        self.connection_attempts = 0
        self.enable_pooling = enable_pooling
        
        # Initialize singleton pool
        if enable_pooling and not DatabaseConnection._pool:
            with DatabaseConnection._pool_lock:
                if not DatabaseConnection._pool:
                    DatabaseConnection._pool = ConnectionPool(self.config, pool_size)
    
    def _get_default_config(self) -> Dict:
        """Get default configuration."""
        return default_config
    
    @contextmanager
    def get_connection(self):
        """Get database connection (pooled or direct)."""
        if self.enable_pooling and DatabaseConnection._pool:
            with DatabaseConnection._pool.get_connection() as conn:
                if conn:
                    self.connection_attempts += 1
                yield conn
        else:
            with self._direct_connection() as conn:
                yield conn
    
    @contextmanager
    def _direct_connection(self):
        """Get direct connection without pooling."""
        conn = None
        try:
            if CONNECT_AVAILABLE:
                # Use connect module's context manager
                with mysql_connection(self.config) as conn:
                    if conn:
                        self.connection_attempts += 1
                    yield conn
            else:
                # Direct mysql connection
                conn = mysql.connector.connect(**self.config) if MYSQL_AVAILABLE else None
                if conn:
                    self.connection_attempts += 1
                yield conn
        except Exception as e:
            logger.error(f"Direct connection error: {e}")
            yield None
        finally:
            if conn and not CONNECT_AVAILABLE:
                self._safe_close(conn)
    
    @contextmanager
    def get_connection_without_db(self, config: Dict):
        """Get connection without database for DB creation."""
        conn = None
        try:
            if CONNECT_AVAILABLE:
                with mysql_connection(config) as conn:
                    yield conn
            else:
                conn = mysql.connector.connect(**config) if MYSQL_AVAILABLE else None
                yield conn
        except Exception as e:
            logger.error(f"DB-less connection error: {e}")
            yield None
        finally:
            if conn and not CONNECT_AVAILABLE:
                self._safe_close(conn)
    
    def create_database_if_not_exists(self, database_name: str = None) -> bool:
        """Create database if it doesn't exist."""
        try:
            db_name = database_name or self.config.get('database', 'store_manager')
            temp_config = self.config.copy()
            temp_config.pop('database', None)
            
            with self.get_connection_without_db(temp_config) as conn:
                if not conn:
                    return False
                
                cursor = conn.cursor()
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
                cursor.execute(f"USE {db_name}")
                conn.commit()
                logger.info(f"Database '{db_name}' ready")
                return True
                
        except Exception as e:
            logger.error(f"Database creation error: {e}")
            return False
    
    def test_connection(self) -> bool:
        """Test database connection."""
        if CONNECT_AVAILABLE:
            conn = connect_to_mysql(self.config, attempts=1)
            if conn:
                self._safe_close(conn)
                return True
            return False
        
        # Fallback test
        with self.get_connection() as conn:
            return conn is not None
    
    def get_connection_stats(self) -> Dict:
        """Get connection statistics."""
        stats = {
            'attempts': self.connection_attempts,
            'pooling_enabled': self.enable_pooling,
        }
        
        if self.enable_pooling and DatabaseConnection._pool:
            stats.update(DatabaseConnection._pool.get_stats())
        
        return stats
    
    def get_config_summary(self) -> Dict:
        """Get sanitized config summary."""
        summary = self.config.copy()
        if 'password' in summary:
            password = summary['password']
            summary['password'] = '*' * len(password) if password else 'empty'
        return summary
    
    def _safe_close(self, conn):
        """Safely close connection."""
        try:
            if conn:
                conn.close()
        except:
            pass
    
    @classmethod
    def close_pool(cls):
        """Close connection pool."""
        with cls._pool_lock:
            if cls._pool:
                cls._pool.close_all()
                cls._pool = None
                logger.info("Connection pool closed")


# Factory function for backward compatibility
def create_connection_manager(config=None, enable_pooling=True, pool_size=5):
    """Create a DatabaseConnection instance."""
    return DatabaseConnection(config, enable_pooling, pool_size)