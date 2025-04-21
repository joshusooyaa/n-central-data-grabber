from flask import Flask, render_template, request, jsonify
import json
import os
from pathlib import Path

app = Flask(__name__)

# Configuration file path - ensure it points to the root directory
CONFIG_PATH = Path(__file__).parent.parent.absolute() / 'config.json'

# List of sensitive fields that should be masked
SENSITIVE_FIELDS = {
    'API': ['api-jwt', 'expires'],
    'DB': {
        'host': ['password']
    },
    'microsoft-graph': ['client-secret', 'expires']
}

def mask_sensitive_data(config):
    """Mask sensitive data in the configuration."""
    masked_config = config.copy()
    
    # Mask API sensitive fields
    if 'API' in masked_config:
        for field in SENSITIVE_FIELDS['API']:
            if field in masked_config['API']:
                masked_config['API'][field] = '••••••••'
    
    # Mask DB sensitive fields
    if 'DB' in masked_config and 'host' in masked_config['DB']:
        for field in SENSITIVE_FIELDS['DB']['host']:
            if field in masked_config['DB']['host']:
                masked_config['DB']['host'][field] = '••••••••'
    
    # Mask Microsoft Graph sensitive fields
    if 'microsoft-graph' in masked_config:
        for field in SENSITIVE_FIELDS['microsoft-graph']:
            if field in masked_config['microsoft-graph']:
                masked_config['microsoft-graph'][field] = '••••••••'
    
    return masked_config

def load_config():
    """Load the configuration from the config file."""
    if not CONFIG_PATH.exists():
        print(f"Config file not found at: {CONFIG_PATH}")
        return {}
    try:
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config file: {e}")
        return {}

def save_config(config):
    """Save the configuration to the config file."""
    try:
        with open(CONFIG_PATH, 'w') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        print(f"Error saving config file: {e}")
        raise

@app.route('/')
def index():
    """Serve the main configuration interface."""
    return render_template('index.html')

@app.route('/api/config', methods=['GET'])
def get_config():
    """API endpoint to get the current configuration."""
    try:
        config = load_config()
        # Return masked configuration to frontend
        masked_config = mask_sensitive_data(config)
        return jsonify(masked_config)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/config', methods=['POST'])
def update_config():
    """API endpoint to update the configuration."""
    try:
        new_config = request.json
        current_config = load_config()
        
        # For sensitive fields, only update if the value is not masked
        for section, fields in SENSITIVE_FIELDS.items():
            if section in new_config:
                if isinstance(fields, dict):  # Nested structure (like DB)
                    for subsection, subfields in fields.items():
                        if subsection in new_config[section]:
                            for field in subfields:
                                if field in new_config[section][subsection]:
                                    if new_config[section][subsection][field] == '••••••••':
                                        # Keep the original value if the new value is masked
                                        new_config[section][subsection][field] = current_config[section][subsection][field]
                else:  # Direct fields
                    for field in fields:
                        if field in new_config[section]:
                            if new_config[section][field] == '••••••••':
                                # Keep the original value if the new value is masked
                                new_config[section][field] = current_config[section][field]
        
        save_config(new_config)
        return jsonify({'message': 'Configuration updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/flow-chart')
def flow_chart():
    """Serve the system flow chart visualization."""
    return render_template('flow_chart.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 