#!/usr/bin/env python
"""
This script checks the environment to ensure it's properly set up for running scrapers.
It can be used as a standalone script or imported by other scripts.
"""
import os
import sys
import importlib.util
import subprocess
from pathlib import Path

def check_environment():
    """Checks if the environment is properly set up for running scrapers"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Script directory: {script_dir}")
    print(f"Current directory: {os.getcwd()}")
    
    # Check Python path
    print("\nPython path:")
    for path in sys.path:
        print(f"  - {path}")
    
    # Check if Leita module can be imported
    try:
        import Leita
        print("\n✅ Leita module can be imported")
    except ImportError:
        print("\n❌ Leita module cannot be imported")
        # Try to fix by adding the parent directory to the path
        sys.path.insert(0, script_dir)
        try:
            import Leita
            print("   Fixed: Leita module can now be imported")
        except ImportError:
            print("   Still cannot import Leita module")
    
    # Check if spider modules exist
    spiders_dir = os.path.join(script_dir, 'Leita', 'spiders')
    if not os.path.exists(spiders_dir):
        print(f"\n❌ Spiders directory not found: {spiders_dir}")
        os.makedirs(spiders_dir, exist_ok=True)
        print(f"   Created spiders directory: {spiders_dir}")
    
    # Create __init__.py files if they don't exist
    init_files = [
        os.path.join(script_dir, 'Leita', '__init__.py'),
        os.path.join(script_dir, 'Leita', 'spiders', '__init__.py')
    ]
    for init_file in init_files:
        if not os.path.exists(init_file):
            with open(init_file, 'w') as f:
                f.write("# Package initialization file\n")
            print(f"Created {init_file}")
    
    # List expected spider files
    expected_spiders = [
        "dekkjahollin.py",
        "klettur.py",
        "mitra.py",
        "n1.py",
        "nesdekk.py",
        "dekkjasalan.py"
    ]
    
    # Check if expected spider files exist
    print("\nChecking for spider files:")
    missing_spiders = []
    for spider in expected_spiders:
        spider_file = os.path.join(spiders_dir, spider)
        if os.path.exists(spider_file):
            print(f"  ✅ {spider}")
        else:
            print(f"  ❌ {spider} - not found")
            missing_spiders.append(spider)
    
    # If spider files are missing, run the copy_spiders.py script
    if missing_spiders:
        print("\n🔄 Running copy_spiders.py to fix missing spider files...")
        copy_script = os.path.join(script_dir, "copy_spiders.py")
        if os.path.exists(copy_script):
            subprocess.run([sys.executable, copy_script], check=True)
            # Check again
            still_missing = []
            for spider in missing_spiders:
                if not os.path.exists(os.path.join(spiders_dir, spider)):
                    still_missing.append(spider)
            if still_missing:
                print(f"\n❌ Still missing spider files: {', '.join(still_missing)}")
                return False
            else:
                print("\n✅ All spider files are now available")
        else:
            print(f"\n❌ copy_spiders.py not found: {copy_script}")
            return False
    
    print("\n✅ Environment check completed successfully")
    return True

if __name__ == "__main__":
    success = check_environment()
    sys.exit(0 if success else 1)
