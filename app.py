import os
import json
import subprocess
import threading
import time
import sys
from pathlib import Path
from flask import Flask, jsonify, render_template, Response, stream_with_context, send_file
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Run environment check on startup
try:
    import check_environment
    check_environment.check_environment()
except ImportError:
    print("Warning: check_environment.py not found, skipping environment check")

app = Flask(__name__, static_folder='static')

# Store logs for display
scraper_logs = []
is_running = False

# List of available spiders
SPIDERS = [
    "dekkjahollin",
    "klettur",
    "mitra",
    "n1",
    "nesdekk", 
    "dekkjasalan"
]

# Database connection placeholder - will be implemented later
db_connection = None

# Initialize database connection when needed
def init_db_connection():
    global db_connection
    # Uncomment this code when ready to use the database
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        from sqlalchemy import create_engine
        db_connection = create_engine(db_url)

@app.route('/')
def index():
    return render_template('index.html', spiders=SPIDERS)

@app.route('/healthz')
def health_check():
    return jsonify({"status": "healthy"}), 200

def run_specific_spider(spider_name):
    global scraper_logs
    
    # First check if the spider file exists
    script_dir = os.path.dirname(os.path.abspath(__file__))
    spiders_dir = os.path.join(script_dir, 'Leita', 'spiders')
    spider_file = os.path.join(spiders_dir, f"{spider_name}.py")
    
    # Show path information for debugging
    scraper_logs.append(f"Looking for spider file: {spider_file}")
    
    # List all files in the Leita/spiders directory for debugging
    if os.path.exists(spiders_dir):
        files = os.listdir(spiders_dir)
        scraper_logs.append(f"Files in {spiders_dir}: {', '.join(files)}")
    else:
        scraper_logs.append(f"Spider directory doesn't exist: {spiders_dir}")
    
    # Try to ensure the spider file is available
    if not os.path.exists(spider_file):
        scraper_logs.append(f"Spider file {spider_name}.py not found. Trying to fix...")
        try:
            # Try the copy_spiders script first
            copy_script = os.path.join(script_dir, "copy_spiders.py")
            if os.path.exists(copy_script):
                scraper_logs.append(f"Running {copy_script}...")
                proc = subprocess.run(
                    [sys.executable, copy_script],
                    capture_output=True,
                    text=True,
                    check=False
                )
                scraper_logs.append(f"copy_spiders output: {proc.stdout}")
                if proc.stderr:
                    scraper_logs.append(f"copy_spiders error: {proc.stderr}")
        except Exception as e:
            scraper_logs.append(f"Error running copy_spiders.py: {str(e)}")
    
    # Check if we now have the spider file
    if os.path.exists(spider_file):
        scraper_logs.append(f"✓ Found spider file: {spider_file}")
    else:
        scraper_logs.append(f"✗ Spider file still not found. Will use existing data.")
    
    # Create the output file path
    output_file = os.path.join(script_dir, f"{spider_name}.json")
    scraper_logs.append(f"Output will go to: {output_file}")
    
    # If we have the spider file, try to run it
    if os.path.exists(spider_file):
        # Try direct runner first
        direct_runner = os.path.join(script_dir, "run_spider_direct.py")
        if os.path.exists(direct_runner):
            scraper_logs.append(f"Running spider with direct runner...")
            cmd = [
                sys.executable,
                direct_runner,
                spider_name,
                output_file
            ]
            
            try:
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )
                
                for line in iter(process.stdout.readline, ''):
                    scraper_logs.append(line.rstrip())
                
                process.stdout.close()
                process.wait()
                
                if process.returncode == 0:
                    scraper_logs.append(f"✅ Spider {spider_name} completed successfully")
                    return True
                else:
                    scraper_logs.append(f"⚠️ Direct runner failed with code {process.returncode}")
            except Exception as e:
                scraper_logs.append(f"⚠️ Error running direct runner: {str(e)}")
        
        # Fall back to scrapy command
        try:
            # Change to the Leita directory
            current_dir = os.getcwd()
            leita_dir = os.path.join(script_dir, "Leita")
            os.chdir(leita_dir)
            scraper_logs.append(f"Changed directory to: {os.getcwd()}")
            
            cmd = [
                'scrapy', 'crawl', 
                spider_name, 
                '-O', output_file
            ]
            scraper_logs.append(f"Running command: {' '.join(cmd)}")
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            for line in iter(process.stdout.readline, ''):
                scraper_logs.append(line.rstrip())
            
            process.stdout.close()
            exit_code = process.wait()
            
            # Change back to original directory
            os.chdir(current_dir)
            
            if exit_code == 0:
                scraper_logs.append(f"✅ Spider {spider_name} completed successfully")
                return True
            else:
                scraper_logs.append(f"⚠️ Spider failed with exit code {exit_code}")
        except Exception as e:
            scraper_logs.append(f"❌ Error running spider: {str(e)}")
            try:
                # Change back to original directory
                os.chdir(current_dir)
            except:
                pass
    
    # If we get here, check if we already have some data for this spider
    existing_json = os.path.join(script_dir, f"{spider_name}.json")
    if os.path.exists(existing_json):
        scraper_logs.append(f"Using existing data from {existing_json}")
        return True
    
    scraper_logs.append(f"No data available for {spider_name}")
    return False

