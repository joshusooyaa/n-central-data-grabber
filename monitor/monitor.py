from emailer import Emailer
from ..logs.log_handler import logger_setup
from ..helpers.config_loader import ConfigLoader

import subprocess

import time

SCRIPT_PATH = "../main.py"
ERROR_LOG_PATH = "../logs/log_files/error.log"

def is_script_running():
  result = subprocess.run(["pgrep", "-f", SCRIPT_PATH], capture_output=True, text=True)
  return bool(result.stdout.strip())

def start_script():
  return subprocess.Popen(["python3", SCRIPT_PATH])

def monitor():
  config = ConfigLoader()
  logger = logger_setup()
  emailer = Emailer(config, logger)
  max_retires = config['monitor']['max-retries']
  wait_time = config['monitor']['wait-time']
  
  retry_count = 0
  while True:
    if not is_script_running():
      if retry_count < max_retires:
        logger.error("Data grabber is no longer running. Attemping to restart...")
        start_script()
        retry_count += 1
        time.sleep()
      else:
        logger.error("Max retires reached.")
        retry_count = 0
        time.sleep(wait_time * 60)
        

if __name__ == "__monitor__":
  monitor()
