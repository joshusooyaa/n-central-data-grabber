let configData = {};

// Load configuration data
async function loadConfig() {
    try {
        const response = await fetch('/api/config');
        configData = await response.json();
        initializeForms();
    } catch (error) {
        console.error('Error loading config:', error);
        showAlert('Error loading configuration', 'danger');
    }
}

// Initialize all forms
function initializeForms() {
    initializeApiEndpointsForm();
    initializeApiDevicesForm();
    initializeTaskFilterForm();
    initializeDataFilterForm();
    initializeDbForm();
    initializeOrgForm();
    initializeMonitorForm();
}

// Create a key-value pair table
function createKeyValueTable(container, data, path) {
    const table = document.createElement('table');
    table.className = 'table key-value-table';
    
    const thead = document.createElement('thead');
    thead.innerHTML = `
        <tr>
            <th>Key</th>
            <th>Value</th>
            <th></th>
        </tr>
    `;
    
    const tbody = document.createElement('tbody');
    
    // Add existing rows
    Object.entries(data).forEach(([key, value]) => {
        if (Array.isArray(value)) {
            addArrayRow(tbody, key, value, path);
        } else if (typeof value === 'object' && value !== null) {
            addNestedObjectRow(tbody, key, value, path);
        } else {
            addKeyValueRow(tbody, key, value, path);
        }
    });
    
    // Add button row
    const buttonRow = document.createElement('tr');
    buttonRow.innerHTML = `
        <td colspan="3">
            <button class="btn btn-primary btn-sm btn-add" onclick="addNewKeyValueRow(this, '${path}')">
                <i class="bi bi-plus"></i> Add New
            </button>
        </td>
    `;
    tbody.appendChild(buttonRow);
    
    table.appendChild(thead);
    table.appendChild(tbody);
    container.innerHTML = '';
    container.appendChild(table);
}

// Add a new key-value row
function addKeyValueRow(tbody, key, value, path) {
    const row = document.createElement('tr');
    row.innerHTML = `
        <td><input type="text" class="form-control" value="${key}" onchange="updateKeyValue(this, '${path}')"></td>
        <td><input type="text" class="form-control" value="${value}" onchange="updateKeyValue(this, '${path}')"></td>
        <td></td>
    `;
    tbody.insertBefore(row, tbody.lastChild);
}

// Add array row with nested table
function addArrayRow(tbody, key, value, path) {
    const row = document.createElement('tr');
    const isNestedArray = Array.isArray(value[0]) && value[0].length === 2;
    
    row.innerHTML = `
        <td colspan="3">
            <div class="array-section">
                <h6 class="array-header">${key}</h6>
                <div class="array-table-container">
                    <table class="table table-sm array-table">
                        <thead>
                            <tr>
                                ${isNestedArray ? '<th>Key</th><th>Value</th>' : '<th>Value</th>'}
                                <th class="action-column"></th>
                            </tr>
                        </thead>
                        <tbody>
                            ${value.map((item, index) => {
                                if (isNestedArray) {
                                    return `
                                        <tr>
                                            <td><input type="text" class="form-control form-control-sm" value="${item[0]}" onchange="updateArrayItem(this, '${path}', '${key}', ${index}, 0)"></td>
                                            <td><input type="text" class="form-control form-control-sm" value="${item[1]}" onchange="updateArrayItem(this, '${path}', '${key}', ${index}, 1)"></td>
                                            <td class="action-column">
                                                <button class="btn btn-danger btn-sm btn-delete" onclick="deleteArrayItem(this, '${path}', '${key}', ${index})">
                                                    <i class="bi bi-trash"></i>
                                                </button>
                                            </td>
                                        </tr>
                                    `;
                                } else {
                                    return `
                                        <tr>
                                            <td><input type="text" class="form-control form-control-sm" value="${item}" onchange="updateArrayItem(this, '${path}', '${key}', ${index})"></td>
                                            <td class="action-column">
                                                <button class="btn btn-danger btn-sm btn-delete" onclick="deleteArrayItem(this, '${path}', '${key}', ${index})">
                                                    <i class="bi bi-trash"></i>
                                                </button>
                                            </td>
                                        </tr>
                                    `;
                                }
                            }).join('')}
                        </tbody>
                    </table>
                    <div class="array-actions">
                        <button class="btn btn-primary btn-sm btn-add" onclick="addNewArrayItem(this, '${path}', '${key}', ${isNestedArray})">
                            <i class="bi bi-plus"></i> Add New
                        </button>
                    </div>
                </div>
            </div>
        </td>
    `;
    tbody.insertBefore(row, tbody.lastChild);
}

