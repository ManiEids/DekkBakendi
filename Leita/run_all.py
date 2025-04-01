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

# Debug information
print(f"Current working directory: {os.getcwd()}")
print(f"Project root: {PROJECT_ROOT}")
print(f"Python path: {sys.path}")

# Ensure spider files are where they should be
copy_script = os.path.join(PROJECT_ROOT, "copy_spiders.py")
if os.path.exists(copy_script):
    print("\n🔄 Ensuring spider files are properly installed...")
    subprocess.run([sys.executable, copy_script], check=True)

# List of spiders to run
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
        json_path = os.path.join(PROJECT_ROOT, f"{spider}.json")
        if os.path.exists(json_path):
            os.unlink(json_path)
            print(f"🗑️ Deleted: {json_path}")
    output_json = os.path.join(PROJECT_ROOT, "combined_tire_data.json")
    if os.path.exists(output_json):
        os.unlink(output_json)
        print(f"🗑️ Deleted: {output_json}")

def run_spider_with_direct_runner(spider_name):
    """Use the direct python runner instead of scrapy command line"""
    print(f"🕷️ Running spider directly: {spider_name}")
    direct_runner = os.path.join(PROJECT_ROOT, "run_spider_direct.py")
    output_file = os.path.join(PROJECT_ROOT, f"{spider_name}.json")
    
    if not os.path.exists(direct_runner):
        print(f"❌ Cannot find direct runner at {direct_runner}")
        return False
        
    cmd = [
        sys.executable,  # Use the same Python interpreter
        direct_runner,
        spider_name,
        output_file
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
    for line in iter(process.stdout.readline, ''):
        print(line, end='', flush=True)
    
    process.stdout.close()
    process.wait()
    
    if process.returncode == 0:
        print(f"✅ Finished spider: {spider_name}")
        return True
    else:
        print(f"❌ Failed spider: {spider_name} with return code {process.returncode}")
        return False

def run_spider(spider_name):
    """Try multiple methods to run a spider"""
    # First check if the spider file exists
    spider_file = os.path.join(BASE_DIR, 'spiders', f"{spider_name}.py")
    if not os.path.exists(spider_file):
        print(f"❌ Spider file doesn't exist: {spider_file}")
        print("    Trying to fix by running copy_spiders.py...")
        subprocess.run([sys.executable, os.path.join(PROJECT_ROOT, "copy_spiders.py")])
        
        if not os.path.exists(spider_file):
            print(f"❌ Still can't find spider file {spider_name}.py")
            return False

    # First try the direct runner
    if os.path.exists(os.path.join(PROJECT_ROOT, "run_spider_direct.py")):
        result = run_spider_with_direct_runner(spider_name)
        if result:
            return True
    
    # Fall back to scrapy command line
    print(f"🕷️ Running spider via scrapy command: {spider_name}")
    
    # Change to Leita directory to ensure scrapy can find the spiders
    os.chdir(BASE_DIR)
    print(f"Changed directory to: {os.getcwd()}")
    
    # Try direct scrapy command with just the spider name
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
    for line in iter(process.stdout.readline, ''):
        print(line, end='', flush=True)
    
    process.stdout.close()
    exit_code = process.wait()
    
    if exit_code == 0:
        print(f"✅ Finished spider: {spider_name}")
        return True
    else:
        print(f"❌ Failed spider: {spider_name} with all methods")
        return False

def merge_json_files():
    """Merge all JSON files into one combined file."""
    print("\n📦 All spiders finished. Running merge script...")
    
    # Use the dedicated merge_tires.py script if it exists
    merge_script = os.path.join(BASE_DIR, "merge_tires.py")
    if os.path.exists(merge_script):
        print(f"Running merge script: {merge_script}")
        process = subprocess.run(
            [sys.executable, merge_script],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        print(process.stdout)
        if process.returncode == 0:
            print("✅ Merge completed successfully using merge_tires.py")
            return True
        else:
            print(f"❌ Merge failed with return code {process.returncode}")
    
    # Fallback to manual merging
    print("Performing manual merge...")
    combined_data = []
    
    # Read and combine each file
    for spider in spiders:
        file_path = os.path.join(PROJECT_ROOT, f"{spider}.json")
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                if isinstance(data, list):
                    # Add seller information
                    for item in data:
                        item['seller'] = spider.capitalize()
                    combined_data.extend(data)
                    print(f"  ✓ Added {len(data)} items from {spider}")
                else:
                    print(f"  ✗ Invalid data format in {file_path}")
        except Exception as e:
            print(f"  ✗ Error processing {file_path}: {str(e)}")
    
    # Write the combined data to a file
    if combined_data:
        output_file = os.path.join(PROJECT_ROOT, "combined_tire_data.json")
        with open(output_file, 'w', encoding='utf-8') as outfile:
            json.dump(combined_data, outfile, indent=2, ensure_ascii=False)
        print(f"✅ Successfully combined {len(combined_data)} items into {output_file}")
        return True
    else:
        print("❌ No data to combine")
        return False

if __name__ == "__main__":
    # Clean up old files first
    delete_old_jsons()

    print("\n🚀 Running all spiders sequentially...")
    for spider in spiders:
        success = run_spider(spider)
        if not success:
            print(f"Warning: Spider {spider} failed or was skipped.")
    
    # Merge results
    merge_json_files()
    
    # Now run database update if script exists
    db_update_script = os.path.join(PROJECT_ROOT, "database_update.py")
    if os.path.exists(db_update_script):
        print("\n🔄 Updating database...")
        subprocess.run([sys.executable, db_update_script])
