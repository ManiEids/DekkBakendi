import os
import json
import subprocess
import threading
import time
import sys
import datetime
import signal
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
running_spider = None

# List of available spiders
SPIDERS = [
    "dekkjahollin",
    "klettur",
    "mitra",
    "n1",
    "nesdekk", 
    "dekkjasalan"
]

# Store file timestamps
file_timestamps = {}

# Database connection placeholder - will be implemented later
db_connection = None

# Define a timeout for spider processes (5 minutes)
SPIDER_TIMEOUT = 300

# Add a dict to track running spider processes
running_processes = {}

# Initialize database connection when needed
def init_db_connection():
    global db_connection
    # Uncomment this code when ready to use the database
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        from sqlalchemy import create_engine
        db_connection = create_engine(db_url)

def update_file_timestamps():
    """Update the timestamps of all known data files"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    files_to_check = ['combined_tire_data.json'] + [f"{spider}.json" for spider in SPIDERS]
    
    for filename in files_to_check:
        filepath = os.path.join(script_dir, filename)
        if os.path.exists(filepath):
            timestamp = datetime.datetime.fromtimestamp(os.path.getmtime(filepath))
            file_timestamps[filename] = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        else:
            file_timestamps[filename] = "Not available"

@app.route('/')
def index():
    update_file_timestamps()
    return render_template('index.html', spiders=SPIDERS, timestamps=file_timestamps, running_spider=running_spider)

@app.route('/healthz')
def health_check():
    return jsonify({"status": "healthy"}), 200

def run_specific_spider(spider_name):
    global scraper_logs, running_spider, running_processes
    
    # Record which spider is currently running
    running_spider = spider_name
    
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
    
    # Set a start time for timeout tracking
    start_time = time.time()
    
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
                # Use preexec_fn on Unix systems to create a new process group
                preexec_fn = os.setsid if hasattr(os, 'setsid') else None
                
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    preexec_fn=preexec_fn
                )
                
                # Store the process ID for potential termination
                running_processes[spider_name] = process.pid
                
                for line in iter(process.stdout.readline, ''):
                    scraper_logs.append(line.rstrip())
                    
                    # Add additional check for completion indicators
                    if "Dumping" in line or "dumping" in line or "items scraped" in line:
                        scraper_logs.append(f"✅ Spider {spider_name} appears to be completing its run")
                    # Log telnet console errors but don't treat them as failures
                    if "AlreadyNegotiating" in line:
                        scraper_logs.append("ℹ️ Telnet console warning (safe to ignore)")
                    
                    # Check for timeout
                    current_time = time.time()
                    if current_time - start_time > SPIDER_TIMEOUT:
                        scraper_logs.append(f"⚠️ Spider {spider_name} timed out after {SPIDER_TIMEOUT} seconds")
                        # Kill the process group on Unix systems
                        try:
                            if hasattr(os, 'killpg'):
                                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                            else:
                                process.terminate()
                        except Exception as e:
                            scraper_logs.append(f"Error terminating process: {str(e)}")
                        
                        # Remove from running processes
                        running_processes.pop(spider_name, None)
                        
                        # Check if any output was produced despite timeout
                        if os.path.exists(output_file):
                            scraper_logs.append(f"✅ Spider {spider_name} produced partial results before timeout")
                            update_file_timestamps()
                            return True
                        return False
                
                process.stdout.close()
                process.wait()
                
                # Remove from running processes
                running_processes.pop(spider_name, None)
                
                if process.returncode == 0:
                    scraper_logs.append(f"✅ Spider {spider_name} completed successfully")
                    # Update timestamps after successful run
                    update_file_timestamps()
                    return True
                else:
                    scraper_logs.append(f"⚠️ Direct runner failed with code {process.returncode}")
            except Exception as e:
                scraper_logs.append(f"⚠️ Error running direct runner: {str(e)}")
                # Remove from running processes in case of exception
                running_processes.pop(spider_name, None)
        
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
                # Update timestamps after successful run
                update_file_timestamps()
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
        # Even when using existing data, update the timestamp information
        update_file_timestamps()
        return True
    
    scraper_logs.append(f"No data available for {spider_name}")
    return False

@app.route('/run-spider/<spider_name>')
def run_spider(spider_name):
    global is_running, scraper_logs, running_spider
    
    if is_running:
        return jsonify({"status": "error", "message": "A spider is already running"}), 400
    
    if spider_name not in SPIDERS:
        scraper_logs.append(f"⚠️ Invalid spider name: {spider_name}")
        return jsonify({"status": "error", "message": "Invalid spider name"}), 400
    
    # Clear previous logs
    scraper_logs = []
    scraper_logs.append(f"🚀 Starting spider: {spider_name}")
    is_running = True
    running_spider = spider_name  # Set the currently running spider
    
    def run_process():
        global is_running, running_spider
        try:
            run_specific_spider(spider_name)
        except Exception as e:
            import traceback
            error_msg = f"Error running spider {spider_name}: {str(e)}\n{traceback.format_exc()}"
            scraper_logs.append(f"❌ {error_msg}")
        finally:
            is_running = False
            running_spider = None  # Clear running spider when done
    
    threading.Thread(target=run_process).start()
    return jsonify({"status": "success", "message": f"Spider {spider_name} started"})

@app.route('/run-scrapers')
def run_scrapers():
    global is_running, scraper_logs, running_spider
    
    if is_running:
        return jsonify({"status": "error", "message": "Scrapers already running"}), 400
    
    # Clear previous logs
    scraper_logs = []
    is_running = True
    running_spider = "all"  # Indicate that all spiders are running
    
    # Run the scrapers in a separate thread
    def run_process():
        global is_running, scraper_logs, running_spider
        try:
            scraper_logs.append("🚀 Starting all scrapers")
            # Run each spider in sequence
            for spider_name in SPIDERS:
                running_spider = spider_name  # Update which spider is currently running
                scraper_logs.append(f"Starting spider: {spider_name}")
                success = run_specific_spider(spider_name)
                if not success:
                    scraper_logs.append(f"⚠️ Failed to run spider: {spider_name}")
            
            # Try to merge the results if we have at least some data
            running_spider = "merging"  # Show that we're in the merging phase
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
                        # Update timestamps after successful merge
                        update_file_timestamps()
                    else:
                        scraper_logs.append(f"⚠️ Merge script exited with code {process.returncode}")
                except Exception as e:
                    scraper_logs.append(f"❌ Error running merge script: {str(e)}")
                    
            scraper_logs.append("All scrapers completed")
        except Exception as e:
            scraper_logs.append(f"Error running scrapers: {str(e)}")
        finally:
            is_running = False
            running_spider = None
    
    threading.Thread(target=run_process).start()
    return jsonify({"status": "success", "message": "Scrapers started"})

@app.route('/cancel')
def cancel_running_spiders():
    global running_processes, is_running, scraper_logs
    
    if not is_running:
        return jsonify({"status": "error", "message": "No spiders are running"}), 400
    
    try:
        # Terminate all running processes
        for spider_name, pid in list(running_processes.items()):
            try:
                scraper_logs.append(f"Cancelling spider: {spider_name} (PID: {pid})")
                if hasattr(os, 'killpg'):
                    os.killpg(os.getpgid(pid), signal.SIGTERM)
                else:
                    os.kill(pid, signal.SIGTERM)
                running_processes.pop(spider_name, None)
            except ProcessLookupError:
                scraper_logs.append(f"Process {pid} for {spider_name} not found")
                running_processes.pop(spider_name, None)
            except Exception as e:
                scraper_logs.append(f"Error cancelling {spider_name}: {str(e)}")
        
        is_running = False
        running_spider = None
        scraper_logs.append("All running spiders cancelled")
        return jsonify({"status": "success", "message": "Cancelled all running spiders"})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error: {str(e)}"}), 500

@app.route('/logs')
def get_logs():
    def generate():
        global scraper_logs, is_running, running_spider
        
        # Keep track of the last position in the logs we've sent
        last_sent_index = 0
        
        # Send initial data including timestamps and running status
        update_file_timestamps()
        yield "data: " + json.dumps({
            "logs": scraper_logs, 
            "running": is_running,
            "timestamps": file_timestamps,
            "running_spider": running_spider
        }) + "\n\n"
        
        # Send updates every 5 seconds
        while True:
            # Sleep to avoid consuming too much CPU
            time.sleep(5)
            
            # Check if there are new logs
            if len(scraper_logs) > last_sent_index:
                new_logs = scraper_logs[last_sent_index:]
                last_sent_index = len(scraper_logs)
                
                # Update timestamps before sending
                update_file_timestamps()
                yield "data: " + json.dumps({
                    "logs": new_logs, 
                    "running": is_running,
                    "timestamps": file_timestamps,
                    "running_spider": running_spider
                }) + "\n\n"
            else:
                # Send a heartbeat even if no new logs, with updated timestamps
                update_file_timestamps()
                yield "data: " + json.dumps({
                    "logs": [], 
                    "running": is_running,
                    "timestamps": file_timestamps,
                    "running_spider": running_spider,
                    "heartbeat": True
                }) + "\n\n"
            time.sleep(3)
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
                # Update the timestamp before serving the file
                update_file_timestamps()
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

@app.route('/update-database')
def update_database():
    """Update Neon database with the latest tire data"""
    try:
        from database import TireDatabase
        
        # Create new database connection
        db = TireDatabase()
        
        # Test connection and import data
        success, message = db.import_from_json()
        
        if success:
            return jsonify({"status": "success", "message": message})
        else:
            return jsonify({"status": "error", "message": message}), 500
    except Exception as e:
        import traceback
        return jsonify({
            "status": "error", 
            "message": f"Database error: {str(e)}",
            "traceback": traceback.format_exc()
        }), 500

@app.route('/debug')
def debug_info():
    """Return debug information about the application state"""
    info = {
        "environment": {
            "is_running": is_running,
            "running_spider": running_spider,
            "log_count": len(scraper_logs),
            "recent_logs": scraper_logs[-10:] if scraper_logs else [],
            "spiders": SPIDERS,
            "file_timestamps": file_timestamps,
            "environment_variables": {k: v for k, v in os.environ.items() if k in ['PORT', 'DATABASE_URL', 'PRODUCTION']}
        },
        "working_directory": os.getcwd(),
        "script_directory": os.path.dirname(os.path.abspath(__file__)),
        "python_version": sys.version
    }
    return jsonify(info)

@app.route('/clear-logs')
def clear_logs():
    """Clear all logs"""
    global scraper_logs
    scraper_logs = ["Logs cleared"]
    return jsonify({"status": "success", "message": "Logs cleared"})

@app.route('/test')
def test_endpoint():
    return jsonify({"status": "success", "message": "Server is responding correctly"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
