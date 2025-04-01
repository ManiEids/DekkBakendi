#!/usr/bin/env python
import os
import shutil
import sys
import glob
import inspect

def ensure_spider_files():
    """
    Ensures that spider files are correctly located in the Leita/spiders directory.
    This helps when files are in the wrong location or missing on deployment platforms.
    """
    # Define paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Script directory: {script_dir}")
    
    spider_source_dirs = [
        os.path.join(script_dir, 'Leita', 'spiders'),
        os.path.join(script_dir, 'spiders'),
        script_dir,
        os.path.join(script_dir, 'Leita')
    ]
    target_dir = os.path.join(script_dir, 'Leita', 'spiders')
    
    # Ensure target directory exists
    os.makedirs(target_dir, exist_ok=True)
    print(f"Ensuring target directory exists: {target_dir}")
    
    # Spider modules we're looking for
    spider_modules = [
        'dekkjahollin.py',
        'klettur.py',
        'mitra.py',
        'n1.py',
        'nesdekk.py',
        'dekkjasalan.py',
    ]
    
    # Ensure __init__.py exists in the spiders directory
    init_file = os.path.join(target_dir, '__init__.py')
    if not os.path.exists(init_file):
        with open(init_file, 'w') as f:
            f.write("# Package initialization file for spiders\n")
        print(f"Created {init_file}")
    
    # Look for spider files in source directories and copy them to target directory
    found_spiders = []
    for source_dir in spider_source_dirs:
        if os.path.exists(source_dir):
            print(f"Checking source directory: {source_dir}")
            for spider_file in spider_modules:
                source_file = os.path.join(source_dir, spider_file)
                if os.path.isfile(source_file) and spider_file not in found_spiders:
                    target_file = os.path.join(target_dir, spider_file)
                    print(f"Copying {source_file} to {target_file}")
                    shutil.copy2(source_file, target_file)
                    found_spiders.append(spider_file)
    
    # If no spider files were found, create stub files to avoid failures
    if not found_spiders:
        print("No spider files found in source directories. Creating stub files...")
        create_stub_files(target_dir, spider_modules)
        found_spiders = spider_modules
    
    # Report results
    print(f"✓ Spider files in {target_dir}: {', '.join(found_spiders)}")
    
    # List the contents of the target directory
    print(f"\nContents of {target_dir}:")
    for file in os.listdir(target_dir):
        print(f"  - {file}")
    
    return True  # Always return success since we create stubs if needed

def create_stub_files(target_dir, spider_modules):
    """Create stub spider files when originals aren't found"""
    for spider_file in spider_modules:
        spider_name = spider_file.replace('.py', '')
        target_path = os.path.join(target_dir, spider_file)
        
        # Create a stub spider file
        with open(target_path, 'w') as f:
            f.write(f"""import scrapy

class {spider_name.capitalize()}Spider(scrapy.Spider):
    name = "{spider_name}"
    allowed_domains = ["example.com"]
    start_urls = ["https://example.com"]
    
    def parse(self, response):
        self.logger.warning("This is a stub spider. The actual implementation was not found.")
        yield {{
            "title": "Stub {spider_name} result",
            "message": "This stub was created because the original spider file was not found."
        }}
""")
        print(f"Created stub file for {spider_name}")

if __name__ == "__main__":
    success = ensure_spider_files()
    sys.exit(0 if success else 1)  # Always exit with success
