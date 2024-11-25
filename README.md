# n-central-data-grabber
This application is used to extract the raw-monitored data from n-central. It is customizeable to exclude/include as many data points as the user wants.

# Setup
## Linux
1. Ensure that both >=Python 3.8 and >=mysql 8.0 are installed
2. Ensure that both pip and venv are installed
    - `sudo apt install python3-pip`
    - `sudo apt install python(version)-venv`
4. Clone the repository into /opt/ (or wherever works best)
5. Navigate to the directory and run the following:
    - `chmod +x scripts/setup.sh`
    - `sudo scripts/setup.sh`
    - `python3 -m venv venv`
    - `source venv/bin/activate`
    - `pip install -r requirements.txt`
6. Configure `config.json`
7. After configuration, to start the script run `python3 main.py`
    - Ensure this is run in the venv, otherwise the script may not be able to access necessary modules
    - To exit the venv, run `deactivate`

### Remote DB Access
If you want to access the DB from a different device on your network, follow these steps.
1. Log into mysql as root user
2. Run the following commands:
    - `CREATE USER 'remote_user'@'%' IDENTIFIED BY '(password_here)'`
        - Replace '%' with an IP if you want to limit access to a specific IP
    - `GRANT ALL PRIVILEGES ON n_central_monitor_data.* TO 'remote_user'@'%';`
    - `FLUSH PRIVILEGES;`
3. Ensure that bind-address is set to 0.0.0.0 (or a specific IP)
    - `sudo nano /etc/mysql/mysql.conf.d/mysqld.cnf`
    - Change `bind-address: 127.0.0.2` to `0.0.0.0` or a specific IP address
4. Restart mysql and check to see if the connection works. 


# Configuration
Take `config-template.json` and rename it to `config.json`. Below is the config documentation. Entries marked with 🔒 indicate you should not change them unless information relating to the API is changed.

## `API`

- **`api-jwt`**:  *N-central User-API Token (JWT) (http, Bearer)* - see N-Central's API for more details.
- **`api-token-refresh-offset`**:  How early to refresh the `API-Access Token` before it expires. Consider updating this in accordance with `script-interval` and how long it takes the script to run. The logs gives detailed information on run-time after each run. Default: 10 minutes.

### `api-endpoints`

- **`base-url`**:  The URL of your n-central ncod server.

#### `auth`
- **🔒`authenticate-endpoint`**:  Used to authenticate the api-jwt token. 
- **🔒`refresh-endpoint`**:  Used to refresh the api-access token.

#### `devices`
- **🔒`endpoint`**:  Endpoint for retrieving the list of devices from N-central.
- **🔒`device-services`**:  Endpoint attached onto `endpoint` with a device id to retrieve the status of service monitoring tasks. 
- **`params`**:  Refine the query to `endpoint`. Review a list of params for `devices` at https://`base-url`/api-explorer
- **`device-filter`**:  How device information is stored in the dictionary that saves the data returned from get request to `endpoint`. In `info`, index 0 of the lists corresponds to a key in the response data. In the case that these names ever change, they can be re-named here. Index 1 of the lists in `info` should not, and do not need to be changed.
- - **Note** info[0][1] should be changed in accordance with the column name for the device table's primary key.
- **🔒`time-format`**:  Used to match the time format the api returns in device tasks for last scan time.  

#### `tasks`
- **🔒`endpoint`**:  Endpoint for retrieving the list of tasks (services) the device is set to run.
- **🔒`task-filter`**:  Used to retrieve important task information from the response returned from the get request to `endpoint`. Do not change unless the API response keys have changed.
- **`data-filter`**:  This is what is used to extract values from the response returned from `endpoint` called with a task id.
  - **🔒`data-row-name`**:  The key in the api response to retrieve the raw data name.
  - **🔒`info`**:  A list of lists. Index 0 of the lists contains the api response key, and index 1 of the lists contains the user defined key they want to store it as. Index 1 of these lists *can* be changed to match column schema in your DB; however, it is recommended to keep these names as is since testing has not been done to ensure proper insertion with different column names. 
  - **`module-names`**:  A list containing the services you want to fetch using an exact match. Setting to empty will fetch all services. Note - the more services, the longer the script will run since an API call will be made for each service.
  - **`unwanted-sub-modules`**:  A list containing the raw data points you do not want to fetch from a service. This uses the 'description' field returned from the api get request to filter out anything containing the word. Can be left empty.
  - **`wanted-sub-modules`**:  A list containing the specific raw data points you want to extract from a service. This checks against the 'description' and 'detailName' fields from the returned api response. Note that this is checked after filtering with `unwanted-sub-modules`. Can be empty.
  - **`generic-modules`**: A list containing the services you want to fetch using a substring match. For example, if this was set to ["CPU"] and a service is named "CPU - Palo Alto" it will include it.

---

## `DB`

### `db-tables`:

- **`orgs`**:  Table name in your db for orgs
- **`devices`**:  Table name in your db for devices
- **`data-info`**:  Table name in your db for data-info
- **`raw-data`**:  Table name in your db for raw-data

### `db-columns`

- **`orgs`**:  A list containing the column names for id and name.
- **`data-info`**:  A list containing the column names for id, name, and description.
- **`raw-data`**:  A list containing the column names for value, state, scan time, id (foreign key to devices), and id (foreign key to data-info)

### `host`

- **`ip`**:  DB Host to connect to.
- **`user`**:  Username used to access DB.
- **`password`**:  Password to access DB.
- **`database`**:  Database name.

---

## `Logging`
- **`max-log-size`**: The size (in mb) the log files should reach before rotating.
- **`backup-count`**: The number of log files that have been rotated out to retain until deleting them.

---

### `org-abbreviations` - *Optional*: 
- A dict containing org names you would like abbreviated for DB insertion into the `org_name` column. Ex: "Google": "GGL" would insert "GGL" into the `org_name` column for the insertion of Google into the orgs table. 

### `script-interval`: 
- How often you want to fetch the data. This is a set interval, and if the script finishes after the interval threshold is met, it will immediately start again. If this is the case though, consider increasing the interval or reducing the amount of raw data being retrieved through `module-names`. Default: 300 seconds.

  


