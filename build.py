#!/usr/bin/env python
import os
import sys
import subprocess

def run_command(cmd):
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"Command failed with exit code {result.returncode}")
        sys.exit(result.returncode)
    return result

# Main build steps
run_command("pip install -r requirements.txt")
run_command("python deploy_setup.py")
run_command("pip install -e .")

print("Build completed successfully!")