// Add nested object row
function addNestedObjectRow(tbody, key, value, path) {
    const row = document.createElement('tr');
    row.innerHTML = `
        <td>${key}</td>
        <td>
            <div class="nested-object-container">
                <table class="table table-sm nested-object-table">
                    <thead>
                        <tr>
                            <th>Key</th>
                            <th>Value</th>
                            <th></th>
                        </tr>
                    </thead>
                    <tbody>
                        ${Object.entries(value).map(([subKey, subValue]) => `
                            <tr>
                                <td><input type="text" class="form-control form-control-sm" value="${subKey}" onchange="updateNestedObjectKey(this, '${path}', '${key}', '${subKey}')"></td>
                                <td><input type="text" class="form-control form-control-sm" value="${subValue}" onchange="updateNestedObjectValue(this, '${path}', '${key}', '${subKey}')"></td>
                                <td></td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
                <button class="btn btn-primary btn-sm btn-add" onclick="addNewNestedObjectItem(this, '${path}', '${key}')">
                    <i class="bi bi-plus"></i> Add New
                </button>
            </div>
        </td>
        <td></td>
    `;
    tbody.insertBefore(row, tbody.lastChild);
}

// Add new array item
function addNewArrayItem(button, path, key, isNestedArray) {
    const tbody = button.previousElementSibling.querySelector('tbody');
    const newRow = document.createElement('tr');
    
    if (isNestedArray) {
        newRow.innerHTML = `
            <td><input type="text" class="form-control form-control-sm" onchange="updateArrayItem(this, '${path}', '${key}', ${tbody.children.length}, 0)"></td>
            <td><input type="text" class="form-control form-control-sm" onchange="updateArrayItem(this, '${path}', '${key}', ${tbody.children.length}, 1)"></td>
            <td>
                <button class="btn btn-danger btn-sm btn-delete" onclick="deleteArrayItem(this, '${path}', '${key}', ${tbody.children.length})">
                    <i class="bi bi-trash"></i>
                </button>
            </td>
        `;
    } else {
        newRow.innerHTML = `
            <td><input type="text" class="form-control form-control-sm" onchange="updateArrayItem(this, '${path}', '${key}', ${tbody.children.length})"></td>
            <td>
                <button class="btn btn-danger btn-sm btn-delete" onclick="deleteArrayItem(this, '${path}', '${key}', ${tbody.children.length})">
                    <i class="bi bi-trash"></i>
                </button>
            </td>
        `;
    }
    
    tbody.appendChild(newRow);
    updateArray(path, key);
}

// Update array item
function updateArrayItem(input, path, key, index, subIndex) {
    const currentData = getConfigValue(path);
    if (!currentData[key]) {
        currentData[key] = [];
    }
    
    if (subIndex !== undefined) {
        if (!currentData[key][index]) {
            currentData[key][index] = ['', ''];
        }
        currentData[key][index][subIndex] = input.value;
    } else {
        currentData[key][index] = input.value;
    }
    
    updateConfig(path, currentData);
}

// Delete array item
function deleteArrayItem(button, path, key, index) {
    const row = button.closest('tr');
    const currentData = getConfigValue(path);
    currentData[key].splice(index, 1);
    updateConfig(path, currentData);
    row.remove();
}

// Update array
function updateArray(path, key) {
    const currentData = getConfigValue(path);
    const tbody = document.querySelector(`[data-path="${path}"] [data-key="${key}"] tbody`);
    currentData[key] = Array.from(tbody.children).map(row => {
        const inputs = row.querySelectorAll('input');
        if (inputs.length === 2) {
            return [inputs[0].value, inputs[1].value];
        } else {
            return inputs[0].value;
        }
    });
    updateConfig(path, currentData);
}

// Add new key-value row
function addNewKeyValueRow(button, path) {
    const tbody = button.closest('tbody');
    addKeyValueRow(tbody, '', '', path);
}

// Update key-value pair
function updateKeyValue(input, path) {
    const row = input.closest('tr');
    const keyInput = row.querySelector('input:first-child');
    const valueInput = row.querySelector('input:nth-child(2)');
    
    const key = keyInput.value;
    const value = valueInput.value;
    
    if (key && value) {
        updateConfig(path, { [key]: value });
    }
}

// Delete key-value row
function deleteKeyValueRow(button, path) {
    const row = button.closest('tr');
    const key = row.querySelector('input:first-child').value;
    
    if (key) {
        const currentData = getConfigValue(path);
        delete currentData[key];
        updateConfig(path, currentData);
    }
    
    row.remove();
}

// Get config value at path
function getConfigValue(path) {
    const sections = path.split('.');
    let current = configData;
    for (const section of sections) {
        current = current[section];
    }
    return current;
}

// Update config at path
async function updateConfig(path, value) {
    try {
        const response = await fetch(`/api/config/${path}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(value)
        });
        
        if (response.ok) {
            showAlert('Configuration updated successfully', 'success');
            loadConfig();
        } else {
            throw new Error('Failed to update configuration');
        }
    } catch (error) {
        console.error('Error updating config:', error);
        showAlert('Error updating configuration', 'danger');
    }
}

