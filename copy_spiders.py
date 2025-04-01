#!/usr/bin/env python
import os
import shutil
import sys
import glob
import inspect
import traceback

def ensure_spider_files():
    """
    Ensures that spider files are correctly located in the Leita/spiders directory.
    This helps when files are in the wrong location or missing on deployment platforms.
    """
    try:
        # Define paths
        script_dir = os.path.dirname(os.path.abspath(__file__))
        print(f"Script directory: {script_dir}")
        
        # Define possible source and target locations
        spider_source_dirs = [
            os.path.join(script_dir, 'Leita', 'Leita', 'spiders'),  # For nested deployments
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
        
        # Ensure __init__.py exists in all relevant directories
        init_dirs = [
            os.path.join(script_dir, 'Leita'),
            target_dir
        ]
        
        for init_dir in init_dirs:
            os.makedirs(init_dir, exist_ok=True)
            init_file = os.path.join(init_dir, '__init__.py')
            if not os.path.exists(init_file):
                with open(init_file, 'w') as f:
                    f.write("# Package initialization file\n")
                print(f"Created {init_file}")
        
        # First do a wide search for any Python files that might contain spider code
        print("\nSearching for spider files in the project directory:")
        found_potential_spiders = []
        for root, _, files in os.walk(script_dir):
            for file in files:
                if file.endswith('.py') and file in spider_modules:
                    path = os.path.join(root, file)
                    print(f"  Found potential spider: {path}")
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        # Check if this is a real spider file, not a stub
                        if "This is a stub spider" not in content and "scrapy.Spider" in content:
                            print(f"  ✓ Confirmed real spider implementation: {path}")
                            found_potential_spiders.append((file, path))
        
        # Look for spider files in potential source directories
        found_spiders = []
        for source_dir in spider_source_dirs:
            if os.path.exists(source_dir):
                print(f"Checking source directory: {source_dir}")
                for spider_file in spider_modules:
                    source_file = os.path.join(source_dir, spider_file)
                    if os.path.isfile(source_file) and spider_file not in found_spiders:
                        # Check if this is a stub or real implementation
                        with open(source_file, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            if "This is a stub spider" not in content:
                                target_file = os.path.join(target_dir, spider_file)
                                print(f"Copying {source_file} to {target_file}")
                                shutil.copy2(source_file, target_file)
                                found_spiders.append(spider_file)
        
        # If some spiders weren't found in the standard directories, use the ones found in the wide search
        missing_spiders = [file for file in spider_modules if file not in found_spiders]
        if missing_spiders and found_potential_spiders:
            for file, path in found_potential_spiders:
                if file in missing_spiders:
                    target_file = os.path.join(target_dir, file)
                    print(f"Copying potential spider {path} to {target_file}")
                    shutil.copy2(path, target_file)
                    found_spiders.append(file)
                    missing_spiders.remove(file)
        
        # If no spider files were found, create stub files to avoid failures
        if missing_spiders:
            print(f"Still missing spiders: {missing_spiders}")
            create_stub_files(target_dir, missing_spiders)
            found_spiders.extend(missing_spiders)
        
        # Report results
        print(f"✓ Spider files in {target_dir}: {', '.join(found_spiders)}")
        
        # List the contents of the target directory and validate
        print(f"\nFinal contents of {target_dir}:")
        for file in os.listdir(target_dir):
            print(f"  - {file}")
            if file.endswith('.py') and file != '__init__.py':
                try:
                    with open(os.path.join(target_dir, file), 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        if "This is a stub spider" in content:
                            print(f"    ⚠️ Warning: {file} is a stub implementation")
                        else:
                            print(f"    ✓ {file} appears to be a real implementation")
                except Exception as e:
                    print(f"    ❌ Error reading file: {str(e)}")
        
        return True  # Always return success since we create stubs if needed
    except Exception as e:
        print(f"Error in ensure_spider_files: {str(e)}")
        traceback.print_exc()
        return False

def create_stub_files(target_dir, spider_modules):
    """Create stub spider files when originals aren't found"""
    for spider_file in spider_modules:
        spider_name = spider_file.replace('.py', '')
        target_path = os.path.join(target_dir, spider_file)
        
        # Don't overwrite existing files
        if os.path.exists(target_path):
            print(f"Skipping existing file: {target_path}")
            continue
            
        # Create a stub spider file
        with open(target_path, 'w') as f:
            f.write(f"""import scrapy
import json
import os
import logging

class {spider_name.capitalize()}Spider(scrapy.Spider):
    name = "{spider_name}"
    allowed_domains = ["example.com"]
    start_urls = ["https://example.com"]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger.warning("This is a stub spider. The actual implementation was not found.")
        
        # Try to find existing data to use
        script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.data_file = os.path.join(script_dir, '{spider_name}.json')
        if os.path.exists(self.data_file):
            self.logger.info(f"Using existing data from {{self.data_file}}")
            
    def parse(self, response):
        # First try to use existing data if available
        if hasattr(self, 'data_file') and os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    if existing_data:
                        self.logger.info(f"Yielding {{len(existing_data)}} items from existing data")
                        for item in existing_data:
                            yield item
                        return
            except Exception as e:
                self.logger.error(f"Error loading existing data: {{e}}")
        
        # Fallback stub item if no existing data
        yield {{
            "title": "Stub {spider_name} result",
            "message": "This stub was created because the original spider file was not found."
        }}
""")
        print(f"Created stub file for {spider_name}")

if __name__ == "__main__":
    success = ensure_spider_files()
    sys.exit(0 if success else 1)  # Always exit with success
