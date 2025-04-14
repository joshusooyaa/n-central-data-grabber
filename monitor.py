from emailer import Emailer
from helpers.utils import logger_setup
from helpers.config_loader import ConfigLoader

import subprocess
import time
import sys

SCRIPT_PATH = "main.py"
ERROR_LOG_PATH = "logs/log_files/error.log"

def is_script_running(logger):
  result = subprocess.run(["pgrep", "-f", SCRIPT_PATH], capture_output=True, text=True)
  return bool(result.stdout.strip())

def start_script(logger):
  venv_python = sys.executable
  #with open("/dev/null", "w") as devnull:
  #  process = subprocess.Popen(
  #    [venv_python, SCRIPT_PATH],
  #    stdout=devnull,
  #    stderr=devnull,
  #    preexec_fn=os.setpgrp
  #  )
  try:
    process = subprocess.Popen([venv_python, SCRIPT_PATH])
    logger.info(f"Process: {process}")
  except Exception as e:
    logger.error(f"Failed to start script {SCRIPT_PATH}. Exception {e}")
  return process

def monitor():
  config = ConfigLoader()
  logger, _ = logger_setup()
  emailer = Emailer(config, logger)
  opened_ticket = False
  max_retires = config['monitor']['max-retries']
  wait_time = config['monitor']['wait-time']

  retry_count = 0
  
  # Fallback just in case something goes wrong, prevent opening too many tickets
  max_sends = 100 
  sends = 0 
  while True:
    if not is_script_running(logger):
      if retry_count < max_retires:
        if not opened_ticket and sends < max_sends:
          emailer.send()
          sends += 1
          opened_ticket = True
        logger.error("Data grabber is no longer running. Attemping to restart...")
        start_script(logger)
        retry_count += 1
        time.sleep(15)
      else:
        logger.error(f"Max retires reached. Failed to restart script. Now sleeping for {wait_time} minutes before attempting again.")
        retry_count = 0
        time.sleep(wait_time * 60)

        if not opened_ticket and sends < max_sends:
          emailer.send()
          sends += 1
          opened_ticket = True
    else:
      opened_ticket = False
      retry_count = 0

    time.sleep(60)

if __name__ == "__main__":
  monitor()