// Show alert message
function showAlert(message, type) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.querySelector('.container-fluid');
    container.insertBefore(alertDiv, container.firstChild);
    
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

// Initialize API Endpoints form
function initializeApiEndpointsForm() {
    const container = document.getElementById('api-endpoints-form');
    const data = configData.API['api-endpoints'];
    createKeyValueTable(container, data, 'API.api-endpoints');
}

// Initialize API Devices form
function initializeApiDevicesForm() {
    const container = document.getElementById('api-devices-form');
    const data = configData.API['api-endpoints'].devices;
    createKeyValueTable(container, data, 'API.api-endpoints.devices');
}

// Initialize Task Filter form
function initializeTaskFilterForm() {
    const container = document.getElementById('task-filter-form');
    const data = configData.API['api-endpoints'].tasks['task-filter'];
    createKeyValueTable(container, data, 'API.api-endpoints.tasks.task-filter');
}

// Initialize Data Filter form
function initializeDataFilterForm() {
    const container = document.getElementById('data-filter-form');
    const data = configData.API['api-endpoints'].tasks['data-filter'];
    createKeyValueTable(container, data, 'API.api-endpoints.tasks.data-filter');
}

// Initialize Database form
function initializeDbForm() {
    const container = document.getElementById('db-form');
    const data = configData.DB;
    createKeyValueTable(container, data, 'DB');
}

// Initialize Organization form
function initializeOrgForm() {
    const container = document.getElementById('org-form');
    const data = configData['org-abbreviations'];
    createKeyValueTable(container, data, 'org-abbreviations');
}

// Initialize Monitor form
function initializeMonitorForm() {
    const container = document.getElementById('monitor-form');
    const data = configData.monitor;
    createKeyValueTable(container, data, 'monitor');
}

// Load configuration when page loads
document.addEventListener('DOMContentLoaded', loadConfig); 