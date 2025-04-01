#!/usr/bin/env python
import os
import sys
import importlib
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def run_spider(spider_name, output_file):
    # Import the spider module
    try:
        print(f"Looking for spider module: Leita.spiders.{spider_name}")
        
        # Try to import the spider module dynamically
        module = importlib.import_module(f"Leita.spiders.{spider_name}")
        print(f"Successfully imported module for {spider_name}")
        
        # Print available attributes to help debug
        print(f"Available attributes in module: {dir(module)}")
        
        # Find the spider class in the module
        spider_cls = None
        for obj_name in dir(module):
            obj = getattr(module, obj_name)
            try:
                if hasattr(obj, 'name') and getattr(obj, 'name') == spider_name:
                    spider_cls = obj
                    break
            except:
                continue
        
        if not spider_cls:
            # Try to find any class with a 'name' attribute
            for obj_name in dir(module):
                obj = getattr(module, obj_name)
                try:
                    if hasattr(obj, 'name'):
                        print(f"Found class with name attribute: {obj_name}, name={obj.name}")
                        if spider_cls is None:  # Take the first one if exact match not found
                            spider_cls = obj
                except:
                    continue
        
        if not spider_cls:
            print(f"❌ Could not find spider class for {spider_name}")
            return False
            
        print(f"Using spider class: {spider_cls.__name__}")
        
        # Configure and run the spider
        settings = get_project_settings()
        settings.set('LOG_LEVEL', 'INFO')
        process = CrawlerProcess(settings)
        process.crawl(spider_cls, output=output_file)
        print(f"Starting crawler process for {spider_name}...")
        process.start()  # This blocks until the crawl is finished
        print(f"Crawler process for {spider_name} completed")
        
        # Verify the output file was created
        if os.path.exists(output_file):
            print(f"Output file created: {output_file}")
            return True
        else:
            print(f"Output file not created: {output_file}")
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
    else:
        print(f"❌ Failed to run spider {spider_name}")
        sys.exit(1)
