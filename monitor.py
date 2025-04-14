from emailer import Emailer
from helpers.utils import logger_setup
from helpers.config_loader import ConfigLoader

import subprocess
import time
import sys
from datetime import datetime, timedelta

SCRIPT_PATH = "main.py"
ERROR_LOG_PATH = "logs/log_files/error.log"

def check_api(logger, emailer, opened_expired_ticket, opened_graph_ticket, last_daily_check, ran_once):
  now = datetime.now()
  if (now - last_daily_check >= timedelta(days=1)) or (ran_once == 0):
    ran_once = 1

    logger.info(f"Checking API and Graph expiry for: {now}")
    config = ConfigLoader() # "Reload" config to check for updates to "expires" instead of using already existing obj
    api_expiration = config["API"]["expires"]
    graph_expiration = config["microsoft-graph"]["expires"]
    last_daily_check = now
    api_expired = is_expired(api_expiration)
    graph_expired = is_expired(graph_expiration)
    
    if api_expired and not opened_expired_ticket:
      logger.info(f"API Key expired. Opening ticket.")
      emailer.send('api')
      opened_expired_ticket = True
    elif not api_expired:
      opened_expired_ticket = False
    
    if graph_expired and not opened_graph_ticket:
      logger.info(f"Microsoft graph expired. Opening ticket.")
      emailer.send('graph')
      opened_graph_ticket = True
    elif not graph_expired:
      graph_expired = False
  
  return opened_expired_ticket, opened_graph_ticket, last_daily_check

def is_expired(expires):
  expires = datetime.strptime(expires, "%Y-%m-%d").date()
  today = datetime.today().date()
  buffer = 3
  warn = expires - timedelta(days=buffer)

  if today >= warn:
    return True
  else:
    return False

def is_script_running():
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
  opened_expired_ticket = False
  opened_graph_ticket = False
  last_daily_check = datetime.now()
  max_retires = config['monitor']['max-retries']
  wait_time = config['monitor']['wait-time']

  retry_count = 0
  ran_once = 0

  while True:
    opened_expired_ticket, opened_graph_ticket, last_daily_check = check_api(logger, emailer, opened_expired_ticket, opened_graph_ticket, last_daily_check, ran_once)
    ran_once = 1

    if not is_script_running():
      if retry_count < max_retires:
        logger.error("Data grabber is no longer running. Attemping to restart...")

        if not opened_ticket:
          emailer.send('fail')
          opened_ticket = True

        start_script(logger)
        retry_count += 1
        time.sleep(15)
      else:
        logger.error(f"Max retires reached. Failed to restart script. Now sleeping for {wait_time} minutes before attempting again.")
        retry_count = 0
        time.sleep(wait_time * 60)
    else:
      opened_ticket = False
      retry_count = 0

    time.sleep(60)

if __name__ == "__main__":
  monitor()
