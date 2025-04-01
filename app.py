import os
import json
import subprocess
import threading
from flask import Flask, jsonify, render_template, Response, stream_with_context

app = Flask(__name__, static_folder='static')

# Store logs for display
scraper_logs = []
is_running = False

@app.route('/')
def index():
    return render_template('index.html')

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
            process = subprocess.Popen(
                ['python', 'run_all.py'], 
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
