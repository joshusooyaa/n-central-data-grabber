import logging
import logging.config
import os
from helpers.utils import ConfigLoader


def logger_setup(logs='logs/log_files/log.log', errors='logs/log_files/error.log', runs='logs/log_files/completed.log'):
  config = ConfigLoader()
  log_size = config['logging']['max-log-size']
  backup_count = config['logging']['backup-count']
  log_dir = os.path.dirname(logs)
  if not os.path.exists(log_dir):
    os.makedirs(log_dir)

  if not os.path.exists(runs):
    with open(runs, 'w') as f:
      f.write('runs_completed: 0\nruns_failed: 0\n')

  def update_run_count(completed=True):
    with open(runs, 'r+') as f:
      lines = f.readlines()
      completed_runs = int(lines[0].split(': ')[1].strip())
      failed_runs = int(lines[1].split(': ')[1].strip())

      if completed:
        completed_runs += 1
      else:
        failed_runs += 1
    
      f.seek(0)
      f.write(f'runs_completed: {completed_runs}\nruns_failed: {failed_runs}\n')
      f.truncate()

      return completed_runs

  logging_config = {
    'version': 1,
    'formatters': {
        'detailed': {
            'format': '[%(filename)-20s Line: %(lineno)-3d] - %(asctime)s - %(levelname)5s - %(message)s',
        },
    },
    'handlers': {
        'log_file_handler': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': logs,
            'level': 'INFO',
            'formatter': 'detailed',
            'maxBytes': log_size*1024*1024,
            'backupCount': backup_count,
        },
        'error_file_handler': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': errors,
            'mode': 'a',
            'level': 'WARNING',
            'formatter': 'detailed',
            'maxBytes': log_size*1024*1024,
            'backupCount': backup_count,
        },
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'detailed',
        },
    },
    'loggers': {
        '': {
            'handlers': ['log_file_handler', 'error_file_handler', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
    'disable_existing_loggers': False,
  }
  logging.config.dictConfig(logging_config)
  return logging.getLogger(__name__), update_run_count