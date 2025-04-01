#!/usr/bin/env python
"""
Standalone script to update the database with the latest tire data.
This can be run as a scheduled task or as part of a pipeline.
"""
import os
import sys
from pathlib import Path

def main():
    """Update the database with the latest tire data"""
    print("Starting database update process...")
    
    # Make sure the environment is set up correctly
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, script_dir)
    
    # First check if combined_tire_data.json exists
    combined_file = os.path.join(script_dir, "combined_tire_data.json")
    if not os.path.exists(combined_file):
        print(f"Error: {combined_file} not found. Run scrapers first.")
        return False
    
    try:
        # Import the database module and update the database
        from database import TireDatabase
        db = TireDatabase()
        
        # Test connection
        conn = db.connect()
        print("✅ Successfully connected to database")
        
        # Import the data
        success, message = db.import_from_json(combined_file)
        
        if success:
            print(f"✅ {message}")
            return True
        else:
            print(f"❌ {message}")
            return False
    
    except Exception as e:
        import traceback
        print(f"❌ Error updating database: {str(e)}")
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
