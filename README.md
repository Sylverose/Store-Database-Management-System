# Store Database Management System

Enterprise-grade store management application with role-based authentication, real-time ETL operations, and comprehensive data analytics. Built with Python, PySide6, and MySQL for managing retail operations including inventory, orders, staff, and customer data.

**Key Capabilities:**
- 🔐 Multi-level user authentication (Employee/Manager/Administrator)
- 📊 Real-time database operations with progress tracking
- 📄 PDF report generation for customer analytics
- 🔄 ETL pipeline for CSV and API data integration
- 🎨 Professional desktop UI with light/dark themes
- 🛡️ Enterprise security features (account lockout, password policies, session management)

## Key Features

### Authentication & Security
- **Role-Based Access Control**: 3 distinct user levels with granular permissions
- **bcrypt Password Hashing**: Industry-standard Argon2-based encryption
- **Session Management**: Singleton pattern with automatic timeout
- **Account Lockout**: Protection against brute-force attacks
- **Password Policy Enforcement**: Complexity requirements with validation
- **Audit Trail**: Login tracking and failed attempt monitoring

### User Interface
- **Modern PySide6 (Qt6)**: Professional desktop application framework
- **Dual Theme System**: Light and dark themes with instant switching
- **Responsive Design**: Adaptive layouts for different screen sizes
- **Multi-threaded Operations**: Non-blocking UI during database operations
- **Real-time Progress Tracking**: Live progress bars and status updates
- **Tabbed Interface**: Organized workspace with role-based tab visibility

### Data Management
- **PDF Report Generation**: Customer data export with professional formatting (reportlab)
- **CSV Import/Export**: Bulk data operations with validation
- **API Integration**: RESTful API client with automatic endpoint discovery
- **Batch Processing**: Optimized insert/update/delete operations
- **Data Validation**: Schema alignment and integrity checks
- **NaN→NULL Conversion**: Proper handling of missing data for MySQL

### Database Operations
- **PyMySQL Driver**: Pure Python MySQL connector with connection pooling
- **10-Table Schema**: Comprehensive relational database with foreign keys
- **Transaction Support**: InnoDB engine with ACID compliance
- **Auto-schema Creation**: Database and tables created automatically
- **Migration Support**: Schema updates and version management
- **Query Optimization**: Indexed columns and efficient joins

### API & External Data
- **Smart Endpoint Detection**: Auto-discovery of API structure and routes
- **Multiple Server Support**: Works with different API architectures
- **Fallback Logic**: Automatic retry with alternative endpoints
- **Rate Limiting**: Configurable request throttling to prevent API abuse
- **Retry Handler**: Exponential backoff strategy for failed requests
- **Error Recovery**: Graceful handling of network and server errors

### Development Features
- **Modular Architecture**: Separation of concerns with clear interfaces
- **Facade Pattern**: Simplified interfaces for complex subsystems
- **Worker Thread Pattern**: Async operations with Qt signals/slots
- **Comprehensive Logging**: Structured JSON logs with correlation IDs
- **Exception System**: Hierarchical exception handling with context
- **Testing Suite**: Unit tests for critical components

## Requirements

### System Requirements
- **Python**: 3.11+ (recommended: 3.13.7)
- **MySQL Server**: 8.0+

### Python Dependencies
```
pandas>=2.0.0
pymysql>=1.0.0
requests>=2.28.0
python-dotenv>=1.0.0
PySide6>=6.4.0
bcrypt>=4.0.0
reportlab>=4.0.0
psutil>=5.9.0
```

**Install:**
```bash
pip install -r requirements.txt
```

## Installation

### Prerequisites

