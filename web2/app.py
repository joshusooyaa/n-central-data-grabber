from flask import Flask, render_template, request, jsonify
import json
import os

app = Flask(__name__)

# Path to config file
CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')

def load_config():
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=2)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/config', methods=['GET', 'POST'])
def config():
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

@app.route('/api/config', methods=['GET'])
def get_config_api():
    return jsonify(load_config())

@app.route('/api/config', methods=['POST'])
def update_config():
    data = request.json
    save_config(data)
    return jsonify({"status": "success"})

@app.route('/api/config/<path:section>', methods=['GET'])
def get_section(section):
    config = load_config()
    sections = section.split('/')
    current = config
    for s in sections:
        if s in current:
            current = current[s]
        else:
            return jsonify({"error": "Section not found"}), 404
    return jsonify(current)

@app.route('/api/config/<path:section>', methods=['POST'])
def update_section(section):
    data = request.json
    config = load_config()
    sections = section.split('/')
    current = config
    for s in sections[:-1]:
        if s in current:
            current = current[s]
        else:
            return jsonify({"error": "Section not found"}), 404
    
    current[sections[-1]] = data
    save_config(config)
    return jsonify({"status": "success"})

if __name__ == '__main__':
    app.run(debug=True) 