"""Test CSV file access after moving to CSV subfolder."""

import os
from db_manager import DatabaseManager

def test_csv_access():
    print("🔍 Testing CSV file access after reorganization...")
    
    db_manager = DatabaseManager()
    print(f"📁 Data directory: {db_manager.data_dir}")
    
    # Test reading each CSV file
    for table_name, csv_file in db_manager.csv_files.items():
        try:
            file_path = os.path.join(db_manager.data_dir, csv_file)
            df = db_manager.read_csv_file(csv_file)
            
            if df is not None:
                print(f"✅ {table_name:12}: {len(df):4} rows, {len(df.columns):2} columns - {csv_file}")
            else:
                print(f"❌ {table_name:12}: Failed to read {csv_file}")
                
        except Exception as e:
            print(f"❌ {table_name:12}: Error - {e}")
    
    print("\n🎉 CSV file reorganization test completed!")

if __name__ == "__main__":
    test_csv_access()