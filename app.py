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
    
    if is_running:g
        return jsonify({"status": "error", "message": "A spider is already running"}), 400
    
    if spider_name not in SPIDERS:
        return jsonify({"status": "error", "message": "Invalid spider name"}), 400e}")
        return jsonify({"status": "error", "message": "A spider is already running"}), 400
    # Clear previous logs
    scraper_logs = []t in SPIDERS:
    is_running = Trueappend(f"⚠️ Invalid spider name: {spider_name}")
    running_spider = spider_name  # Set the currently running spiderr name"}), 400
    
    def run_process():ogs and add initial logs
        global is_running, running_spider
        try:logs.append(f"🚀 Starting spider: {spider_name}")
            scraper_logs.append(f"Starting spider: {spider_name}")
            run_specific_spider(spider_name)currently running spider
        finally:
            is_running = False
            running_spider = None  # Clear running spider when done
        try:
    threading.Thread(target=run_process).start()
    return jsonify({"status": "success", "message": f"Spider {spider_name} started"})
            import traceback
@app.route('/run-scrapers')rror running spider {spider_name}: {str(e)}\n{traceback.format_exc()}"
def run_scrapers():rror_msg)
    global is_running, scraper_logs, running_spider
        finally:
    if is_running:ning = False
        return jsonify({"status": "error", "message": "Scrapers already running"}), 400
    
    # Clear previous logset=run_process).start()
    scraper_logs = []status": "success", "message": f"Spider {spider_name} started"})
    is_running = True
    running_spider = "all"  # Indicate that all spiders are running
    run_scrapers():
    # Run the scrapers in a separate threadg_spider
    def run_process():
        global is_running, scraper_logs, running_spider
        try:eceived request to run all scrapers")
            # Run each spider in sequence
            for spider_name in SPIDERS:
                running_spider = spider_name  # Update which spider is currently running
                scraper_logs.append(f"Starting spider: {spider_name}")y running"}), 400
                success = run_specific_spider(spider_name)
                if not success:dd initial logs
                    scraper_logs.append(f"⚠️ Failed to run spider: {spider_name}")
                    end("🚀 Starting all scrapers")
            # Try to merge the results if we have at least some data
            running_spider = "merging"  # Show that we're in the merging phase
            merge_script = os.path.join(os.path.dirname(__file__), "Leita", "merge_tires.py")
            if os.path.exists(merge_script):
                scraper_logs.append("Running merge script...")
                try:nning, scraper_logs, running_spider
                    process = subprocess.Popen(
                        [sys.executable, merge_script],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,pdate which spider is currently running
                        text=True,d(f"Starting spider: {spider_name}")
                        bufsize=1cific_spider(spider_name)
                    )t success:
                    scraper_logs.append(f"⚠️ Failed to run spider: {spider_name}")
                    for line in iter(process.stdout.readline, ''):
                        scraper_logs.append(line.rstrip()) some data
                    spider = "merging"  # Show that we're in the merging phase
                    process.stdout.close().path.dirname(__file__), "Leita", "merge_tires.py")
                    process.wait()e_script):
                    per_logs.append("Running merge script...")
                    if process.returncode == 0:
                        scraper_logs.append("✅ Merge completed successfully")
                        # Update timestamps after successful merge
                        update_file_timestamps()
                    else:tderr=subprocess.STDOUT,
                        scraper_logs.append(f"⚠️ Merge script exited with code {process.returncode}")
                except Exception as e:
                    scraper_logs.append(f"❌ Error running merge script: {str(e)}")
                    
            scraper_logs.append("All scrapers completed")ine, ''):
                        scraper_logs.append(line.rstrip())
        except Exception as e:
            scraper_logs.append(f"Error running scrapers: {str(e)}")
        finally:    process.wait()
            is_running = False
            running_spider = Noneturncode == 0:
                        scraper_logs.append("✅ Merge completed successfully")
    threading.Thread(target=run_process).start()r successful merge
    return jsonify({"status": "success", "message": "Scrapers started"})
                    else:
