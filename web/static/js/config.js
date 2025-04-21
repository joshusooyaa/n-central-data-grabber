// Configuration state
let config = {};
const sensitiveFields = [
    'api-jwt',
    'client-secret',
    'password',
    'api-token',
    'expires'
];

// DOM Elements
const saveBtn = document.getElementById('saveBtn');
const refreshBtn = document.getElementById('refreshBtn');
const addOrgBtn = document.getElementById('addOrgBtn');
const notification = document.getElementById('notification');

// Tab functionality
document.querySelectorAll('.tab-btn').forEach(button => {
    button.addEventListener('click', () => {
        // Remove active class from all buttons and panes
        document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
        document.querySelectorAll('.tab-pane').forEach(pane => pane.classList.remove('active'));
        
        // Add active class to clicked button and corresponding pane
        button.classList.add('active');
        document.getElementById(button.dataset.tab).classList.add('active');
    });
});

// Load configuration
async function loadConfig() {
    try {
        const response = await fetch('/api/config');
        if (!response.ok) throw new Error('Failed to load configuration');
        
        config = await response.json();
        renderConfig();
    } catch (error) {
        showNotification('Error loading configuration: ' + error.message, 'error');
    }
}

// Render configuration
function renderConfig() {
    renderAPIConfig();
    renderDBConfig();
    renderOrgConfig();
    renderLoggingConfig();
    renderMicrosoftConfig();
    renderMonitorConfig();
}

// Render API Configuration
function renderAPIConfig() {
    const container = document.getElementById('api-config');
    container.innerHTML = '';
    
    const apiConfig = config.API || {};
    const rows = [
        { key: 'expires', value: apiConfig.expires, description: 'API token expiration time' },
        { key: 'api-jwt', value: apiConfig['api-jwt'], description: 'API JWT token', sensitive: true },
        { key: 'api-token-refresh-offset', value: apiConfig['api-token-refresh-offset'], description: 'Token refresh offset in minutes' },
        { key: 'base-url', value: apiConfig['api-endpoints']?.['base-url'], description: 'Base URL for API endpoints' }
    ];
    
    rows.forEach(row => {
        container.appendChild(createConfigRow(row));
    });
}

// Render Database Configuration
function renderDBConfig() {
    const container = document.getElementById('db-config');
    container.innerHTML = '';
    
    const dbConfig = config.DB || {};
    const hostConfig = dbConfig.host || {};
    
    const rows = [
        { key: 'host', value: hostConfig.ip, description: 'Database host IP' },
        { key: 'user', value: hostConfig.user, description: 'Database username' },
        { key: 'password', value: hostConfig.password, description: 'Database password', sensitive: true },
        { key: 'database', value: hostConfig.database, description: 'Database name' }
    ];
    
    rows.forEach(row => {
        container.appendChild(createConfigRow(row));
    });
}

