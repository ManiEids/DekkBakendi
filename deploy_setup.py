#!/usr/bin/env python
"""
Setup script for deployment - ensures proper environment configuration.
"""
import os
import sys
import subprocess
from pathlib import Path

def main():
    """Make sure the environment is properly set up for deployment."""
    print("Running deployment setup...")
    
    # Get the project directory
    project_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Project directory: {project_dir}")
    
    # Create necessary directory structure
    directories = [
        os.path.join(project_dir, "Leita"),
        os.path.join(project_dir, "Leita", "spiders")
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"Ensured directory exists: {directory}")
    
    # Create required __init__.py files
    init_files = [
        os.path.join(project_dir, "Leita", "__init__.py"),
        os.path.join(project_dir, "Leita", "spiders", "__init__.py")
    ]
    
    for init_file in init_files:
        if not os.path.exists(init_file):
            with open(init_file, "w") as f:
                f.write("# Package initialization\n")
            print(f"Created {init_file}")
    
    # Run copy_spiders.py to ensure spider files are in place
    copy_script = os.path.join(project_dir, "copy_spiders.py")
    if os.path.exists(copy_script):
        print("Running copy_spiders.py...")
        result = subprocess.run([sys.executable, copy_script], check=False)
        if result.returncode == 0:
            print("✓ Spider files successfully set up")
        else:
            print("⚠️ Warning: copy_spiders.py returned non-zero exit code")
    
    # Check for environment variables
    required_vars = ["DATABASE_URL", "PORT"]
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    if missing_vars:
        print(f"⚠️ Warning: Missing environment variables: {', '.join(missing_vars)}")
    
    print("✓ Deploy setup completed")
    return 0

if __name__ == "__main__":
    sys.exit(main())