@app.route('/cancel')   scraper_logs.append(f"⚠️ Merge script exited with code {process.returncode}")
def cancel_running_spiders():ion as e:
    global running_processes, is_running, scraper_logsing merge script: {str(e)}")
            
    if not is_running:gs.append("All scrapers completed")
        return jsonify({"status": "error", "message": "No spiders are running"}), 400
        except Exception as e:
    try:    import traceback
        # Terminate all running processescrapers: {str(e)}\n{traceback.format_exc()}"
        for spider_name, pid in list(running_processes.items()):
            try:per_logs.append(f"❌ {error_msg}")
                scraper_logs.append(f"Cancelling spider: {spider_name} (PID: {pid})")
                if hasattr(os, 'killpg'):
                    os.killpg(os.getpgid(pid), signal.SIGTERM)
                else:
                    os.kill(pid, signal.SIGTERM)
                running_processes.pop(spider_name, None)apers started"})
            except ProcessLookupError:
                scraper_logs.append(f"Process {pid} for {spider_name} not found")
                running_processes.pop(spider_name, None)
            except Exception as e:unning, scraper_logs
                scraper_logs.append(f"Error cancelling {spider_name}: {str(e)}")
        ot is_running:
        is_running = Falsetatus": "error", "message": "No spiders are running"}), 400
        running_spider = None
        scraper_logs.append("All running spiders cancelled")
        return jsonify({"status": "success", "message": "Cancelled all running spiders"})
    except Exception as e:id in list(running_processes.items()):
        return jsonify({"status": "error", "message": f"Error: {str(e)}"}), 500
                scraper_logs.append(f"Cancelling spider: {spider_name} (PID: {pid})")
@app.route('/logs')hasattr(os, 'killpg'):
def get_logs():     os.killpg(os.getpgid(pid), signal.SIGTERM)
    def generate():e:
        global scraper_logs, is_running, running_spider
                running_processes.pop(spider_name, None)
        # Keep track of the last position in the logs we've sent
        last_sent_index = 0s.append(f"Process {pid} for {spider_name} not found")
                running_processes.pop(spider_name, None)
        # Send initial data including timestamps and running status
        update_file_timestamps()end(f"Error cancelling {spider_name}: {str(e)}")
        yield "data: " + json.dumps({
            "logs": scraper_logs, 
            "running": is_running,
            "timestamps": file_timestamps,piders cancelled")
            "running_spider": running_spider "message": "Cancelled all running spiders"})
        }) + "\n\n"n as e:
        return jsonify({"status": "error", "message": f"Error: {str(e)}"}), 500
        # Send updates every 5 seconds
        while True:
            # Sleep to avoid consuming too much CPU
            time.sleep(5)
            al scraper_logs, is_running, running_spider
            # Check if there are new logs
            if len(scraper_logs) > last_sent_index:
                new_logs = scraper_logs[last_sent_index:]
                last_sent_index = len(scraper_logs)
                ning": is_running,
                # Update timestamps before sending
                update_file_timestamps()ider
                \n"
                yield "data: " + json.dumps({
                    "logs": new_logs, ion in the logs we've sent
                    "running": is_running,
                    "timestamps": file_timestamps,
                    "running_spider": running_spider running status
                }) + "\n\n"mps()
            else:ta: " + json.dumps({
                # Send a heartbeat even if no new logs, with updated timestamps
                update_file_timestamps()
                yield "data: " + json.dumps({
                    "logs": [], nning_spider
                    "running": is_running,
                    "timestamps": file_timestamps,
                    "running_spider": running_spider, better responsiveness)
                    "heartbeat": True
                }) + "\n\n"d consuming too much CPU
            time.sleep(3)
    return Response(stream_with_context(generate()), 
                   mimetype="text/event-stream",
                   headers={"Cache-Control": "no-cache", 
                            "Connection": "keep-alive"})]
                last_sent_index = len(scraper_logs)
