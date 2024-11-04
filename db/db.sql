CREATE DATABASE IF NOT EXISTS n_central_monitor_data;
USE n_central_monitor_data;

CREATE TABLE orgs (
    org_id INT AUTO_INCREMENT PRIMARY KEY,
    org_name VARCHAR(255) NOT NULL
);

CREATE TABLE devices (
    device_id INT PRIMARY KEY,
    device_name VARCHAR(255) NOT NULL,
    device_class VARCHAR(255) NOT NULL,
    model VARCHAR(255),
    manufacturer VARCHAR(255),
    org_id INT,
    FOREIGN KEY (org_id) REFERENCES orgs(org_id) ON DELETE CASCADE
);

CREATE TABLE data_info (
    data_id VARCHAR(255) PRIMARY KEY,
    field_name VARCHAR(255) NOT NULL,
    description VARCHAR(255) NOT NULL
);

CREATE TABLE raw_data (
    raw_data_id INT AUTO_INCREMENT PRIMARY KEY,
    value TEXT NOT NULL,
    state VARCHAR(255),
    scan_time DATETIME,
    device_id INT,
    data_id VARCHAR(255),
    FOREIGN KEY (device_id) REFERENCES devices(device_id) ON DELETE CASCADE,
    FOREIGN KEY (data_id) REFERENCES data_info(data_id) ON DELETE CASCADE
);