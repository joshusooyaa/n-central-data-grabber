// Configuration data structure
let config = {
    API: {
        expires: "",
        "api-jwt": "",
        "api-token-refresh-offset": 10,
        "api-endpoints": {
            "base-url": "",
            auth: {
                "authenticate-endpoint": "auth/authenticate",
                "refresh-endpoint": "auth/refresh"
            },
            devices: {
                endpoint: "devices/",
                "device-services": "service-monitor-status",
                params: {
                    pageSize: "pageSize=-1"
                }
            },
            tasks: {
                endpoint: "appliance-tasks/",
                "data-filter": {
                    "module-names": [],
                    "unwanted-sub-modules": [],
                    "wanted-sub-modules": [],
                    "generic-modules": []
                }
            }
        }
    },
    DB: {
        "db-tables": {},
        "db-columns": {},
        host: {
            ip: "",
            user: "",
            password: "",
            database: ""
        }
    },
    "org-abbreviations": {},
    logging: {
        "max-log-size": 10,
        "backup-count": 5
    },
    "microsoft-graph": {
        "client-id": "",
        "client-secret": "",
        "tenant-id": "",
        "email-details": {
            sender: "",
            subject: "",
            body: "",
            recipient: ""
        },
        expires: ""
    },
    monitor: {
        "max-retries": 5,
        "wait-time": 60
    },
    "script-interval": 300
};

// Initialize the page
document.addEventListener('DOMContentLoaded', function() {
    loadConfig();
    setupEventListeners();
});

// Load configuration from config.json
async function loadConfig() {
    try {
        const response = await fetch('/api/config');
        if (!response.ok) {
            if (response.status === 401) {
                window.location.href = '/login';
                return;
            }
            throw new Error('Failed to load configuration');
        }
        const serverConfig = await response.json();
        
        // Merge server config with default config
        config = { ...config, ...serverConfig };
        
        // Populate forms with the loaded configuration
        populateForms();
        
        // Save to localStorage for offline use
        localStorage.setItem('ncentralConfig', JSON.stringify(config));
    } catch (error) {
        console.error('Error loading configuration:', error);
        // Fallback to localStorage if available
        const savedConfig = localStorage.getItem('ncentralConfig');
        if (savedConfig) {
            config = JSON.parse(savedConfig);
            populateForms();
        }
        showAlert('Error loading configuration. Using cached data.', 'danger');
    }
}

// Populate forms with saved data
function populateForms() {
    // API Configuration
    document.getElementById('api_expires').value = config.API.expires;
    document.getElementById('api_jwt').value = '********'; // Placeholder for secret
    document.getElementById('api_token_refresh_offset').value = config.API["api-token-refresh-offset"];
    document.getElementById('base_url').value = config.API["api-endpoints"]["base-url"];
    document.getElementById('auth_authenticate').value = config.API["api-endpoints"].auth["authenticate-endpoint"];
    document.getElementById('auth_refresh').value = config.API["api-endpoints"].auth["refresh-endpoint"];

    // Device settings
    document.getElementById('device_endpoint').value = config.API["api-endpoints"].devices.endpoint;
    document.getElementById('device_services').value = config.API["api-endpoints"].devices["device-services"];
    document.getElementById('page_size').value = config.API["api-endpoints"].devices.params.pageSize;

    // Task settings
    document.getElementById('task_endpoint').value = config.API["api-endpoints"].tasks.endpoint;

    // Database Configuration
    document.getElementById('db_host').value = config.DB.host.ip;
    document.getElementById('db_user').value = config.DB.host.user;
    document.getElementById('db_password').value = '********'; // Placeholder for secret
    document.getElementById('db_database').value = config.DB.host.database;

    // Logging Configuration
    document.getElementById('max_log_size').value = config.logging["max-log-size"];
    document.getElementById('backup_count').value = config.logging["backup-count"];

    // Microsoft Graph Configuration
    document.getElementById('client_id').value = config["microsoft-graph"]["client-id"];
    document.getElementById('client_secret').value = '********'; // Placeholder for secret
    document.getElementById('tenant_id').value = config["microsoft-graph"]["tenant-id"];
    document.getElementById('graph_expires').value = config["microsoft-graph"].expires;
    document.getElementById('email_sender').value = config["microsoft-graph"]["email-details"].sender;
    document.getElementById('email_subject').value = config["microsoft-graph"]["email-details"].subject;
    document.getElementById('email_body').value = config["microsoft-graph"]["email-details"].body;
    document.getElementById('email_recipient').value = config["microsoft-graph"]["email-details"].recipient;

    // Monitor Configuration
    document.getElementById('max_retries').value = config.monitor["max-retries"];
    document.getElementById('wait_time').value = config.monitor["wait-time"];
    document.getElementById('script_interval').value = config["script-interval"];

    // Populate arrays
    populateModuleNames();
    populateUnwantedSubModules();
    populateWantedSubModules();
    populateGenericModules();
    populateDbTables();
    populateDbColumns();
    populateOrgAbbreviations();

    // Setup secret field handlers
    setupSecretFields();
}

