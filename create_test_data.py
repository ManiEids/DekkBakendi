#!/usr/bin/env python
"""
Creates test data files for the Tire Scraper Dashboard.
"""
import os
import json
from datetime import datetime

def create_test_data():
    """Create sample test data files for each spider"""
    print("Creating test data files...")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Define spider names
    spiders = ["dekkjahollin", "klettur", "mitra", "n1", "nesdekk", "dekkjasalan"]
    
    # Create a sample tire entry
    sample_tire = {
        "title": "Sample Tire",
        "manufacturer": "TestBrand",
        "price": "12.345 kr",
        "tire_size": "205/55R16",
        "width": "205",
        "aspect_ratio": "55",
        "rim_size": "16",
        "stock": "in stock",
        "inventory": 5,
        "picture": "https://example.com/sample_tire.jpg"
    }
    
    # Create a sample data file for each spider
    for spider in spiders:
        # Create 2 sample entries for each spider
        sample_data = [
            {**sample_tire, "title": f"{spider} Sample Tire 1"},
            {**sample_tire, "title": f"{spider} Sample Tire 2"}
        ]
        
        # Write the sample data to a JSON file
        output_file = os.path.join(script_dir, f"{spider}.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(sample_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Created sample data for {spider} with {len(sample_data)} entries")
    
    # Create a combined data file
    combined_data = []
    for spider in spiders:
        spider_data = [
            {
                **sample_tire,
                "title": f"{spider} Combined Tire",
                "seller": spider.capitalize()
            }
        ]
        combined_data.extend(spider_data)
    
    # Write the combined data to a JSON file
    combined_file = os.path.join(script_dir, "combined_tire_data.json")
    with open(combined_file, "w", encoding="utf-8") as f:
        json.dump(combined_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Created combined data file with {len(combined_data)} entries")
    return True

if __name__ == "__main__":
    success = create_test_data()
    print("Test data created successfully!" if success else "Failed to create test data")
