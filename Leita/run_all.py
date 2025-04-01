import os
import json
import subprocess
import time
import glob
from multiprocessing import Pool
from pathlib import Path

# Configure logging level to see detailed spider activity
os.environ['SCRAPY_SETTINGS_MODULE'] = 'scrapy.settings'
os.environ['SCRAPY_LOG_LEVEL'] = 'DEBUG'  # Use DEBUG to see detailed activity

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
    process = subprocess.Popen(
        ['scrapy', 'crawl', spider_name, '-O', f'{spider_name}.json', '--logfile', f'{spider_name}.log', '-L', 'DEBUG'],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True
    )
    
    # Echo the output to console in real-time to ensure it's captured in web interface
    for line in process.stdout:
        print(line, end='', flush=True)
    
    process.wait()
    
    # Also print log file contents to ensure they appear in the web interface
    if os.path.exists(f'{spider_name}.log'):
        print(f"--- Detailed logs from {spider_name}.log ---")
        with open(f'{spider_name}.log', 'r') as log_file:
            log_content = log_file.read()
            print(log_content)
    
    if process.returncode == 0:
        print(f"✅ Finished spider: {spider_name}")
        return True
    else:
        print(f"❌ Failed spider: {spider_name}")
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
