import mysql.connector
from mysql.connector import Error

class DBHandler:
  def __init__(self, config, logger, api):
    self.config = config
    self.logger = logger
    self.api = api
    self.connection = None

    self.device_filter = config['API']['api-endpoints']['devices']['device-filter']['info']
    self.data_filter = config['API']['api-endpoints']['tasks']['data-filter']['info']
    self.db_columns = config['DB']['db-columns']
    self.db_tables = config['DB']['db-tables']

    self.cached_orgs = {}
    self.cached_devices = []
    self.cached_data = []

  def connect(self):
    try:
      self.connection = mysql.connector.connect(
        host=self.config['DB']['host']['ip'],
        user=self.config['DB']['host']['user'],
        password=self.config['DB']['host']['password'],
        database=self.config['DB']['host']['database']
      )
      if self.connection.is_connected():
        self.logger.info(f"Successfully established connection with DB: {self.config['DB']['host']['database']}")
    except Error as e:
      self.logger.error(f"Error while connecting to MySQL: {e}")
  
  def close(self):
    if self.connection and self.connection.is_connected():
      self.connection.close()
      self.logger.info(f"DB connection closed with: {self.config['DB']['host']['database']}")

  def execute_query(self, query, params=None):
    cursor = None
    try:
      cursor = self.connection.cursor()
      cursor.execute(query, params)
      self.connection.commit()
      return cursor.lastrowid
    except Error as e:
      self.logger.error(f"Error executing query: {query}")
      self.logger.error(f"Error thrown as: {e}")
      return False
    finally:
      if cursor:
        cursor.close()

  def insert(self, table, data):
    placeholders = ", ".join(['%s'] * len(data))
    columns = ", ".join(data.keys())
    sql = f"INSERT IGNORE INTO {table} ({columns}) VALUES ({placeholders})"

    values = tuple(data.values())

    try:
      self.execute_query(sql, values)
    except Error as e:
      self.logger.error(f"Error inserting data: {e}")
  
  def update(self, table, column_name, new_value, where_column, where_value):
    sql = f"UPDATE {table} SET {column_name} = %s WHERE {where_column} = %s"
    try:
      self.execute_query(sql, (new_value, where_value))
    except Error as e:
      self.logger.error(f"Error updating device id: {where_value} with error: {e}")
  
  def batch_insert(self, table, columns, data_list):
    placeholders = ", ".join(['%s'] * len(columns))
    columns_str = ", ".join(columns)
    sql = f"INSERT IGNORE INTO {table} ({columns_str}) VALUES ({placeholders})"
    try:
      cursor = self.connection.cursor()
      cursor.executemany(sql, data_list)
      self.connection.commit()
    except Error as e:
      self.logger.error(f"Error inserting data: {e}")
    finally:
      if cursor:
        cursor.close()
  
  def get(self, table, columns="*", conditions=None):
    cursor = None
    try:
      cursor = self.connection.cursor(dictionary=True)
      query = f"SELECT {columns} FROM {table}"

      if conditions:
        where = ' AND '.join([f"{key} = %s" for key in conditions.keys()])
        query += f" WHERE {where}"
        cursor.execute(query, tuple(conditions.values()))
      else:
        cursor.execute(query)
      
      return cursor.fetchall()
    except Error as e:
      self.logger.error(f"Error retrieving data: {e}")
    finally:
      if cursor:
        cursor.close()

  def format_and_insert(self, table, data, tables):
    device_id_key = self.device_filter[0][1]
    device_name_key = self.device_filter[1][1]

    if table == tables['devices']:
      if not self._added_device(data[device_id_key]):
        data = self._package_device_insertion_data(data)
        self.logger.info(f"New device found! id: {data[device_id_key]}")
        self.insert(table, data)
      elif self._device_name_changed(data[device_id_key], data[device_name_key]):
        self.logger.info(f"Device name changed! id: {data[device_id_key]}, new name: {data[device_name_key]}")
        self.update(table, device_name_key, data[device_name_key], device_id_key, data[device_id_key])

    elif table == tables['raw-data']:
      data_info_batch = []
      raw_data_batch = []

      data_id_key = self.data_filter[0][1]
      description_key = self.data_filter[1][1]
      value_key = self.data_filter[2][1]
      state_key = self.data_filter[3][1]
      disk_name_key = self.data_filter[4][1]

      for device_id, fields_list in data.items():
        if device_id == 'scanTime':
          continue
        for field_dict in fields_list:
          for field_name, raw_data in field_dict.items():
            data_id = raw_data[data_id_key]
            if raw_data.get(disk_name_key):
              data_id = f"{raw_data[data_id_key]}_{raw_data[disk_name_key]}"
              field_name = f"{field_name}_{raw_data[disk_name_key]}"
            
            data_info_batch.append((
                    data_id,
                    field_name,
                    raw_data[description_key]
                ))

            raw_data_batch.append((
                raw_data[value_key],
                raw_data[state_key],
                data['scanTime'],
                device_id,
                data_id
            ))
      
      self.batch_insert(tables['data-info'], self.db_columns['data-info'], data_info_batch)
      self.batch_insert(tables['raw-data'], self.db_columns['raw-data'], raw_data_batch)

  def _get_org_id(self, org_name):
    org_id_column = self.db_columns['orgs'][0]
    org_name_column = self.db_columns['orgs'][1]
    org_table = self.config['DB']['db-tables']['orgs']

    if org_name in self.cached_orgs:
      return self.cached_orgs[org_name]
    else:
      org = self.get(org_table, org_id_column, {org_name_column: org_name})
      org_id = None

      if org:
        org_id = org[0][org_id_column]
      else:
        self.insert(org_table, {org_name_column: org_name})
        org = self.get(org_table, org_id_column, {org_name_column: org_name})
        org_id = org[0][org_id_column]

      return org_id
  
  def _added_device(self, device_id):
    device_id_table = self.db_columns['devices'][0]
    resp = self.get(self.db_tables['devices'], device_id_table, {device_id_table: device_id})
    if resp is not None and resp != []:
      return True

    return False

  def _shorten_org_name(self, org_name):
    abbreviated_orgs = self.config['org-abbreviations']
    if abbreviated_orgs.get(org_name):
      return abbreviated_orgs[org_name]

    return org_name
  
  def _package_device_insertion_data(self, data):
    org_columns = self.config['DB']['db-columns']['orgs']
    org_id_key = org_columns[0]
    org_name_field = self.device_filter[3][1]
    org_name = data.pop(org_name_field)
    org_shortened_name = self._shorten_org_name(org_name)
    
    data[org_id_key] = self._get_org_id(org_shortened_name)
    data = self._add_device_model_details(data)
    return data

  def _add_device_model_details(self, data):
    id_key = self.device_filter[0][1]
    endpoint = self.config['API']['api-endpoints']['devices']['endpoint'] + str(data[id_key]) + '/assets'
    asset_data = self.api.get(endpoint)
    self.logger.info("Attempting to add device model and manufacturer.")

    if asset_data:
      asset_data = asset_data['data']
      if asset_data.get("computersystem"):
        asset_data = asset_data["computersystem"]
        if asset_data.get("model"):
          data['model'] = asset_data["model"]
        if asset_data.get("manufacturer"):
          data['manufacturer'] = asset_data["manufacturer"]

    return data
  
  def _device_name_changed(self, device_id, new_name):
    device_id_column = self.db_columns['devices'][0]
    device_name_column = self.db_columns['devices'][1]
    device = self.get(self.db_tables['devices'], device_name_column, {device_id_column: device_id})
    if device and device != [] and device[0][device_name_column] != new_name:
      return True
    
    return False