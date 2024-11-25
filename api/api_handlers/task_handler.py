class TaskHandler:
  def __init__(self, config, logger, api, tasks, device_id):
    self.device = device_id
    self.endpoint = config['API']['api-endpoints']['tasks']['endpoint']
    self.tasks_filter = config['API']['api-endpoints']['tasks']['task-filter']['info']
    self.data_row_name = config['API']['api-endpoints']['tasks']['data-filter']['data-row-name']
    self.data_filter = config['API']['api-endpoints']['tasks']['data-filter']['info']
    self.modules = config['API']['api-endpoints']['tasks']['data-filter']['module-names']
    self.generic_modules = config['API']['api-endpoints']['tasks']['data-filter']['generic-modules']
    self.unwanted_sub_modules = config['API']['api-endpoints']['tasks']['data-filter']['unwanted-sub-modules']
    self.wanted_sub_modules = config['API']['api-endpoints']['tasks']['data-filter']['wanted-sub-modules']

    self.logger = logger
    self.tasks = self._filter_task_info(tasks)
    self.api = api
    self.raw_data = {self.device: [], 'scanTime': None}

  def _filter_raw_data(self, data):
    description_key = self.data_filter[1][0]
    if (len(data['serviceDetails']) > 0):
      for detail in data['serviceDetails']:
        if not any(module in detail[self.data_row_name] or module in detail[description_key].lower() for module in self.unwanted_sub_modules):
          if any(module in detail[self.data_row_name] or module in detail[description_key].lower() for module in self.wanted_sub_modules) or len(self.wanted_sub_modules) == 0:
            self.raw_data[self.device].append({
              detail.get(self.data_row_name): {
                new_key: detail.get(key) for key, new_key in self.data_filter
              }
            })

    if data.get('scanTime'):
      self.raw_data['scanTime'] = data['scanTime']

  def _is_task_to_get(self, task, task_name):
    if len(self.modules) == 0 or task_name in self.modules:
      return True
    elif any(generic in task_name for generic in self.generic_modules):
      return True
    
    return False

  def _get_raw_data(self):
    task_id_key = self.tasks_filter[0]
    module_name_key = self.tasks_filter[2]
    task_ident_key = self.tasks_filter[3]
    task_name = task[module_name_key]
  
    for task in self.tasks:
      if self._is_task_to_get(task, task_name):
        resp = self.api.get(self.endpoint + f'{task[task_id_key]}')
        if (resp):
          if task_name == 'Disk':
            resp = self._add_info(resp, task[task_ident_key], field='diskName')

          self._filter_raw_data(resp)
    
    return self.raw_data
  
  def _add_info(self, data, diskName, field):
    for detail in data['serviceDetails']:
      detail[field] = diskName
    
    return data

  def _filter_task_info(self, tasks):
    task_list = []
    for task in tasks:
      task_list.append({
        key: task.get(key) for key in self.tasks_filter
      })

    return task_list
  
  def get_raw_data(self):
    return self._get_raw_data()

  def get_scan_time(self):
    return self.scan_time