// Render Organization Configuration
function renderOrgConfig() {
    const container = document.getElementById('org-config');
    container.innerHTML = '';
    
    const orgConfig = config['org-abbreviations'] || {};
    
    Object.entries(orgConfig).forEach(([org, abbreviation]) => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><input type="text" value="${org}" class="org-name"></td>
            <td><input type="text" value="${abbreviation}" class="org-abbreviation"></td>
            <td>
                <button class="btn secondary delete-org"><i class="fas fa-trash"></i></button>
            </td>
        `;
        
        row.querySelector('.delete-org').addEventListener('click', () => {
            row.remove();
        });
        
        container.appendChild(row);
    });
}

// Render Logging Configuration
function renderLoggingConfig() {
    const container = document.getElementById('logging-config');
    container.innerHTML = '';
    
    const loggingConfig = config.logging || {};
    
    const rows = [
        { key: 'max-log-size', value: loggingConfig['max-log-size'], description: 'Maximum log file size in MB' },
        { key: 'backup-count', value: loggingConfig['backup-count'], description: 'Number of backup log files to keep' }
    ];
    
    rows.forEach(row => {
        container.appendChild(createConfigRow(row));
    });
}

// Render Microsoft Graph Configuration
function renderMicrosoftConfig() {
    const container = document.getElementById('microsoft-config');
    container.innerHTML = '';
    
    const msConfig = config['microsoft-graph'] || {};
    
    const rows = [
        { key: 'client-id', value: msConfig['client-id'], description: 'Microsoft Graph Client ID' },
        { key: 'client-secret', value: msConfig['client-secret'], description: 'Microsoft Graph Client Secret', sensitive: true },
        { key: 'tenant-id', value: msConfig['tenant-id'], description: 'Microsoft Graph Tenant ID' },
        { key: 'sender', value: msConfig['email-details']?.sender, description: 'Email sender address' },
        { key: 'recipient', value: msConfig['email-details']?.recipient, description: 'Email recipient address' }
    ];
    
    rows.forEach(row => {
        container.appendChild(createConfigRow(row));
    });
}

// Render Monitor Configuration
function renderMonitorConfig() {
    const container = document.getElementById('monitor-config');
    container.innerHTML = '';
    
    const monitorConfig = config.monitor || {};
    
    const rows = [
        { key: 'max-retries', value: monitorConfig['max-retries'], description: 'Maximum number of retry attempts' },
        { key: 'wait-time', value: monitorConfig['wait-time'], description: 'Wait time between retries in seconds' }
    ];
    
    rows.forEach(row => {
        container.appendChild(createConfigRow(row));
    });
}

// Create a configuration row
function createConfigRow({ key, value, description, sensitive = false }) {
    const row = document.createElement('tr');
    const isSensitive = sensitive || sensitiveFields.includes(key);
    
    row.innerHTML = `
        <td>${key}</td>
        <td>
            <input type="${isSensitive ? 'password' : 'text'}" 
                   value="${value || ''}" 
                   data-key="${key}"
                   ${isSensitive ? 'placeholder="••••••••"' : ''}>
        </td>
        <td>${description}</td>
    `;
    
    return row;
}

// Save configuration
async function saveConfig() {
    try {
        // Update config object with form values
        updateConfigFromForm();
        
        const response = await fetch('/api/config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(config)
        });
        
        if (!response.ok) throw new Error('Failed to save configuration');
        
        showNotification('Configuration saved successfully', 'success');
    } catch (error) {
        showNotification('Error saving configuration: ' + error.message, 'error');
    }
}

// Update config object from form values
function updateConfigFromForm() {
    // Update API config
    config.API = config.API || {};
    document.querySelectorAll('#api-config input').forEach(input => {
        const key = input.dataset.key;
        if (key.includes('.')) {
            const [parent, child] = key.split('.');
            config.API[parent] = config.API[parent] || {};
            config.API[parent][child] = input.value;
        } else {
            config.API[key] = input.value;
        }
    });
    
    // Update DB config
    config.DB = config.DB || {};
    config.DB.host = config.DB.host || {};
    document.querySelectorAll('#db-config input').forEach(input => {
        config.DB.host[input.dataset.key] = input.value;
    });
    
    // Update org config
    config['org-abbreviations'] = {};
    document.querySelectorAll('#org-config tr').forEach(row => {
        const name = row.querySelector('.org-name').value;
        const abbreviation = row.querySelector('.org-abbreviation').value;
        if (name && abbreviation) {
            config['org-abbreviations'][name] = abbreviation;
        }
    });
    
    // Update logging config
    config.logging = config.logging || {};
    document.querySelectorAll('#logging-config input').forEach(input => {
        config.logging[input.dataset.key] = parseInt(input.value);
    });
    
    // Update Microsoft Graph config
    config['microsoft-graph'] = config['microsoft-graph'] || {};
    config['microsoft-graph']['email-details'] = config['microsoft-graph']['email-details'] || {};
    document.querySelectorAll('#microsoft-config input').forEach(input => {
        const key = input.dataset.key;
        if (key === 'sender' || key === 'recipient') {
            config['microsoft-graph']['email-details'][key] = input.value;
        } else {
            config['microsoft-graph'][key] = input.value;
        }
    });
    
    // Update monitor config
    config.monitor = config.monitor || {};
    document.querySelectorAll('#monitor-config input').forEach(input => {
        config.monitor[input.dataset.key] = parseInt(input.value);
    });
}

// Show notification
function showNotification(message, type) {
    notification.textContent = message;
    notification.className = `notification ${type}`;
    
    setTimeout(() => {
        notification.style.display = 'none';
    }, 3000);
}

// Add new organization
addOrgBtn.addEventListener('click', () => {
    const container = document.getElementById('org-config');
    const row = document.createElement('tr');
    row.innerHTML = `
        <td><input type="text" class="org-name" placeholder="Organization Name"></td>
        <td><input type="text" class="org-abbreviation" placeholder="Abbreviation"></td>
        <td>
            <button class="btn secondary delete-org"><i class="fas fa-trash"></i></button>
        </td>
    `;
    
    row.querySelector('.delete-org').addEventListener('click', () => {
        row.remove();
    });
    
    container.appendChild(row);
});

// Event Listeners
saveBtn.addEventListener('click', saveConfig);
refreshBtn.addEventListener('click', loadConfig);

// Initial load
loadConfig(); 