// Setup handlers for secret fields
function setupSecretFields() {
    const secretFields = [
        'api_jwt',
        'db_password',
        'client_secret'
    ];

    secretFields.forEach(fieldId => {
        const field = document.getElementById(fieldId);
        if (field) {
            // Clear field on focus if it contains placeholder
            field.addEventListener('focus', function() {
                if (this.value === '********') {
                    this.value = '';
                }
            });

            // Restore placeholder if field is empty on blur
            field.addEventListener('blur', function() {
                if (this.value === '') {
                    this.value = '********';
                }
            });
        }
    });
}

// Save configuration to localStorage and server
async function saveConfig() {
    try {
        // Collect form data
        config.API.expires = document.getElementById('api_expires').value;
        // Only update JWT if it's been changed (not placeholder and not empty)
        const apiJwt = document.getElementById('api_jwt').value;
        if (apiJwt !== '********' && apiJwt !== '') {
            config.API["api-jwt"] = apiJwt;
        }
        config.API["api-token-refresh-offset"] = parseInt(document.getElementById('api_token_refresh_offset').value);
        config.API["api-endpoints"]["base-url"] = document.getElementById('base_url').value;
        config.API["api-endpoints"].auth["authenticate-endpoint"] = document.getElementById('auth_authenticate').value;
        config.API["api-endpoints"].auth["refresh-endpoint"] = document.getElementById('auth_refresh').value;

        // Device settings
        config.API["api-endpoints"].devices.endpoint = document.getElementById('device_endpoint').value;
        config.API["api-endpoints"].devices["device-services"] = document.getElementById('device_services').value;
        config.API["api-endpoints"].devices.params.pageSize = document.getElementById('page_size').value;

        // Task settings
        config.API["api-endpoints"].tasks.endpoint = document.getElementById('task_endpoint').value;

        // Database settings
        config.DB.host.ip = document.getElementById('db_host').value;
        config.DB.host.user = document.getElementById('db_user').value;
        // Only update password if it's been changed (not placeholder and not empty)
        const dbPassword = document.getElementById('db_password').value;
        if (dbPassword !== '********' && dbPassword !== '') {
            config.DB.host.password = dbPassword;
        }
        config.DB.host.database = document.getElementById('db_database').value;

        // Logging settings
        config.logging["max-log-size"] = parseInt(document.getElementById('max_log_size').value);
        config.logging["backup-count"] = parseInt(document.getElementById('backup_count').value);

        // Microsoft Graph settings
        config["microsoft-graph"]["client-id"] = document.getElementById('client_id').value;
        // Only update client secret if it's been changed (not placeholder and not empty)
        const clientSecret = document.getElementById('client_secret').value;
        if (clientSecret !== '********' && clientSecret !== '') {
            config["microsoft-graph"]["client-secret"] = clientSecret;
        }
        config["microsoft-graph"]["tenant-id"] = document.getElementById('tenant_id').value;
        config["microsoft-graph"].expires = document.getElementById('graph_expires').value;
        config["microsoft-graph"]["email-details"].sender = document.getElementById('email_sender').value;
        config["microsoft-graph"]["email-details"].subject = document.getElementById('email_subject').value;
        config["microsoft-graph"]["email-details"].body = document.getElementById('email_body').value;
        config["microsoft-graph"]["email-details"].recipient = document.getElementById('email_recipient').value;

        // Monitor settings
        config.monitor["max-retries"] = parseInt(document.getElementById('max_retries').value);
        config.monitor["wait-time"] = parseInt(document.getElementById('wait_time').value);
        config["script-interval"] = parseInt(document.getElementById('script_interval').value);

        // Save to server
        const response = await fetch('/api/config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(config)
        });

        if (!response.ok) {
            if (response.status === 401) {
                window.location.href = '/login';
                return;
            }
            throw new Error('Failed to save configuration to server');
        }

        // Save to localStorage
        localStorage.setItem('ncentralConfig', JSON.stringify(config));
        showAlert('Configuration saved successfully!', 'success');
    } catch (error) {
        console.error('Error saving configuration:', error);
        showAlert('Error saving configuration: ' + error.message, 'danger');
    }
}

