from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import json
import os
import shutil
from functools import wraps
from datetime import datetime, timedelta
import subprocess
import glob

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Generate a random secret key for sessions
app.permanent_session_lifetime = timedelta(hours=8)  # Default session lifetime

# Path to config file
# CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
# CONFIG_TEMPLATE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config-template.json')
CONFIG_PATH = '/opt/n-central-data-grabber/config.json'
CONFIG_TEMPLATE_PATH = '/opt/n-central-data-grabber/config-template.json'

def load_config():
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=2)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        
        # Check if session has expired
        if 'last_activity' in session:
            config = load_config()
            timeout_minutes = config.get('web-server', {}).get('session-timeout', 480)  # Default 8 hours
            last_activity = datetime.fromisoformat(session['last_activity'])
            if datetime.now() - last_activity > timedelta(minutes=timeout_minutes):
                session.clear()
                return redirect(url_for('login'))
        
        # Update last activity time
        session['last_activity'] = datetime.now().isoformat()
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        try:
            config = load_config()
            web_creds = config.get('web-server', {})
            stored_username = web_creds.get('username')
            stored_password = web_creds.get('password')
            
            if username == stored_username and password == stored_password:
                session.permanent = True  # Enable session expiration
                session['logged_in'] = True
                session['last_activity'] = datetime.now().isoformat()
                # Set session lifetime from config
                timeout_minutes = web_creds.get('session-timeout', 480)  # Default 8 hours
                app.permanent_session_lifetime = timedelta(minutes=timeout_minutes)
                return redirect(url_for('index'))
            else:
                return render_template('login.html', error='Invalid credentials')
        except Exception as e:
            return render_template('login.html', error='Configuration error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
@login_required
def dashboard():
    service_running = get_service_status()
    runs_completed, runs_failed = get_log_stats()
    last_run_time, last_run_success = get_last_run_info()
    recent_logs = read_logs('recent')
    error_logs = read_logs('error')

    return render_template('dashboard.html',
                         service_running=service_running,
                         runs_completed=runs_completed,
                         runs_failed=runs_failed,
                         last_run_time=last_run_time,
                         last_run_success=last_run_success,
                         recent_logs=recent_logs,
                         error_logs=error_logs)

@app.route('/config')
@login_required
def config_page():
    return render_template('index.html')

@app.route('/api/config', methods=['GET', 'POST'])
@login_required
def config_api():
    if request.method == 'GET':
        try:
            with open(CONFIG_PATH, 'r') as f:
                return jsonify(json.load(f))
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    elif request.method == 'POST':
        try:
            config_data = request.get_json()
            with open(CONFIG_PATH, 'w') as f:
                json.dump(config_data, f, indent=2)
            return jsonify({'message': 'Configuration saved successfully'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@app.route('/docs')
@login_required
def docs():
    return render_template('docs.html')

@app.route('/api/config/<path:section>', methods=['GET', 'POST'])
@login_required
def config_section(section):
    try:
        with open(CONFIG_PATH, 'r') as f:
            config = json.load(f)
            
        if request.method == 'GET':
            # Navigate to the section
            sections = section.split('/')
            current = config
            for s in sections:
                if s in current:
                    current = current[s]
                else:
                    return jsonify({"error": "Section not found"}), 404
            return jsonify(current)
            
        elif request.method == 'POST':
            # Update the section
            data = request.json
            sections = section.split('/')
            current = config
            for s in sections[:-1]:
                if s in current:
                    current = current[s]
                else:
                    return jsonify({"error": "Section not found"}), 404
            
            current[sections[-1]] = data
            with open(CONFIG_PATH, 'w') as f:
                json.dump(config, f, indent=2)
            return jsonify({"status": "success"})
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/reset_config', methods=['POST'])
@login_required
def reset_config():
    try:
        # Copy config-template.json to config.json
        shutil.copy2(CONFIG_TEMPLATE_PATH, CONFIG_PATH)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def get_service_status():
    try:
        result = subprocess.run(['systemctl', 'is-active', 'datamonitor.service'], 
                              capture_output=True, text=True)
        return result.stdout.strip() == 'active'
    except Exception:
        return False

def get_log_stats():
    try:
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        log_path = os.path.join(root_dir, 'logs/log_files/completed.log')
        with open(log_path, 'r') as f:
            lines = f.readlines()
            completed_runs = int(lines[0].split(': ')[1].strip())
            failed_runs = int(lines[1].split(': ')[1].strip())
            return completed_runs, failed_runs
    except Exception as e:
        return 0, 0

def get_last_run_info():
    try:
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        log_dir = os.path.join(root_dir, 'logs/log_files')
        log_files = glob.glob(os.path.join(log_dir, 'log.log*'))
        if not log_files:
            return datetime.now().strftime('%Y-%m-%d %H:%M:%S'), False

        latest_log = max(log_files, key=os.path.getmtime)
        with open(latest_log, 'r') as f:
            lines = f.readlines()
            # Look for the loop end message
            for line in reversed(lines):
                if 'Loop ended on' in line:
                    parts = line.strip().split(' - ', 3)
                    if len(parts) >= 4:
                        _, timestamp, _, message = parts
                        # Extract the end time from the message
                        end_time = message.split('Loop ended on ')[1].strip()
                        return end_time, True
            # If no loop end found, use the last line
            if lines:
                last_line = lines[-1]
                success = 'ERROR' not in last_line.upper()
                timestamp = ' '.join(last_line.split()[:2])
                return timestamp, success
    except Exception as e:
        pass
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S'), False

def read_logs(log_type='recent', num_lines=50):
    try:
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        log_dir = os.path.join(root_dir, 'logs/log_files')
        if log_type == 'error':
            log_file = os.path.join(log_dir, 'error.log')
        else:
            log_file = os.path.join(log_dir, 'log.log')

        if not os.path.exists(log_file):
            return []

        with open(log_file, 'r') as f:
            lines = f.readlines()[-num_lines:]
            logs = []
            for line in lines:
                # Example format: [utils.py Line: 59 ] - 2024-10-30 13:40:26,196 - INFO - Total runs: 24
                if ' - ' in line:
                    parts = line.strip().split(' - ', 3)
                    if len(parts) >= 4:
                        file_info, timestamp, level, message = parts
                        # Clean up the level
                        level = level.strip().lower()
                        if level not in ['info', 'warning', 'error']:
                            if 'ERROR' in level.upper():
                                level = 'error'
                            elif 'WARNING' in level.upper():
                                level = 'warning'
                            else:
                                level = 'info'
                        log_entry = {
                            'message': message.strip(),
                            'level': level,
                            'timestamp': timestamp.strip(),
                            'file': file_info.strip('[]').strip()
                        }
                        logs.append(log_entry)
            return logs
    except Exception as e:
        return []

@app.route('/api/status')
@login_required
def get_status():
    service_running = get_service_status()
    runs_completed, runs_failed = get_log_stats()
    last_run_time, last_run_success = get_last_run_info()
    
    return jsonify({
        'is_running': service_running,
        'completed_runs': runs_completed,
        'failed_runs': runs_failed,
        'last_run_time': last_run_time,
        'last_run_status': 'Success' if last_run_success else 'Failed'
    })

@app.route('/api/logs')
@login_required
def get_all_logs():
    recent_logs = read_logs('recent')
    error_logs = read_logs('error')
    return jsonify({
        'recent_logs': recent_logs,
        'error_logs': error_logs
    })

@app.route('/api/service/start', methods=['POST'])
@login_required
def start_service():
    try:
        subprocess.run(['sudo', 'service', 'datamonitor', 'start'], 
                      check=True, capture_output=True)
        return jsonify({'success': True})
    except subprocess.CalledProcessError as e:
        return jsonify({
            'success': False, 
            'error': e.stderr.decode() if e.stderr else 'Failed to start service'
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=False) 
