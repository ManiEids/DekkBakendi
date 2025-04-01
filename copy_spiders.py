#!/usr/bin/env python
import os
import shutil
import sys
import glob

def ensure_spider_files():
    """
    Ensures that spider files are correctly located in the Leita/spiders directory.
    This helps when files are in the wrong location or missing on deployment platforms.
    """
    # Define paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    spider_source_dirs = [
        os.path.join(script_dir, 'Leita', 'spiders'),
        os.path.join(script_dir, 'spiders'),
        script_dir
    ]
    target_dir = os.path.join(script_dir, 'Leita', 'spiders')
    
    # Ensure target directory exists
    os.makedirs(target_dir, exist_ok=True)
    
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
    
    # Report results
    if found_spiders:
        print(f"✓ Successfully copied {len(found_spiders)} spider files to {target_dir}")
        print(f"Spider files: {', '.join(found_spiders)}")
    else:
        print(f"✗ No spider files found in any of the source directories!")
        
    # List the contents of the target directory
    print(f"\nContents of {target_dir}:")
    for file in os.listdir(target_dir):
        print(f"  - {file}")
    
    return len(found_spiders) > 0

if __name__ == "__main__":
    success = ensure_spider_files()
    sys.exit(0 if success else 1)
