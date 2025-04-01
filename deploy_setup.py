#!/usr/bin/env python
import os
import shutil
import sys

def deploy_setup():
    """Prepares the project for deployment by ensuring all spider files are in the correct location"""
    print("Setting up deployment...")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    target_dir = os.path.join(base_dir, "Leita", "spiders")
    os.makedirs(target_dir, exist_ok=True)
    
    # Initialize empty __init__.py files
    init_file = os.path.join(target_dir, "__init__.py")
    if not os.path.exists(init_file):
        with open(init_file, "w") as f:
            f.write("# Spider package initialization file\n")
    
    # List of included spider files
    included_spiders = [
        os.path.join(base_dir, "Leita", "Leita", "spiders", "dekkjahollin.py"),
        os.path.join(base_dir, "Leita", "Leita", "spiders", "klettur.py"),
        os.path.join(base_dir, "Leita", "Leita", "spiders", "mitra.py"),
        os.path.join(base_dir, "Leita", "Leita", "spiders", "n1.py"),
        os.path.join(base_dir, "Leita", "Leita", "spiders", "nesdekk.py"),
        os.path.join(base_dir, "Leita", "Leita", "spiders", "dekkjasalan.py"),
    ]
    
    # Manually bundle the spiders
    print("Copying spider files to deployment directory:")
    for path in included_spiders:
        if os.path.exists(path):
            filename = os.path.basename(path)
            dest = os.path.join(target_dir, filename)
            print(f"  Copying {path} -> {dest}")
            shutil.copy2(path, dest)
    
    print("Deployment setup complete!")
    return True

if __name__ == "__main__":
    success = deploy_setup()
    sys.exit(0 if success else 1)
