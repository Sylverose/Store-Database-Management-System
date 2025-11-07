"""
Database migration to add security fields for account lockout
Run this script to add the necessary columns to the users table
"""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from connect import connect_to_mysql
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def add_security_columns():
    """Add security-related columns to users table"""
    
    conn = None
    cursor = None
    
    try:
        conn = connect_to_mysql()
        cursor = conn.cursor()
        
        logger.info("Adding security columns to users table...")
        
        # Add failed_login_attempts column
        try:
            cursor.execute("""
                ALTER TABLE users 
                ADD COLUMN failed_login_attempts INT DEFAULT 0
            """)
            logger.info("✓ Added failed_login_attempts column")
        except Exception as e:
            if "Duplicate column" in str(e):
                logger.info("✓ failed_login_attempts column already exists")
            else:
                raise
        
        # Add locked_until column
        try:
            cursor.execute("""
                ALTER TABLE users 
                ADD COLUMN locked_until DATETIME NULL
            """)
            logger.info("✓ Added locked_until column")
        except Exception as e:
            if "Duplicate column" in str(e):
                logger.info("✓ locked_until column already exists")
            else:
                raise
        
        # Add last_failed_attempt column
        try:
            cursor.execute("""
                ALTER TABLE users 
                ADD COLUMN last_failed_attempt DATETIME NULL
            """)
            logger.info("✓ Added last_failed_attempt column")
        except Exception as e:
            if "Duplicate column" in str(e):
                logger.info("✓ last_failed_attempt column already exists")
            else:
                raise
        
        # Add last_login column (for tracking)
        try:
            cursor.execute("""
                ALTER TABLE users 
                ADD COLUMN last_login DATETIME NULL
            """)
            logger.info("✓ Added last_login column")
        except Exception as e:
            if "Duplicate column" in str(e):
                logger.info("✓ last_login column already exists")
            else:
                raise
        
        conn.commit()
        logger.info("\n✅ Security columns added successfully!")
        
        # Show current table structure
        cursor.execute("DESCRIBE users")
        columns = cursor.fetchall()
        
        logger.info("\nCurrent users table structure:")
        for col in columns:
            logger.info(f"  - {col[0]}: {col[1]}")
        
    except Exception as e:
        logger.error(f"❌ Error adding security columns: {e}")
        if conn:
            conn.rollback()
        raise
    
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Database Migration: Add Security Columns")
    print("=" * 60)
    print()
    
    add_security_columns()
    
    print()
    print("=" * 60)
    print("Migration completed!")
    print("=" * 60)
