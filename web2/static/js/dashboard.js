let recentLogsTimer;
let errorLogsTimer;

// Constants for update intervals (in milliseconds)
const STATUS_UPDATE_INTERVAL = 60000; // 1 minute
const LOGS_UPDATE_INTERVAL = 30000;   // 30 seconds

// Elements cache
const elements = {
    serviceStatus: document.querySelector('.service-status'),
    statusText: document.querySelector('.status-text'),
    completedRuns: document.getElementById('completedRuns'),
    failedRuns: document.getElementById('failedRuns'),
    lastRunTime: document.getElementById('lastRunTime'),
    lastRunStatus: document.getElementById('lastRunStatus'),
    recentLogs: document.getElementById('recentLogs'),
    errorLogs: document.getElementById('errorLogs')
};

function formatLogMessage(log) {
    const logClass = `log-${log.level}`;
    return `<div class="log-entry ${logClass}">${log.message}</div>`;
}

async function refreshLogs(type) {
    try {
        const response = await fetch(`/api/logs/${type}`);
        const data = await response.json();
        
        const logsContainer = document.getElementById(`${type}-logs`);
        if (logsContainer) {
            logsContainer.innerHTML = data.logs.map(formatLogMessage).join('');
            logsContainer.scrollTop = logsContainer.scrollHeight;
        }
    } catch (error) {
        console.error(`Error refreshing ${type} logs:`, error);
    }
}

function startAutoRefresh() {
    // Clear any existing timers
    if (recentLogsTimer) clearInterval(recentLogsTimer);
    if (errorLogsTimer) clearInterval(errorLogsTimer);

    // Set up new timers
    recentLogsTimer = setInterval(() => refreshLogs('recent'), 30000);
    errorLogsTimer = setInterval(() => refreshLogs('error'), 30000);
}

async function startService() {
    if (!confirm('Are you sure you want to start the service?')) {
        return;
    }

    try {
        const response = await fetch('/api/service/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        if (data.success) {
            location.reload();
        } else {
            alert(`Failed to start service: ${data.error}`);
        }
    } catch (error) {
        alert('Failed to start service. Please check the logs for details.');
    }
}

// Utility functions
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    // Handle the format: 2024-10-30 13:35:24,447
    const [datePart, timePart] = dateString.split(' ');
    const [time, millis] = timePart.split(',');
    return `${datePart} ${time}`;
}

function formatLogEntry(log) {
    const timestamp = formatDate(log.timestamp);
    const level = log.level.toLowerCase();
    return `<div class="log-entry log-${level}">
        [${timestamp}] ${log.level}: ${log.message}
    </div>`;
}

// API calls
async function fetchServiceStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        
        // Update service status
        elements.serviceStatus.classList.toggle('active', data.is_running);
        elements.serviceStatus.classList.toggle('inactive', !data.is_running);
        elements.statusText.textContent = data.is_running ? 'Active' : 'Inactive';
        
        // Update statistics
        elements.completedRuns.textContent = data.completed_runs || '0';
        elements.failedRuns.textContent = data.failed_runs || '0';
        elements.lastRunTime.textContent = formatDate(data.last_run_time);
        elements.lastRunStatus.textContent = data.last_run_status || 'N/A';
        
        return true;
    } catch (error) {
        console.error('Error fetching service status:', error);
        return false;
    }
}

async function fetchLogs() {
    try {
        const response = await fetch('/api/logs');
        const data = await response.json();
        
        // Update recent logs
        if (elements.recentLogs && data.recent_logs) {
            elements.recentLogs.innerHTML = data.recent_logs
                .map(formatLogEntry)
                .join('');
        }
        
        // Update error logs
        if (elements.errorLogs && data.error_logs) {
            elements.errorLogs.innerHTML = data.error_logs
                .map(formatLogEntry)
                .join('');
        }
        
        return true;
    } catch (error) {
        console.error('Error fetching logs:', error);
        return false;
    }
}

// Event handlers
function setupRefreshButtons() {
    const refreshButtons = document.querySelectorAll('.refresh-logs');
    refreshButtons.forEach(button => {
        button.addEventListener('click', async (e) => {
            e.preventDefault();
            const icon = button.querySelector('i');
            icon.classList.add('fa-spin');
            
            await fetchLogs();
            
            // Remove spin after a short delay
            setTimeout(() => {
                icon.classList.remove('fa-spin');
            }, 500);
        });
    });
}

