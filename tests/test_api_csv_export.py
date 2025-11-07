"""Test API data export to CSV files."""

from data_from_api import APIClient
from db_manager import DatabaseManager, create_api_tables_and_csv
import os

def test_api_csv_export():
    """Test the API CSV export functionality."""
    print("🧪 Testing API CSV Export Functionality")
    print("="*50)
    
    # Method 1: Using API client directly
    print("\n📋 Method 1: Direct API Client CSV Export")
    client = APIClient()
    
    try:
        success = client.save_all_api_data_to_csv()
        client.close()
        
        if success:
            print("✅ Direct API CSV export successful!")
        else:
            print("❌ Direct API CSV export failed!")
            
    except Exception as e:
        print(f"❌ Error in direct API export: {e}")
    
    # Method 2: Using database manager
    print("\n📋 Method 2: Database Manager CSV Export")
    db_manager = DatabaseManager()
    
    try:
        success = db_manager.export_api_data_to_csv()
        
        if success:
            print("✅ Database manager CSV export successful!")
        else:
            print("❌ Database manager CSV export failed!")
            
    except Exception as e:
        print(f"❌ Error in database manager export: {e}")
    
    # Check if files were created
    print("\n📁 Checking CSV Files in data/API/:")
    api_dir = os.path.join('..', 'data', 'API')
    
    if os.path.exists(api_dir):
        files = os.listdir(api_dir)
        csv_files = [f for f in files if f.endswith('.csv')]
        
        if csv_files:
            print(f"✅ Found {len(csv_files)} CSV files:")
            for file in sorted(csv_files):
                file_path = os.path.join(api_dir, file)
                if os.path.exists(file_path):
                    size = os.path.getsize(file_path)
                    print(f"  📄 {file:<20} ({size:,} bytes)")
        else:
            print("❌ No CSV files found in API directory")
    else:
        print("❌ API directory does not exist")

if __name__ == "__main__":
    test_api_csv_export()