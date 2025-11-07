"""
Compact schema manager - handles table schema definitions and creation using utilities.
"""

import logging
from typing import Dict, List, Optional

# Inline schema definitions
SCHEMA_DEFINITIONS = {
    'brands': "CREATE TABLE IF NOT EXISTS brands (brand_id INT PRIMARY KEY, brand_name VARCHAR(255) NOT NULL) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4",
    'categories': "CREATE TABLE IF NOT EXISTS categories (category_id INT PRIMARY KEY, category_name VARCHAR(255) NOT NULL) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4",
    'stores': """CREATE TABLE IF NOT EXISTS stores (store_id INT PRIMARY KEY AUTO_INCREMENT, name VARCHAR(255) NOT NULL, phone VARCHAR(20), 
                 email VARCHAR(255), street VARCHAR(255), city VARCHAR(100), state VARCHAR(50), zip_code VARCHAR(20)) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
    'staffs': """CREATE TABLE IF NOT EXISTS staffs (staff_id INT PRIMARY KEY AUTO_INCREMENT, name VARCHAR(100) NOT NULL, last_name VARCHAR(100) NOT NULL, 
                 email VARCHAR(255), phone VARCHAR(20), active BOOLEAN DEFAULT TRUE, store_name VARCHAR(255), street VARCHAR(255), manager_id INT, 
                 FOREIGN KEY (manager_id) REFERENCES staffs(staff_id)) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
    'products': """CREATE TABLE IF NOT EXISTS products (product_id INT PRIMARY KEY, product_name VARCHAR(255) NOT NULL, brand_id INT, category_id INT, 
                   model_year INT, list_price DECIMAL(10, 2), FOREIGN KEY (brand_id) REFERENCES brands(brand_id), 
                   FOREIGN KEY (category_id) REFERENCES categories(category_id)) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
    'stocks': """CREATE TABLE IF NOT EXISTS stocks (store_name VARCHAR(255), product_id INT, quantity INT DEFAULT 0, PRIMARY KEY (product_id, store_name), 
                 FOREIGN KEY (product_id) REFERENCES products(product_id)) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
    'orders': """CREATE TABLE IF NOT EXISTS orders (order_id INT PRIMARY KEY, customer_id INT NOT NULL, order_status INT NOT NULL, 
                 order_status_name VARCHAR(50), order_date DATE, required_date DATE, shipped_date DATE, staff_name VARCHAR(255), 
                 store VARCHAR(255), INDEX idx_customer_id (customer_id), INDEX idx_order_date (order_date), 
                 INDEX idx_order_status (order_status), INDEX idx_store (store)) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
    'order_items': """CREATE TABLE IF NOT EXISTS order_items (item_id INT PRIMARY KEY, order_id INT NOT NULL, product_id INT NOT NULL, 
                      quantity INT NOT NULL DEFAULT 1, list_price DECIMAL(10, 2) NOT NULL, discount DECIMAL(4, 2) DEFAULT 0.00, 
                      INDEX idx_order_id (order_id), INDEX idx_product_id (product_id)) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
    'customers': """CREATE TABLE IF NOT EXISTS customers (customer_id INT PRIMARY KEY, first_name VARCHAR(100) NOT NULL, last_name VARCHAR(100) NOT NULL, 
                    email VARCHAR(255) UNIQUE, phone VARCHAR(20), street VARCHAR(255), city VARCHAR(100), state VARCHAR(50), zip_code VARCHAR(20), 
                    INDEX idx_email (email), INDEX idx_state (state), INDEX idx_city (city)) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
    'users': """CREATE TABLE IF NOT EXISTS users (user_id INT PRIMARY KEY AUTO_INCREMENT, staff_id INT UNIQUE, username VARCHAR(50) UNIQUE NOT NULL, 
                password_hash VARCHAR(255) NOT NULL, role ENUM('Employee', 'Manager', 'Administrator') NOT NULL DEFAULT 'Employee', 
                last_login DATETIME, created_at DATETIME DEFAULT CURRENT_TIMESTAMP, active BOOLEAN DEFAULT TRUE, 
                failed_login_attempts INT DEFAULT 0, last_failed_login DATETIME, account_locked_until DATETIME, 
                password_last_changed DATETIME DEFAULT CURRENT_TIMESTAMP, must_change_password BOOLEAN DEFAULT FALSE,
                two_factor_enabled BOOLEAN DEFAULT FALSE, two_factor_secret VARCHAR(32), backup_codes TEXT,
                FOREIGN KEY (staff_id) REFERENCES staffs(staff_id) ON DELETE SET NULL, INDEX idx_username (username), 
                INDEX idx_role (role)) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"""
}

TABLE_COLUMNS = {
    'orders': ['order_id', 'customer_id', 'order_status', 'order_status_name', 'order_date', 'required_date', 'shipped_date', 'staff_name', 'store'],
    'order_items': ['item_id', 'order_id', 'product_id', 'quantity', 'list_price', 'discount'],
    'customers': ['customer_id', 'first_name', 'last_name', 'email', 'phone', 'street', 'city', 'state', 'zip_code'],
    'brands': ['brand_id', 'brand_name'],
    'categories': ['category_id', 'category_name'],
    'stores': ['store_id', 'name', 'phone', 'email', 'street', 'city', 'state', 'zip_code'],
    'products': ['product_id', 'product_name', 'brand_id', 'category_id', 'model_year', 'list_price'],
    'staffs': ['staff_id', 'name', 'last_name', 'email', 'phone', 'active', 'store_name', 'street', 'manager_id'],
    'stocks': ['store_name', 'product_id', 'quantity'],
    'users': ['user_id', 'staff_id', 'username', 'password_hash', 'role', 'last_login', 'created_at', 'active', 
              'failed_login_attempts', 'last_failed_login', 'account_locked_until', 'password_last_changed', 
              'must_change_password', 'two_factor_enabled', 'two_factor_secret', 'backup_codes']
}

logger = logging.getLogger(__name__)

class SchemaManager:
    """Manages database table schemas using data-driven definitions."""
    
    def __init__(self, db_connection):
        """Initialize with inline schema definitions."""
        self.db_connection = db_connection
    
    def get_schema(self, table_name: str) -> Optional[str]:
        """Get schema definition for a table."""
        return SCHEMA_DEFINITIONS.get(table_name)
    
    def create_table(self, table_name: str) -> bool:
        """Create a specific table."""
        try:
            schema = self.get_schema(table_name)
            if not schema:
                logger.error(f"No schema defined for: {table_name}")
                return False
            
            with self.db_connection.get_connection() as conn:
                if not conn:
                    logger.error("Database connection failed")
                    return False
                
                cursor = conn.cursor()
                cursor.execute(schema)
                conn.commit()
                logger.info(f"Table '{table_name}' created")
                return True
                
        except Exception as e:
            logger.error(f"Error creating table {table_name}: {e}")
            return False
    
    def create_all_tables(self, table_order: List[str] = None) -> bool:
        """Create all tables in correct order."""
        order = table_order or ['brands', 'categories', 'stores', 'staffs', 'products', 'stocks', 'orders', 'order_items', 'customers']
        
        success_count = 0
        for table_name in order:
            if self.create_table(table_name):
                success_count += 1
            else:
                logger.warning(f"Failed to create: {table_name}")
        
        logger.info(f"Created {success_count}/{len(order)} tables")
        return success_count == len(order)
    
    def get_table_columns(self, table_name: str) -> List[str]:
        """Get expected columns for validation."""
        return TABLE_COLUMNS.get(table_name, [])
    
    def get_schema(self, table_name: str) -> Optional[str]:
        """
        Get schema definition for a specific table.
        
        Args:
            table_name (str): Name of the table
            
        Returns:
            str: SQL schema definition or None if not found
        """
        return self.table_schemas.get(table_name)
    
    def create_table(self, table_name: str) -> bool:
        """
        Create a specific table in the database.
        
        Args:
            table_name (str): Name of the table to create
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            schema = self.get_schema(table_name)
            if not schema:
                logger.error(f"No schema defined for table: {table_name}")
                return False
            
            with self.db_connection.get_connection() as conn:
                if conn is None:
                    logger.error("Failed to connect to database")
                    return False
                
                cursor = conn.cursor()
                cursor.execute(schema)
                conn.commit()
                
                logger.info(f"Table '{table_name}' created successfully")
                return True
                
        except Exception as e:
            logger.error(f"Error creating table {table_name}: {e}")
            return False
    
    def create_all_tables(self, table_order: List[str] = None) -> bool:
        """
        Create all tables in the correct order (respecting foreign key constraints).
        
        Args:
            table_order (List[str]): Order to create tables. Uses default if None.
            
        Returns:
            bool: True if all tables created successfully
        """
        # Default order respecting foreign key constraints
        order = table_order or ['brands', 'categories', 'stores', 'staffs', 'products', 'stocks', 'orders', 'order_items', 'customers']
        
        success_count = 0
        for table_name in order:
            if self.create_table(table_name):
                success_count += 1
            else:
                logger.warning(f"Failed to create table: {table_name}")
        
        total_tables = len(order)
        logger.info(f"Created {success_count}/{total_tables} tables")
        
        return success_count == total_tables
    
    def get_table_columns(self, table_name: str) -> List[str]:
        """
        Get expected columns for a table (for data validation).
        
        Args:
            table_name (str): Name of the table
            
        Returns:
            List[str]: List of column names
        """
        table_columns = {
            'orders': ['order_id', 'customer_id', 'order_status', 'order_status_name', 
                      'order_date', 'required_date', 'shipped_date', 'staff_name', 'store'],
            'order_items': ['item_id', 'order_id', 'product_id', 'quantity', 'list_price', 'discount'],
            'customers': ['customer_id', 'first_name', 'last_name', 'email', 'phone', 'street', 'city', 'state', 'zip_code'],
            'brands': ['brand_id', 'brand_name'],
            'categories': ['category_id', 'category_name'],
            'stores': ['store_id', 'name', 'phone', 'email', 'street', 'city', 'state', 'zip_code'],
            'products': ['product_id', 'product_name', 'brand_id', 'category_id', 'model_year', 'list_price'],
            'staffs': ['staff_id', 'name', 'last_name', 'email', 'phone', 'active', 'store_name', 'street', 'manager_id'],
            'stocks': ['store_name', 'product_id', 'quantity']
        }
        return table_columns.get(table_name, [])
    
    def get_all_table_names(self) -> List[str]:
        """Get list of all defined table names."""
        return list(SCHEMA_DEFINITIONS.keys())
    
    def table_exists(self, table_name: str) -> bool:
        """Check if table exists in database."""
        try:
            with self.db_connection.get_connection() as conn:
                if not conn:
                    return False
                
                cursor = conn.cursor()
                cursor.execute(f"SHOW TABLES LIKE %s", (table_name,))
                return cursor.fetchone() is not None
                
        except Exception as e:
            logger.error(f"Error checking table existence: {e}")
            return False


# Factory function for backward compatibility
def create_schema_manager(db_connection):
    """Create a SchemaManager instance."""
    return SchemaManager(db_connection)