1. **Python 3.11+** (Python 3.13.7 recommended)
   - Download from [python.org](https://www.python.org/downloads/)
   - During installation, check "Add Python to PATH"

2. **MySQL Server 8.0+**
   - Download from [mysql.com](https://dev.mysql.com/downloads/mysql/)
   - Remember your root password during installation
   - Ensure MySQL service is running

3. **Git** (optional, for cloning)
   - Download from [git-scm.com](https://git-scm.com/downloads/)

### Step-by-Step Installation

**1. Get the Project**
```bash
# Option A: Clone with Git
git clone https://github.com/Sylverose/Advanced-Python-ETL-Pipeline-with-GUI.git
cd Advanced-Python-ETL-Pipeline-with-GUI

# Option B: Download ZIP
# Download from GitHub → Extract → Open folder in terminal
```

**2. Create Virtual Environment (Recommended)**
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/Mac
python3 -m venv .venv
source .venv/bin/activate
```

**3. Install Dependencies**
```bash
pip install -r requirements.txt
```

**4. Configure Database**

Create a `.env` file in the project root directory:
```bash
# Windows (PowerShell)
New-Item .env -ItemType File

# Linux/Mac
touch .env
```

Edit `.env` with your MySQL credentials:
```
DB_USER=root
DB_PASSWORD=your_mysql_password_here
DB_HOST=127.0.0.1
DB_NAME=store_manager
```

**5. Initialize Authentication System**
```bash
python initialize_auth.py
```

This will:
- Connect to MySQL and create the `store_manager` database
- Create the `users` table
- Prompt you to create an administrator account
- Optionally link the admin to an existing staff member

**6. Launch the Application**
```bash
python run_app.py
```

### Verification

After installation, verify everything works:

1. **Database Connection**: The app should connect to MySQL without errors
2. **Login Window**: You should see the login screen
3. **Admin Login**: Use the credentials you created in step 5
4. **Dashboard**: After login, you should see the dashboard

### Troubleshooting Installation

**"python is not recognized"**
- Python is not in your PATH
- Reinstall Python and check "Add Python to PATH"
- Or use full path: `C:\Python313\python.exe`

**"pip install fails"**
- Upgrade pip: `python -m pip install --upgrade pip`
- Use `pip3` instead of `pip` on Linux/Mac

**"Could not connect to database"**
- Ensure MySQL service is running
- Check your credentials in `.env`
- Test connection: `mysql -u root -p` in terminal

**"Access denied for user"**
- Verify password in `.env` matches MySQL root password
- Try resetting MySQL password

**"No module named 'PySide6'"**
- Virtual environment not activated
- Run: `.venv\Scripts\activate` (Windows) or `source .venv/bin/activate` (Linux/Mac)
- Reinstall: `pip install -r requirements.txt`

**"initialize_auth.py fails"**
- Ensure database is configured correctly in `.env`
- Check MySQL service is running
- Verify database permissions for the user

## Usage

### First-Time Usage

**1. Launch the Application**
```bash
python run_app.py
```

**2. Login**
- Enter the administrator username and password you created during `initialize_auth.py`
- Click "Login"

**3. Explore the Dashboard**

Based on your role, you'll see different options:

| Feature | Employee | Manager | Administrator |
|---------|----------|---------|---------------|
| View Dashboard | ✅ | ✅ | ✅ |
| View/Export Data | ✅ | ✅ | ✅ |
| Import/Modify Data | ❌ | ✅ | ✅ |
| View Users/Logs | ❌ | ✅ | ✅ |
| Manage Database | ❌ | ❌ | ✅ |
| Manage Users | ❌ | ❌ | ✅ |

**4. Administrator Actions**

As an administrator, you can:

- **Manage Database**: Click "Manage Database" to open the ETL admin window
  - Import CSV files
  - Fetch API data
  - Create/manage database tables
  - Run tests and validations

- **Manage Users**: Click "Manage Users" to:
  - Create new user accounts (Employee, Manager, Administrator)
  - Change user roles
  - Activate/deactivate accounts
  - Link users to staff members

- **Generate Reports**: Export customer data to PDF format

### Common Workflows

**Creating a New User (Admin Only)**
1. Login as Administrator
2. Click "Manage Users" button on dashboard
3. Go to "Create User" tab
4. Fill in: username, password, role, optional staff ID
5. Click "Create User"

**Loading Data (Admin Only)**
1. Click "Manage Database"
2. In the ETL window:
   - **For CSV**: Click "Select CSV Files", choose files, click "Load CSV to Database"
   - **For API**: Click "Fetch API Data to Database"
3. Monitor progress in the output section

**Exporting Reports**
1. In the dashboard, find the "Customer Reporting" section
2. Select customer from dropdown
3. Click "Generate PDF Report"
4. PDF saves to `data/print/` folder

### Alternative Launch Methods

```bash
# Production: Launch with authentication (recommended)
python run_app.py

# Development: Direct admin access (bypasses authentication)
python run_admin_direct.py

# CLI: Run ETL operations from command line
python src/main.py
```

**When to use `run_admin_direct.py`:**
- Development and testing
- Quick database operations without login
- Bypasses all authentication (use only in secure environments)

## Authentication System

### Overview

The application uses a comprehensive role-based authentication system with three user levels:

| Role | Description | Typical Use Case |
|------|-------------|------------------|
| **Employee** | Basic access to view and export data | Data analysts, viewers |
| **Manager** | Can import and modify data | Department managers, data managers |
| **Administrator** | Full system access including user management | System administrators, IT staff |

### User Roles & Permissions

| Feature | Employee | Manager | Administrator |
|---------|----------|---------|---------------|
| View dashboard & data | ✅ | ✅ | ✅ |
| Export data (CSV/PDF) | ✅ | ✅ | ✅ |
| Import CSV data | ❌ | ✅ | ✅ |
| Modify/update data | ❌ | ✅ | ✅ |
| View users & logs | ❌ | ✅ | ✅ |
| Delete data | ❌ | ❌ | ✅ |
| Manage database (full ETL) | ❌ | ❌ | ✅ |
| Create/manage users | ❌ | ❌ | ✅ |
| Change system settings | ❌ | ❌ | ✅ |

### Initial Setup

**Step 1: Run initialization script**
```bash
python initialize_auth.py
```

**Step 2: Follow the prompts**
```
Welcome to the ETL Pipeline Manager - Authentication Setup

Enter admin username: admin
Enter admin password: ********
Confirm password: ********

Link to existing staff member? (y/n): n

✅ Administrator account created successfully!
   Username: admin
   Role: Administrator
```

**Step 3: Login**
```bash
python run_app.py
```

Use the credentials you just created to login.

### Security Features

- ✅ **bcrypt Password Hashing**: Military-grade password encryption
- ✅ **Account Lockout**: Automatic lockout after failed login attempts
- ✅ **Password Policy**: Enforces minimum complexity requirements
- ✅ **Session Management**: Secure session handling with timeout
- ✅ **Session Timeout**: Automatic logout after inactivity
- ✅ **Password Change Enforcement**: Can require password changes
- ✅ **Active Status**: Deactivate users without deleting accounts

### Users Table Schema

```sql
CREATE TABLE users (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    staff_id INT UNIQUE,                    -- Optional link to staff
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,    -- bcrypt hashed
    role ENUM('Employee', 'Manager', 'Administrator') NOT NULL,
    last_login DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    active BOOLEAN DEFAULT TRUE,
    failed_login_attempts INT DEFAULT 0,
    last_failed_login DATETIME,
    account_locked_until DATETIME,
    password_last_changed DATETIME DEFAULT CURRENT_TIMESTAMP,
    must_change_password BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (staff_id) REFERENCES staffs(staff_id)
)
```

### User Management (Admin Only)

**GUI Method:**
1. Login as Administrator
2. Click "Manage Users" button on dashboard
3. **Create Tab**: Add new users
   - Enter username (must be unique)
   - Set password (will be hashed automatically)
   - Select role (Employee/Manager/Administrator)
   - Optional: Link to staff member by ID
4. **Manage Tab**: View and manage existing users
   - Change user roles
   - Activate/deactivate accounts
   - View user details and last login

**Programmatic Method:**
```python
from auth.user_manager import UserManager
from connect import connect_to_mysql
from config.database import DatabaseConfig

# Setup
db_config = DatabaseConfig().to_dict()
connection = connect_to_mysql(db_config)
user_manager = UserManager(connection)

# Create a new user
user_manager.create_user(
    username="john.doe",
    password="SecurePass123!",
    role="Manager",
    staff_id=5  # Optional: links to staffs table
)

# Change user role
user_manager.update_user_role(user_id=2, new_role="Administrator")

# Deactivate user (keeps data, prevents login)
user_manager.deactivate_user(user_id=3)

# Reactivate user
user_manager.activate_user(user_id=3)
```

### Password Requirements

The system enforces the following password policy:

- **Minimum length**: 8 characters
- **Complexity**: Must include:
  - At least one uppercase letter (A-Z)
  - At least one lowercase letter (a-z)
  - At least one number (0-9)
  - At least one special character (!@#$%^&*)

**Example valid passwords:**
- `SecurePass123!`
- `MyP@ssw0rd`
- `Admin#2024`

### Troubleshooting Authentication

**"Invalid username or password"**
- Usernames are case-sensitive
- Check for typos in username
- Ensure caps lock is off for password
- Verify account is active: `SELECT * FROM users WHERE username='your_username';`

**"Account locked"**
- Too many failed login attempts
- Wait for lockout period to expire (check `account_locked_until` in database)
- Or ask admin to reset: `UPDATE users SET failed_login_attempts=0, account_locked_until=NULL WHERE username='your_username';`

**"No users exist"**
- Run `python initialize_auth.py` to create first admin
- Check database connection in `.env`

**"Must change password"**
- Contact administrator to reset `must_change_password` flag
- Or implement password change feature (future enhancement)

## Project Structure

```
ETL/
├── data/
│   ├── CSV/                       # CSV data sources
│   ├── API/                       # API exports
│   ├── data_model.md
│   └── etl_data_model_diagram.mmd
├── gui/
│   ├── login_window/              # Authentication
│   ├── dashboard_window/          # Main dashboard
│   ├── admin_window/              # Database management
│   ├── user_management/           # User CRUD
│   ├── tabbed_window.py           # Window container
│   └── themes/                    # Theme system
│       ├── base_theme.py
│       ├── dark_theme.py
│       ├── light_theme.py
│       ├── theme_manager.py
│       └── img/
│           └── logo.png           # App icon
├── src/
│   ├── auth/                      # Authentication system
│   │   ├── user_manager.py        # Main facade
│   │   ├── password_handler.py
│   │   ├── password_policy.py
│   │   ├── user_authenticator.py
│   │   ├── user_repository.py
│   │   ├── session.py
│   │   ├── session_timeout.py
│   │   ├── account_lockout.py
│   │   └── permissions.py
│   ├── api/                       # API client
│   ├── config/                    # Configuration
│   ├── database/                  # Database operations
│   │   ├── db_manager.py
│   │   ├── connection_manager.py
│   │   ├── csv_operations.py
│   │   ├── data_from_api.py
│   │   ├── pdf_generator.py      # PDF reports
│   │   ├── schema_manager.py
│   │   ├── batch_operations/
│   │   └── utilities/
│   ├── exceptions/                # Exception handling
│   └── logs/
├── logs/
├── tests/
├── run_app.py                     # Main entry (with auth)
├── run_admin_direct.py            # Direct admin (no auth)
├── initialize_auth.py             # Auth setup
└── requirements.txt
```

## Database Configuration

### Quick Setup

**Create `.env` file in project root:**
```
DB_USER=root
DB_PASSWORD=your_mysql_password_here
DB_HOST=127.0.0.1
DB_NAME=store_manager
```

### Database Schema

The application manages **10 tables** with proper foreign key relationships:

**Core Business Tables:**
- `categories` - Product categories
- `brands` - Product brands
- `products` - Product catalog (links to categories, brands)
- `stores` - Store locations
- `staffs` - Employee and manager data
- `stocks` - Inventory levels (links to products, stores)

**Transaction Tables:**
- `customers` - Customer information
- `orders` - Order headers (links to customers, stores, staffs)
- `order_items` - Order line items (links to orders, products)

**Security Table:**
- `users` - Authentication and authorization (links to staffs)

### Automatic Setup

When you run `initialize_auth.py` or launch the app for the first time:

1. **Database Creation**: If `store_manager` doesn't exist, it will be created
2. **Table Creation**: All 10 tables will be created with proper schema
3. **Data Validation**: Schema is validated on each connection

### Manual Database Operations

**Connect to MySQL directly:**
```bash
mysql -u root -p
```

**View tables:**
```sql
USE store_manager;
SHOW TABLES;
DESCRIBE users;
```

**Check data:**
```sql
SELECT * FROM users;
SELECT * FROM products LIMIT 10;
```

### Connection Details

- **Driver**: PyMySQL (pure Python MySQL client)
- **Engine**: InnoDB (supports foreign keys and transactions)
- **Connection Pooling**: Managed automatically
- **Auto-commit**: Disabled (explicit transaction control)
- **Character Set**: utf8mb4 (full Unicode support)

## Architecture

### GUI Components
```
run_app.py → LoginWindow → TabbedMainWindow
                              ├── DashboardWindow (role-based)
                              ├── ETLMainWindow (Admin only)
                              └── UserManagementDialog (Admin only)
```

### Authentication Flow
```
UserManager (Facade)
    ├── PasswordHandler → bcrypt hashing
    ├── UserAuthenticator → login/session
    └── UserRepository → CRUD operations
```

### Theme System
```
ThemeManager
    ├── BaseTheme (Abstract)
    ├── LightTheme
    └── DarkTheme
```

### Database Operations
```
DatabaseManager
    ├── ConnectionManager → PyMySQL pooling
    ├── CSVOperations → pandas import/export
    ├── SchemaManager → table creation/validation
    └── BatchOperations → optimized bulk operations
```

## Testing

```bash
cd tests && python run_tests.py
python src/cache_cleaner.py
```

## Contact

**Project Maintainer:** Andy Sylvia Rosenvold  
**Email:** andy.rosenvold@specialisterne.com  
**Repository:** https://github.com/Sylverose/Advanced-Python-ETL-Pipeline-with-GUI

## License

MIT License - see LICENSE file for details



