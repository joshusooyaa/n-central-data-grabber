from api.api_client import APIClient
from helpers.config_loader import ConfigLoader
from api.api_handlers.device_handler import DeviceHandler
from api.api_handlers.task_handler import TaskHandler
from db.db_handler import DBHandler
from logs.log_handler import logger_setup
from datetime import datetime

import time

def param_cleaner(params):
  clean_params = []
  for k, v in params.items():
    if not k.startswith("_"):
      clean_params.append(v)

  if len(clean_params) > 1:
    return clean_params
  else:
    return clean_params[0]

def initialize_components():
  logger, update_run_count = logger_setup()
  logger.info("\n==================================\n"
              "  Beginning N-Central Data Extractor\n"
              "==================================\n")
  
  config = ConfigLoader()
  api = APIClient(config, logger)
  device_handler = DeviceHandler(config, logger, api)
  db = DBHandler(config, logger, api)
  
  return logger, update_run_count, config, api, device_handler, db

def reinitialize_config():
  return ConfigLoader()
 
def validate_config(config, logger):
  device_id_key = config['API']['api-endpoints']['devices']['device-filter']['info'][0][1]
  db_column_device_id = config['DB']['db-columns']['devices'][0]

  if db_column_device_id != device_id_key:
    logger.error(f"DB Column: {db_column_device_id} does not match device-filter {device_id_key}. "
                  "Please update your config file.")
    return False
  
  return True

def log_process_summary(loop_start_time, task_fetch_times, raw_data_fetch_times, insertion_times, interval, logger, run_count):
  avg_task_fetch_time = sum(task_fetch_times) / len(task_fetch_times)
  avg_raw_data_fetch_time = sum(raw_data_fetch_times) / len(raw_data_fetch_times)
  avg_insertion_time = sum(insertion_times) / len(insertion_times)
  duration = time.time() - loop_start_time
  time_to_sleep = max(0, interval - duration)

  logger.info("================================================================")
  logger.info(f"Loop ended on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
  logger.info(f"Average time spent on fetching tasks:    {avg_task_fetch_time:.4f} seconds")
  logger.info(f"Average time spent on fetching raw data: {avg_raw_data_fetch_time:.4f} seconds")
  logger.info(f"Average time spent on insertion:         {avg_insertion_time:.4f} seconds")
  logger.info(f"Time taken to complete: {duration:.2f} seconds.")
  logger.info(f"Total runs: {run_count}")
  logger.info(f"Now sleeping for {time_to_sleep:.2f} seconds.")
  logger.info("================================================================\n")
  
  return time_to_sleep

def process_device_data(device_handler, db, api, config, logger):
  devices = device_handler.get_devices()
  task_fetch_times = []
  raw_data_fetch_times = []
  insertion_times = []
  db_table_config = config['DB']['db-tables']
  device_id_key = config['API']['api-endpoints']['devices']['device-filter']['info'][0][1]

  logger.info("Beginning raw data insertion.")

  loop_begin_time = datetime.now()
  for device in devices:
    device_id = device[device_id_key]

    start_time = time.time()
    tasks = device_handler.get_device_tasks(device_id, loop_begin_time)
    task_duration = time.time() - start_time
    task_fetch_times.append(task_duration)

    start_time = time.time()
    task_handler = TaskHandler(config, logger, api, tasks, device_id)
    raw_data = task_handler.get_raw_data()
    raw_data_duration = time.time() - start_time
    raw_data_fetch_times.append(raw_data_duration)

    start_time = time.time()
    db.format_and_insert(db_table_config['devices'], device, db_table_config)
    db.format_and_insert(db_table_config['raw-data'], raw_data, db_table_config)
    insert_duration = time.time() - start_time
    insertion_times.append(insert_duration)

  logger.info("Raw data insertion complete.")
  return task_fetch_times, raw_data_fetch_times, insertion_times