// Add a new module name
function addModuleName(item = '') {
    const moduleNamesDiv = document.getElementById('module_names');
    const moduleNameItem = document.createElement('div');
    moduleNameItem.className = 'array-section';
    moduleNameItem.innerHTML = `
        <div class="array-header">
            <input type="text" class="form-control" placeholder="Module Name" value="${item || ''}">
            <button type="button" class="btn btn-delete" onclick="this.parentElement.parentElement.remove()">
                <i class="fas fa-trash"></i>
            </button>
        </div>
    `;
    moduleNamesDiv.appendChild(moduleNameItem);
}

// Add a new unwanted sub-module
function addUnwantedSubModule(item = '') {
    const unwantedSubModulesDiv = document.getElementById('unwanted_sub_modules');
    const unwantedSubModuleItem = document.createElement('div');
    unwantedSubModuleItem.className = 'array-section';
    unwantedSubModuleItem.innerHTML = `
        <div class="array-header">
            <input type="text" class="form-control" placeholder="Unwanted Sub-Module" value="${item || ''}">
            <button type="button" class="btn btn-delete" onclick="this.parentElement.parentElement.remove()">
                <i class="fas fa-trash"></i>
            </button>
        </div>
    `;
    unwantedSubModulesDiv.appendChild(unwantedSubModuleItem);
}

// Add a new wanted sub-module
function addWantedSubModule(item = '') {
    const wantedSubModulesDiv = document.getElementById('wanted_sub_modules');
    const wantedSubModuleItem = document.createElement('div');
    wantedSubModuleItem.className = 'array-section';
    wantedSubModuleItem.innerHTML = `
        <div class="array-header">
            <input type="text" class="form-control" placeholder="Wanted Sub-Module" value="${item || ''}">
            <button type="button" class="btn btn-delete" onclick="this.parentElement.parentElement.remove()">
                <i class="fas fa-trash"></i>
            </button>
        </div>
    `;
    wantedSubModulesDiv.appendChild(wantedSubModuleItem);
}

// Add a new generic module
function addGenericModule(item = '') {
    const genericModulesDiv = document.getElementById('generic_modules');
    const genericModuleItem = document.createElement('div');
    genericModuleItem.className = 'array-section';
    genericModuleItem.innerHTML = `
        <div class="array-header">
            <input type="text" class="form-control" placeholder="Generic Module" value="${item || ''}">
            <button type="button" class="btn btn-delete" onclick="this.parentElement.parentElement.remove()">
                <i class="fas fa-trash"></i>
            </button>
        </div>
    `;
    genericModulesDiv.appendChild(genericModuleItem);
}

// Add a new database table
function addDbTable(item = {}) {
    const dbTablesDiv = document.getElementById('db_tables');
    const dbTableItem = document.createElement('div');
    dbTableItem.className = 'array-section';
    dbTableItem.innerHTML = `
        <div class="array-header">
            <input type="text" class="form-control" placeholder="Table Key" value="${Object.keys(item)[0] || ''}">
            <input type="text" class="form-control" placeholder="Table Name" value="${Object.values(item)[0] || ''}">
            <button type="button" class="btn btn-delete" onclick="this.parentElement.parentElement.remove()">
                <i class="fas fa-trash"></i>
            </button>
        </div>
    `;
    dbTablesDiv.appendChild(dbTableItem);
}

// Add a new database column
function addDbColumn(item = {}) {
    const dbColumnsDiv = document.getElementById('db_columns');
    const dbColumnItem = document.createElement('div');
    dbColumnItem.className = 'array-section';
    dbColumnItem.innerHTML = `
        <div class="array-header">
            <input type="text" class="form-control" placeholder="Table Key" value="${Object.keys(item)[0] || ''}">
            <input type="text" class="form-control" placeholder="Column Names (comma-separated)" value="${Object.values(item)[0]?.join(', ') || ''}">
            <button type="button" class="btn btn-delete" onclick="this.parentElement.parentElement.remove()">
                <i class="fas fa-trash"></i>
            </button>
        </div>
    `;
    dbColumnsDiv.appendChild(dbColumnItem);
}

