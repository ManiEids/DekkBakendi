#!/usr/bin/env python
import os
import sys
import importlib
import inspect
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def run_spider(spider_name, output_file):
    """Run a spider by name and save output to the specified file"""
    print(f"Starting spider run process for: {spider_name}")
    print(f"Python path: {sys.path}")
    
    # Check for the spider file first to ensure it exists
    spider_file = os.path.join(project_root, 'Leita', 'spiders', f"{spider_name}.py")
    if os.path.exists(spider_file):
        print(f"✓ Spider file found: {spider_file}")
    else:
        print(f"✗ Spider file not found: {spider_file}")
        # List files in the spiders directory
        spiders_dir = os.path.join(project_root, 'Leita', 'spiders')
        if os.path.isdir(spiders_dir):
            print(f"Contents of {spiders_dir}:")
            for file in os.listdir(spiders_dir):
                print(f"  - {file}")
        else:
            print(f"Spiders directory not found: {spiders_dir}")
    
    # Try multiple possible import paths
    possible_modules = [
        f"Leita.spiders.{spider_name}",  # Full path
        f"spiders.{spider_name}",        # From Leita directory
        spider_name                      # Direct import
    ]
    
    module = None
    for module_path in possible_modules:
        try:
            print(f"Attempting to import: {module_path}")
            module = importlib.import_module(module_path)
            print(f"✓ Successfully imported {module_path}")
            break
        except ImportError as e:
            print(f"✗ Import failed for {module_path}: {e}")
    
    if not module:
        print("❌ All import attempts failed")
        return False
    
    # Find the spider class in the module
    spider_cls = None
    for name, obj in inspect.getmembers(module):
        try:
            # Check if it's a class with a 'name' attribute equal to spider_name
            if inspect.isclass(obj) and hasattr(obj, 'name') and obj.name == spider_name:
                spider_cls = obj
                print(f"✓ Found spider class: {name}")
                break
        except Exception:
            continue
    
    if not spider_cls:
        print(f"❌ Could not find spider class for {spider_name} in module {module.__name__}")
        return False
    
    # Configure and run the spider
    try:
        settings = get_project_settings()
        settings.set('LOG_LEVEL', 'INFO')
        # Explicitly set FEEDS setting to output to the JSON file
        settings.set('FEEDS', {
            output_file: {
                'format': 'json',
                'encoding': 'utf8',
                'indent': 4,
            }
        })
        
        process = CrawlerProcess(settings)
        process.crawl(spider_cls)
        print(f"Starting crawler process for {spider_name}...")
        process.start()  # This blocks until the crawl is finished
        print(f"Crawler process for {spider_name} completed")
        
        # Verify the output file was created
        if os.path.exists(output_file):
            print(f"✓ Output file created: {output_file}")
            return True
        else:
            print(f"✗ Output file not created: {output_file}")
            return False
    except Exception as e:
        print(f"❌ Error running spider {spider_name}: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python run_spider_direct.py <spider_name> <output_file>")
        sys.exit(1)
    
    spider_name = sys.argv[1]
    output_file = sys.argv[2]
    
    success = run_spider(spider_name, output_file)
    if success:
        print(f"✅ Successfully ran spider {spider_name}")
        sys.exit(0)
    else:
        print(f"❌ Failed to run spider {spider_name}")
        sys.exit(1)
