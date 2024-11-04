from helpers.utils import initialize_components, reinitialize_config, validate_config, log_process_summary, process_device_data
import time
import traceback

def main():
  logger, update_run_count, config, api, device_handler, db = initialize_components()

  if not validate_config(config, logger):
    return

  interval = config['script-interval']
  
  try:
    while True:
      loop_start_time = time.time()
      logger.info("================================================================")
      logger.info("Loop awoke from sleep. Beginning data extraction process.")
      logger.info("================================================================")

      logger.info("Reinitializing Config")
      config = reinitialize_config()

      db.connect()
      task_fetch_times, raw_data_fetch_times, insertion_times = process_device_data(device_handler, db, api, config, logger)
      db.close()

      run_count = update_run_count(True)
      time_to_sleep = log_process_summary(loop_start_time, task_fetch_times, raw_data_fetch_times, insertion_times, interval, logger, run_count)
      time.sleep(time_to_sleep)

  except Exception as e:
    logger.error("An error occurred: %s", str(e))
    logger.error(traceback.format_exc())
    update_run_count(False)
  
  finally:
    logger.info("\n==================================\n"
              "N-Central Data Extractor Ended\n"
              "==================================\n")

if __name__ == "__main__":
  main()