// Add a new organization abbreviation
function addOrgAbbreviation(item = {}) {
    const orgAbbreviationsDiv = document.getElementById('org_abbreviations');
    const orgAbbreviationItem = document.createElement('div');
    orgAbbreviationItem.className = 'array-section';
    orgAbbreviationItem.innerHTML = `
        <div class="array-header">
            <input type="text" class="form-control" placeholder="Organization Name" value="${Object.keys(item)[0] || ''}">
            <input type="text" class="form-control" placeholder="Abbreviation" value="${Object.values(item)[0] || ''}">
            <button type="button" class="btn btn-delete" onclick="this.parentElement.parentElement.remove()">
                <i class="fas fa-trash"></i>
            </button>
        </div>
    `;
    orgAbbreviationsDiv.appendChild(orgAbbreviationItem);
}

// Populate module names array
function populateModuleNames() {
    const moduleNamesDiv = document.getElementById('module_names');
    moduleNamesDiv.innerHTML = '';
    config.API["api-endpoints"].tasks["data-filter"]["module-names"].forEach(item => {
        addModuleName(item);
    });
}

// Populate unwanted sub-modules array
function populateUnwantedSubModules() {
    const unwantedSubModulesDiv = document.getElementById('unwanted_sub_modules');
    unwantedSubModulesDiv.innerHTML = '';
    config.API["api-endpoints"].tasks["data-filter"]["unwanted-sub-modules"].forEach(item => {
        addUnwantedSubModule(item);
    });
}

// Populate wanted sub-modules array
function populateWantedSubModules() {
    const wantedSubModulesDiv = document.getElementById('wanted_sub_modules');
    wantedSubModulesDiv.innerHTML = '';
    config.API["api-endpoints"].tasks["data-filter"]["wanted-sub-modules"].forEach(item => {
        addWantedSubModule(item);
    });
}

// Populate generic modules array
function populateGenericModules() {
    const genericModulesDiv = document.getElementById('generic_modules');
    genericModulesDiv.innerHTML = '';
    config.API["api-endpoints"].tasks["data-filter"]["generic-modules"].forEach(item => {
        addGenericModule(item);
    });
}

// Populate database tables array
function populateDbTables() {
    const dbTablesDiv = document.getElementById('db_tables');
    dbTablesDiv.innerHTML = '';
    Object.entries(config.DB["db-tables"]).forEach(([key, value]) => {
        addDbTable({ [key]: value });
    });
}

// Populate database columns array
function populateDbColumns() {
    const dbColumnsDiv = document.getElementById('db_columns');
    dbColumnsDiv.innerHTML = '';
    Object.entries(config.DB["db-columns"]).forEach(([key, value]) => {
        addDbColumn({ [key]: value });
    });
}

// Populate organization abbreviations array
function populateOrgAbbreviations() {
    const orgAbbreviationsDiv = document.getElementById('org_abbreviations');
    orgAbbreviationsDiv.innerHTML = '';
    Object.entries(config["org-abbreviations"]).forEach(([key, value]) => {
        addOrgAbbreviation({ [key]: value });
    });
}

// Show alert message
function showAlert(message, type = 'info') {
    const alertDiv = document.getElementById('alert');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.textContent = message;
    alertDiv.style.display = 'block';
    setTimeout(() => {
        alertDiv.style.display = 'none';
    }, 3000);
}

// Setup event listeners
function setupEventListeners() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Add form validation
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            if (this.checkValidity()) {
                saveConfig();
            }
        });
    });
}

function resetConfig() {
    // Show the confirmation modal
    const resetModal = new bootstrap.Modal(document.getElementById('resetConfirmModal'));
    resetModal.show();
}

function confirmReset() {
    // Hide the modal
    const resetModal = bootstrap.Modal.getInstance(document.getElementById('resetConfirmModal'));
    resetModal.hide();

    // Show loading state
    const resetBtn = document.querySelector('button[onclick="resetConfig()"]');
    const originalContent = resetBtn.innerHTML;
    resetBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Resetting...';
    resetBtn.disabled = true;

    // Call the reset endpoint
    fetch('/reset_config', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('Configuration reset to defaults successfully!', 'success');
            // Reload the configuration
            loadConfig();
        } else {
            showAlert('Failed to reset configuration: ' + data.error, 'danger');
        }
    })
    .catch(error => {
        showAlert('Error resetting configuration: ' + error, 'danger');
    })
    .finally(() => {
        // Restore button state
        resetBtn.innerHTML = originalContent;
        resetBtn.disabled = false;
    });
} 