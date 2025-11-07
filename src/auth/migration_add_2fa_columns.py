"""
Migration script to add security and 2FA columns to the users table.
Run this once to update existing databases.
"""

import sys
from pathlib import Path

# Add project paths
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from connect import connect_to_mysql
from config.database import DatabaseConfig
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_users_table():
    """Add security and 2FA columns to existing users table."""
    try:
        # Connect to database
        db_config = DatabaseConfig().to_dict()
        connection = connect_to_mysql(db_config)
        
        if not connection:
            logger.error("Failed to connect to database")
            return False
        
        cursor = connection.cursor()
        
        # List of columns to add
        columns_to_add = [
            ("failed_login_attempts", "INT DEFAULT 0"),
            ("last_failed_login", "DATETIME"),
            ("account_locked_until", "DATETIME"),
            ("password_last_changed", "DATETIME DEFAULT CURRENT_TIMESTAMP"),
            ("must_change_password", "BOOLEAN DEFAULT FALSE"),
            ("two_factor_enabled", "BOOLEAN DEFAULT FALSE"),
            ("two_factor_secret", "VARCHAR(32)"),
            ("backup_codes", "TEXT")
        ]
        
        # Check which columns already exist
        cursor.execute("DESCRIBE users")
        existing_columns = [row[0] for row in cursor.fetchall()]
        
        # Add missing columns
        for column_name, column_definition in columns_to_add:
            if column_name not in existing_columns:
                try:
                    alter_query = f"ALTER TABLE users ADD COLUMN {column_name} {column_definition}"
                    cursor.execute(alter_query)
                    connection.commit()
                    logger.info(f"✅ Added column: {column_name}")
                except Exception as e:
                    logger.error(f"❌ Failed to add column {column_name}: {e}")
            else:
                logger.info(f"⏭️  Column already exists: {column_name}")
        
        cursor.close()
        connection.close()
        
        logger.info("\n🎉 Migration completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("DATABASE MIGRATION: Adding Security & 2FA Columns")
    print("=" * 60)
    print("\nThis will add the following columns to the 'users' table:")
    print("  • failed_login_attempts")
    print("  • last_failed_login")
    print("  • account_locked_until")
    print("  • password_last_changed")
    print("  • must_change_password")
    print("  • two_factor_enabled")
    print("  • two_factor_secret")
    print("  • backup_codes")
    print("\n" + "=" * 60)
    
    response = input("\nProceed with migration? (yes/no): ").strip().lower()
    
    if response in ['yes', 'y']:
        print("\nRunning migration...\n")
        success = migrate_users_table()
        if success:
            print("\n✅ Database updated successfully!")
        else:
            print("\n❌ Migration failed. Check logs for details.")
    else:
        print("\n❌ Migration cancelled.")
