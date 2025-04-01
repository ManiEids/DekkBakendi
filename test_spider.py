#!/usr/bin/env python
import os
import sys
import subprocess

def test_spider(spider_name):
    """Test a single spider with verbose output"""
    print(f"🔍 Testing spider: {spider_name}")
    print(f"Current directory: {os.getcwd()}")
    
    cmd = ['scrapy', 'list']
    print(f"Checking available spiders: {' '.join(cmd)}")
    
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE, 
        stderr=subprocess.STDOUT,
        text=True
    )
    
    for line in iter(process.stdout.readline, ''):
        print(line, end='')
    
    process.stdout.close()
    process.wait()
    
    # Now try to run the spider
    cmd = ['scrapy', 'crawl', spider_name, '-o', f"{spider_name}_test.json"]
    print(f"\nRunning spider: {' '.join(cmd)}")
    
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE, 
        stderr=subprocess.STDOUT,
        text=True
    )
    
    for line in iter(process.stdout.readline, ''):
        print(line, end='')
    
    process.stdout.close()
    exit_code = process.wait()
    
    if exit_code == 0:
        print(f"✅ Spider {spider_name} completed successfully")
        return True
    else:
        print(f"❌ Spider {spider_name} failed with exit code {exit_code}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_spider.py <spider_name>")
        sys.exit(1)
    
    spider_name = sys.argv[1]
    success = test_spider(spider_name)
    
    sys.exit(0 if success else 1)
