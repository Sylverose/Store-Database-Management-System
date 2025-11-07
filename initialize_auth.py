"""
Initialize the database with users table and create default administrator account.
Run this once to set up authentication for the first time.
"""

import sys
import logging
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

from connect import connect_to_mysql
from database.schema_manager import SchemaManager
from auth.user_manager import UserManager
from config import DatabaseConfig

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def initialize_auth_system():
    """Initialize authentication system and create default admin user."""
    
    print("=" * 60)
    print("Authentication System Initialization")
    print("=" * 60)
    print()
    
    try:
        # Connect to database
        print("Connecting to database...")
        db_config = DatabaseConfig().to_dict()
        connection = connect_to_mysql(db_config)
        
        if not connection:
            print("❌ Failed to connect to database")
            return False
        
        print("✅ Connected to database")
        print()
        
        # Create users table
        print("Creating users table...")
        
        cursor = connection.cursor()
        
        # Check if table exists
        cursor.execute("SHOW TABLES LIKE 'users'")
        table_exists = cursor.fetchone() is not None
        
        if table_exists:
            print("⚠️  Users table already exists")
            recreate = input("Do you want to recreate it? (yes/no): ").strip().lower()
            if recreate == 'yes':
                cursor.execute("DROP TABLE users")
                connection.commit()
                print("Dropped existing users table")
                table_exists = False
        
        if not table_exists:
            # Create users table
            create_table_sql = """
                CREATE TABLE users (
                    user_id INT PRIMARY KEY AUTO_INCREMENT,
                    staff_id INT UNIQUE,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    role ENUM('Employee', 'Manager', 'Administrator') NOT NULL DEFAULT 'Employee',
                    last_login DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    active BOOLEAN DEFAULT TRUE,
                    FOREIGN KEY (staff_id) REFERENCES staffs(staff_id) ON DELETE SET NULL,
                    INDEX idx_username (username),
                    INDEX idx_role (role)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """
            cursor.execute(create_table_sql)
            connection.commit()
            print("✅ Users table created successfully")
        
        cursor.close()
        
        print()
        
        # Create default administrator
        print("Creating default administrator account...")
        print()
        
        username = input("Enter administrator username (default: admin): ").strip() or "admin"
        
        # Get password with confirmation
        while True:
            password = input("Enter administrator password: ").strip()
            if len(password) < 6:
                print("❌ Password must be at least 6 characters long")
                continue
            
            password_confirm = input("Confirm password: ").strip()
            if password != password_confirm:
                print("❌ Passwords do not match")
                continue
            
            break
        
        # Optional: Link to staff member
        link_staff = input("\nLink to existing staff member? (yes/no): ").strip().lower()
        staff_id = None
        
        if link_staff == 'yes':
            cursor = connection.cursor()
            cursor.execute("SELECT staff_id, name, last_name, email FROM staffs WHERE active = TRUE")
            staff_members = cursor.fetchall()
            cursor.close()
            
            if staff_members:
                print("\nAvailable staff members:")
                for i, staff in enumerate(staff_members, 1):
                    print(f"{i}. ID: {staff[0]} - {staff[1]} {staff[2]} ({staff[3]})")
                
                try:
                    choice = int(input("\nEnter staff number (or 0 to skip): "))
                    if choice > 0 and choice <= len(staff_members):
                        staff_id = staff_members[choice - 1][0]
                        print(f"✅ Linked to staff ID: {staff_id}")
                except ValueError:
                    print("⚠️  Invalid input, skipping staff link")
            else:
                print("⚠️  No active staff members found")
        
        # Create user
        user_manager = UserManager(connection)
        success = user_manager.create_user(
            username=username,
            password=password,
            role='Administrator',
            staff_id=staff_id
        )
        
        if success:
            print(f"\n✅ Administrator account '{username}' created successfully!")
            print()
            print("=" * 60)
            print("Initialization Complete!")
            print("=" * 60)
            print(f"\nYou can now log in with:")
            print(f"  Username: {username}")
            print(f"  Role: Administrator")
            print()
            return True
        else:
            print("\n❌ Failed to create administrator account")
            return False
        
    except Exception as e:
        logger.error(f"Error during initialization: {e}")
        print(f"\n❌ Error: {e}")
        return False
    finally:
        if connection:
            connection.close()
            print("Database connection closed")


if __name__ == "__main__":
    try:
        success = initialize_auth_system()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nInitialization cancelled by user")
        sys.exit(1)
