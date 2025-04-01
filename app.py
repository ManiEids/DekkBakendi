import os
import json
import subprocess
import threading
from flask import Flask, jsonify, render_template, Response, stream_with_context
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder='static')

# Store logs for display
scraper_logs = []
is_running = False

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
    return render_template('index.html')

@app.route('/healthz')
def health_check():
    return jsonify({"status": "healthy"}), 200

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
            # Look for run_all.py in multiple possible locations
            possible_paths = [
                "run_all.py",
                "Leita/run_all.py",
                os.path.join(os.path.dirname(__file__), "Leita", "run_all.py")
            ]
            
            run_script = None
            for path in possible_paths:
                if os.path.exists(path):
                    run_script = path
                    scraper_logs.append(f"Found run_all.py at: {path}")
                    break
            
            if not run_script:
                scraper_logs.append("Error: run_all.py not found")
                return
            
            process = subprocess.Popen(
                ['python', run_script], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            for line in iter(process.stdout.readline, ''):
                scraper_logs.append(line)
            
            process.stdout.close()
            process.wait()
        finally:
            is_running = False
    
    threading.Thread(target=run_process).start()
    return jsonify({"status": "success", "message": "Scrapers started"})

@app.route('/logs')
def get_logs():
    def generate():
        global scraper_logs
        # Return current logs first
        yield "data: " + json.dumps({"logs": scraper_logs, "running": is_running}) + "\n\n"
        
        # Stream new logs as they come in
        previous_log_length = len(scraper_logs)
        while True:
            if len(scraper_logs) > previous_log_length:
                new_logs = scraper_logs[previous_log_length:]
                previous_log_length = len(scraper_logs)
                yield "data: " + json.dumps({"logs": new_logs, "running": is_running}) + "\n\n"
    
    return Response(stream_with_context(generate()), mimetype="text/event-stream")

@app.route('/data/<filename>')
def get_data(filename):
    allowed_files = ['combined_tire_data.json', 'n1.json', 'nesdekk.json', 'dekkjahollin.json',
                     'dekkjahusid.json', 'max1.json', 'hjolbardasalan.json']
    
    if filename not in allowed_files:
        return jsonify({"error": "File not found"}), 404
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify(data)
    except FileNotFoundError:
        return jsonify({"error": "File not found"}), 404
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON file"}), 500

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
