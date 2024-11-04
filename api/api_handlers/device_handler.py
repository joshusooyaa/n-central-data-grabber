from datetime import datetime, timedelta

class DeviceHandler:
  def __init__(self, config, logger, api):
    from helpers.utils import param_cleaner
    self.endpoint = config['API']['api-endpoints']['devices']['endpoint']
    self.service_endpoint = config['API']['api-endpoints']['devices']['device-services']
    self.params = param_cleaner(config['API']['api-endpoints']['devices']['params'])
    self.device_filter = config['API']['api-endpoints']['devices']['device-filter']['info']
    self.time_format = config['API']['api-endpoints']['devices']['time-format']
    self.api = api
    self.logger = logger

  def _clean_str(self, val):
    if isinstance(val, str):
      return val.lower().replace('-','').replace(' ', '_')
    else:
      return val

  def _clean_device_response(self, devices):
    cleaned_list = []
    for device in devices:
      cleaned_list.append({
        new_key: device.get(key) for key, new_key in self.device_filter
      })

    return cleaned_list

  def _get_devices(self):
    devices = self.api.get(self.endpoint, self.params)
    return self._clean_device_response(devices['data'])
  
  def _fetch_newly_updated_tasks(self, tasks, start_time):
    updated_tasks = []
    for task in tasks['data']:
      if task.get('lastScanTime'):
        last_scan_time = datetime.strptime(task['lastScanTime'], self.time_format)
        # start_time = start_time.replace(tzinfo=last_scan_time.tzinfo)
        start_time = datetime.now(last_scan_time.tzinfo)
        if start_time - last_scan_time < timedelta(minutes=8):
          updated_tasks.append(task)

    return updated_tasks

  def _get_device_tasks(self, device_id, start_time):
    tasks = self.api.get(self.endpoint + f"{device_id}/" + self.service_endpoint)
    tasks = self._fetch_newly_updated_tasks(tasks, start_time)
    return tasks

  def get_devices(self):
    devices = self._get_devices()
    return devices

  def get_device_tasks(self, device_id, start_time):
    return self._get_device_tasks(device_id, start_time)