// Initialize dashboard
async function initDashboard() {
    // Initial data fetch
    await Promise.all([
        fetchServiceStatus(),
        fetchLogs()
    ]);
    
    // Setup refresh buttons
    setupRefreshButtons();
    
    // Setup update intervals
    setInterval(fetchServiceStatus, STATUS_UPDATE_INTERVAL);
    setInterval(fetchLogs, LOGS_UPDATE_INTERVAL);
}

// Start dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', initDashboard);

function createLogElement(log) {
    const div = document.createElement('div');
    div.className = `log-entry ${log.level.toLowerCase()}`;
    
    // Create timestamp element
    const timestamp = document.createElement('span');
    timestamp.className = 'log-timestamp';
    
    if (log.timestamp) {
        // Format the timestamp to be more readable
        const [datePart, timePart] = log.timestamp.split(' ');
        const [time, millis] = timePart.split(',');
        timestamp.textContent = `${datePart} ${time}`;
    } else {
        timestamp.textContent = 'Invalid Date';
    }
    
    // Create file info element
    const fileInfo = document.createElement('span');
    fileInfo.className = 'log-file';
    fileInfo.textContent = log.file;
    
    // Create message element
    const message = document.createElement('span');
    message.className = 'log-message';
    message.textContent = log.message;
    
    // Append all elements
    div.appendChild(timestamp);
    div.appendChild(document.createTextNode(' - '));
    div.appendChild(fileInfo);
    div.appendChild(document.createTextNode(' - '));
    div.appendChild(message);
    
    return div;
}

function updateDashboard() {
    console.log("Updating dashboard...");
    
    // Fetch service status and statistics
    fetch('/api/status')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log("Status data received:", data);
            
            // Update service status
            const statusElement = document.getElementById('service-status');
            if (statusElement) {
                statusElement.textContent = data.is_running ? 'Active' : 'Inactive';
                statusElement.className = `service-status ${data.is_running ? 'active' : 'inactive'}`;
            }

            // Update statistics
            const completedRuns = document.getElementById('completed-runs');
            const failedRuns = document.getElementById('failed-runs');
            const lastRunTime = document.getElementById('last-run-time');
            const lastRunStatus = document.getElementById('last-run-status');

            if (completedRuns) completedRuns.textContent = data.completed_runs;
            if (failedRuns) failedRuns.textContent = data.failed_runs;
            if (lastRunTime) lastRunTime.textContent = data.last_run_time;
            if (lastRunStatus) lastRunStatus.textContent = data.last_run_status;
        })
        .catch(error => {
            console.error('Error fetching status:', error);
            // Show error in the UI
            const statusElement = document.getElementById('service-status');
            if (statusElement) {
                statusElement.textContent = 'Error';
                statusElement.className = 'service-status error';
            }
        });

    // Fetch logs
    fetch('/api/logs')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log("Logs data received:", data);
            
            // Update recent logs
            const recentLogsContainer = document.getElementById('recent-logs');
            if (recentLogsContainer) {
                recentLogsContainer.innerHTML = '';
                if (data.recent_logs && data.recent_logs.length > 0) {
                    data.recent_logs.forEach(log => {
                        console.log("Processing log:", log);
                        const logElement = createLogElement(log);
                        recentLogsContainer.appendChild(logElement);
                    });
                } else {
                    recentLogsContainer.innerHTML = '<div class="log-entry info">No recent logs available</div>';
                }
            }

            // Update error logs
            const errorLogsContainer = document.getElementById('error-logs');
            if (errorLogsContainer) {
                errorLogsContainer.innerHTML = '';
                if (data.error_logs && data.error_logs.length > 0) {
                    data.error_logs.forEach(log => {
                        console.log("Processing error log:", log);
                        const logElement = createLogElement(log);
                        errorLogsContainer.appendChild(logElement);
                    });
                } else {
                    errorLogsContainer.innerHTML = '<div class="log-entry info">No error logs available</div>';
                }
            }
        })
        .catch(error => {
            console.error('Error fetching logs:', error);
            // Show error in the UI
            const recentLogsContainer = document.getElementById('recent-logs');
            const errorLogsContainer = document.getElementById('error-logs');
            if (recentLogsContainer) {
                recentLogsContainer.innerHTML = '<div class="log-entry error">Error loading logs</div>';
            }
            if (errorLogsContainer) {
                errorLogsContainer.innerHTML = '<div class="log-entry error">Error loading logs</div>';
            }
        });
}

// Update dashboard every 30 seconds
setInterval(updateDashboard, 30000);

// Initial update
updateDashboard(); 