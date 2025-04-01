import os
import json
import subprocess
import glob
import sys
from pathlib import Path

# Configure paths to work both locally and on Render
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
sys.path.insert(0, PROJECT_ROOT)

spiders = [
    "dekkjahollin",
    "klettur",
    "mitra",
    "n1",
    "nesdekk",
    "dekkjasalan"
]

# Step 1: Clean up old JSON files
def delete_old_jsons():
    print("🔄 Cleaning up old JSON files...")
    for spider in spiders:
        json_path = Path(f"{spider}.json")
        if json_path.exists():
            json_path.unlink()
            print(f"🗑️ Deleted: {json_path}")
    output_json = Path("combined_tire_data.json")
    if output_json.exists():
        output_json.unlink()
        print(f"🗑️ Deleted: {output_json}")

def run_spider(spider_name):
    """Run a spider and wait for it to complete."""
    print(f"🕷️ Running spider: {spider_name}")
    
    # Change to project root directory to ensure scrapy can find the spiders
    os.chdir(PROJECT_ROOT)
    
    # Run spider with absolute path to make sure it finds the right configuration
    cmd = [
        'scrapy', 'crawl', 
        spider_name, 
        '-O', os.path.join(PROJECT_ROOT, f"{spider_name}.json"),
    ]
    print(f"Running command: {' '.join(cmd)}")
    
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE, 
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    # Echo the output to console
    for line in process.stdout:
        print(line, end='', flush=True)
    
    process.stdout.close()
    process.wait()
    
    if process.returncode == 0:
        print(f"✅ Finished spider: {spider_name}")
        return True
    else:
        print(f"❌ Failed spider: {spider_name} with return code {process.returncode}")
        return False

def merge_json_files():
    """Merge all JSON files into one combined file."""
    print("\n📦 All spiders finished. Running merge script...")
    
    # List all the tire data files
    json_files = glob.glob("*.json")
    if not json_files:
        print("❌ No JSON files found to merge.")
        return False
    
    combined_data = []
    
    # Read and combine each file
    for file_path in json_files:
        if file_path == "combined_tire_data.json":
            continue
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                # If it's a list, extend combined_data
                if isinstance(data, list):
                    combined_data.extend(data)
                # If it's a dict, append it
                elif isinstance(data, dict):
                    combined_data.append(data)
                
                print(f"  ✓ Processed {file_path} ({len(data) if isinstance(data, list) else 1} items)")
        except Exception as e:
            print(f"  ✗ Error processing {file_path}: {str(e)}")
    
    # Write the combined data to a new file
    if combined_data:
        with open("combined_tire_data.json", 'w', encoding='utf-8') as outfile:
            json.dump(combined_data, outfile, indent=2, ensure_ascii=False)
        print(f"✅ Successfully combined all tire data into combined_tire_data.json")
        print(f"✅ Merge completed successfully. Ready to query.")
        return True
    else:
        print("❌ No data found to merge.")
        return False

if __name__ == "__main__":
    delete_old_jsons()

    print("\n🚀 Running all spiders sequentially...")
    for spider in spiders:
        success = run_spider(spider)
        if not success:
            print(f"Warning: Spider {spider} failed or was skipped.")

    merge_json_files()