@app.route('/data/<filename>')
def get_data(filename):e timestamps before sending
    # Update allowed files to match your actual files
    allowed_files = ['combined_tire_data.json', 'n1.json', 'nesdekk.json', 'dekkjahollin.json',
                     'dekkjasalan.json', 'mitra.json', 'klettur.json']
                    "logs": new_logs, 
    if filename not in allowed_files:ning,
        return jsonify({"error": "File not found"}), 404
                    "running_spider": running_spider
    try:        }) + "\n\n"
        # Check all possible locations for the file
        possible_paths = [eartbeat every 3 seconds even if no new logs
            os.path.join(os.path.dirname(__file__), filename),  # Root directory
            os.path.join(os.path.dirname(__file__), 'Leita', filename),  # Leita subdirectory
        ]           "logs": [], 
                    "running": is_running,
        for path in possible_paths:ile_timestamps,
            if os.path.exists(path):: running_spider,
                print(f"Found file at {path}")
                # Update the timestamp before serving the file
                update_file_timestamps()
                # For larger files, it's more efficient to send the file directly
                return send_file(path, mimetype='application/json')
                   headers={"Cache-Control": "no-cache", 
        return jsonify({"error": "File not found"}), 404
    except Exception as e:
        print(f"Error serving file {filename}: {str(e)}")
        return jsonify({"error": f"Error serving file: {str(e)}"}), 500
    # Update allowed files to match your actual files
@app.route('/db-status')mbined_tire_data.json', 'n1.json', 'nesdekk.json', 'dekkjahollin.json',
def db_status():     'dekkjasalan.json', 'mitra.json', 'klettur.json']
    if not db_connection:
        init_db_connection()ed_files:
        return jsonify({"error": "File not found"}), 404
    if db_connection:
        return jsonify({"status": "connected"})
    else: Check all possible locations for the file
        return jsonify({"status": "not connected", "message": "Database connection not initialized"}), 503
            os.path.join(os.path.dirname(__file__), filename),  # Root directory
@app.route('/update-database')th.dirname(__file__), 'Leita', filename),  # Leita subdirectory
def update_database():
    """Update Neon database with the latest tire data"""
    try:for path in possible_paths:
        from database import TireDatabase
                print(f"Found file at {path}")
        # Create new database connectionefore serving the file
        db = TireDatabase()_timestamps()
                # For larger files, it's more efficient to send the file directly
        # Test connection and import datametype='application/json')
        success, message = db.import_from_json()
        return jsonify({"error": "File not found"}), 404
        if success:n as e:
            return jsonify({"status": "success", "message": message})
        else:n jsonify({"error": f"Error serving file: {str(e)}"}), 500
            return jsonify({"status": "error", "message": message}), 500
    except Exception as e:
        import traceback
        return jsonify({:
            "status": "error", 
            "message": f"Database error: {str(e)}",
            "traceback": traceback.format_exc()
        }), 500jsonify({"status": "connected"})
    else:
@app.route('/debug')tatus": "not connected", "message": "Database connection not initialized"}), 503
def debug_info():
    """Return debug information about the application state"""
    info = {def update_database():



























    app.run(host='0.0.0.0', port=port, debug=False)    port = int(os.environ.get('PORT', 5000))if __name__ == '__main__':    return jsonify({"status": "success", "message": "Logs cleared"})    scraper_logs = ["Logs cleared"]    global scraper_logs    """Clear all logs"""def clear_logs():@app.route('/clear-logs')    return jsonify(info)    }        }                                   if k in ['PORT', 'DATABASE_URL', 'PRODUCTION']}            "environment_variables": {k: v for k, v in os.environ.items()             "script_directory": os.path.dirname(os.path.abspath(__file__)),            "working_directory": os.getcwd(),            "python_version": sys.version,        "environment": {        "file_timestamps": file_timestamps,        "spiders": SPIDERS,        "recent_logs": scraper_logs[-10:] if scraper_logs else [],        "log_count": len(scraper_logs),        "running_spider": running_spider,        "is_running": is_running,    """Update Neon database with the latest tire data"""
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

# Add a simple test route to verify the server is responding
@app.route('/test')
def test_endpoint():
    return jsonify({"status": "success", "message": "Server is responding correctly"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