@app.route('/run-spider/<spider_name>')
def run_spider(spider_name):
    global is_running, scraper_logs
    
    if is_running:
        return jsonify({"status": "error", "message": "A spider is already running"}), 400
    
    if spider_name not in SPIDERS:
        return jsonify({"status": "error", "message": "Invalid spider name"}), 400
    
    # Clear previous logs
    scraper_logs = []
    is_running = True
    
    def run_process():
        global is_running
        try:
            scraper_logs.append(f"Starting spider: {spider_name}")
            run_specific_spider(spider_name)
        finally:
            is_running = False
    
    threading.Thread(target=run_process).start()
    return jsonify({"status": "success", "message": f"Spider {spider_name} started"})

@app.route('/run-scrapers')
def run_scrapers():
    global is_running, scraper_logs
    
    if is_running:
        return jsonify({"status": "error", "message": "Scrapers already running"}), 400
    
    # Clear previous logs
    scraper_logs = []
    is_running = True
    
    # Run the scrapers in a separate thread
    def run_process():
        global is_running, scraper_logs
        try:
            # Run each spider in sequence
            for spider_name in SPIDERS:
                scraper_logs.append(f"Starting spider: {spider_name}")
                success = run_specific_spider(spider_name)
                if not success:
                    scraper_logs.append(f"⚠️ Failed to run spider: {spider_name}")
                    
            # Try to merge the results if we have at least some data
            merge_script = os.path.join(os.path.dirname(__file__), "Leita", "merge_tires.py")
            if os.path.exists(merge_script):
                scraper_logs.append("Running merge script...")
                try:
                    process = subprocess.Popen(
                        [sys.executable, merge_script],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        bufsize=1
                    )
                    
                    for line in iter(process.stdout.readline, ''):
                        scraper_logs.append(line.rstrip())
                    
                    process.stdout.close()
                    process.wait()
                    
                    if process.returncode == 0:
                        scraper_logs.append("✅ Merge completed successfully")
                    else:
                        scraper_logs.append(f"⚠️ Merge script exited with code {process.returncode}")
                except Exception as e:
                    scraper_logs.append(f"❌ Error running merge script: {str(e)}")
            
            scraper_logs.append("All scrapers completed")
            
        except Exception as e:
            scraper_logs.append(f"Error running scrapers: {str(e)}")
        finally:
            is_running = False
    
    threading.Thread(target=run_process).start()
    return jsonify({"status": "success", "message": "Scrapers started"})

@app.route('/logs')
def get_logs():
    def generate():
        global scraper_logs, is_running
        
        # Keep track of the last position in the logs we've sent
        last_sent_index = 0
        
        # Send initial data
        yield "data: " + json.dumps({
            "logs": scraper_logs, 
            "running": is_running
        }) + "\n\n"
        
        # Send updates every 5 seconds
        while True:
            # Sleep to avoid consuming too much CPU
            time.sleep(5)
            
            # Check if there are new logs
            if len(scraper_logs) > last_sent_index:
                new_logs = scraper_logs[last_sent_index:]
                last_sent_index = len(scraper_logs)
                yield "data: " + json.dumps({
                    "logs": new_logs, 
                    "running": is_running
                }) + "\n\n"
            else:
                # Send a heartbeat even if no new logs
                yield "data: " + json.dumps({
                    "logs": [], 
                    "running": is_running,
                    "heartbeat": True
                }) + "\n\n"
    
    return Response(stream_with_context(generate()), 
                   mimetype="text/event-stream",
                   headers={"Cache-Control": "no-cache", 
                            "Connection": "keep-alive"})

@app.route('/data/<filename>')
def get_data(filename):
    # Update allowed files to match your actual files
    allowed_files = ['combined_tire_data.json', 'n1.json', 'nesdekk.json', 'dekkjahollin.json',
                     'dekkjasalan.json', 'mitra.json', 'klettur.json']
    
    if filename not in allowed_files:
        return jsonify({"error": "File not found"}), 404
    
    try:
        # Check all possible locations for the file
        possible_paths = [
            os.path.join(os.path.dirname(__file__), filename),  # Root directory
            os.path.join(os.path.dirname(__file__), 'Leita', filename),  # Leita subdirectory
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                print(f"Found file at {path}")
                # For larger files, it's more efficient to send the file directly
                return send_file(path, mimetype='application/json')
            
        return jsonify({"error": "File not found"}), 404
    except Exception as e:
        print(f"Error serving file {filename}: {str(e)}")
        return jsonify({"error": f"Error serving file: {str(e)}"}), 500

@app.route('/db-status')
def db_status():
    if not db_connection:
        init_db_connection()
    
    if db_connection:
        return jsonify({"status": "connected"})
    else:
        return jsonify({"status": "not connected", "message": "Database connection not initialized"}), 503

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
