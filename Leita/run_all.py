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
        json_path = Path(f"{spider}.json")
        if json_path.exists():
            json_path.unlink()
            print(f"🗑️ Deleted: {json_path}")
    output_json = Path("combined_tire_data.json")
    if output_json.exists():
        output_json.unlink()
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
    # First try the direct runner
    if os.path.exists(os.path.join(PROJECT_ROOT, "run_spider_direct.py")):
        return run_spider_with_direct_runner(spider_name)
    
    # Fall back to scrapy command line
    print(f"🕷️ Running spider via scrapy command: {spider_name}")
    
    # Change to project root directory to ensure scrapy can find the spiders
    os.chdir(PROJECT_ROOT)
    
    # Use PYTHONPATH to help scrapy find modules
    env = os.environ.copy()
    env['PYTHONPATH'] = PROJECT_ROOT
    
    # Try with the full module path
    cmd = [
        'scrapy', 'crawl', 
        f"Leita.spiders.{spider_name}.{spider_name}", 
        '-O', os.path.join(PROJECT_ROOT, f"{spider_name}.json"),
    ]
    print(f"Running command: {' '.join(cmd)}")
    
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE, 
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        env=env
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
        # Try again with just the spider name
        cmd = [
            'scrapy', 'crawl', 
            spider_name, 
            '-O', os.path.join(PROJECT_ROOT, f"{spider_name}.json"),
        ]
        print(f"Retry with command: {' '.join(cmd)}")
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env=env
        )
        
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

    print("\n🚀 Running all spiders sequentially (one at a time)...")
    for spider in spiders:
        success = run_spider(spider)
        if not success:
            print(f"Warning: Spider {spider} failed or was skipped.")
        else:
            # Process one successful spider at a time to avoid memory issues
            print(f"\n📦 Processing {spider} data...")
            with open(f"{spider}.json", 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    print(f"  ✓ {spider}.json contains {len(data) if isinstance(data, list) else 1} items")
                except json.JSONDecodeError:
                    print(f"  ✗ {spider}.json contains invalid JSON")

    merge_json_files()
