import logging
import os
import sys
from datetime import datetime, timezone, timedelta

# ==============================
# CONFIGURATION
# ==============================
LOG_DIR = "logs"
ALL_LOG_FILE = "all.log"
ERROR_LOG_FILE = "error.log"
WARNING_LOG_FILE = "warning.log" # <--- NEW FILE

# Define Dhaka Timezone (UTC+6)
DHAKA_OFFSET = timezone(timedelta(hours=6))

class DhakaFormatter(logging.Formatter):
    """
    Custom Formatter to force Asia/Dhaka time (UTC+6)
    and 12-hour AM/PM format.
    """
    def converter(self, timestamp):
        dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        return dt.astimezone(DHAKA_OFFSET)

    def formatTime(self, record, datefmt=None):
        dt = self.converter(record.created)
        if datefmt:
            return dt.strftime(datefmt)
        else:
            return dt.strftime("%Y-%m-%d %I:%M:%S %p")

class ColorFormatter(DhakaFormatter):
    """
    Adds colors to the console output.
    """
    GREY = "\x1b[38;20m"
    GREEN = "\x1b[32;20m"
    YELLOW = "\x1b[33;20m"
    RED = "\x1b[31;20m"
    BOLD_RED = "\x1b[31;1m"
    RESET = "\x1b[0m"

    FORMAT = "[%(asctime)s] [%(levelname)s] %(message)s"

    FORMATS = {
        logging.DEBUG: GREY + FORMAT + RESET,
        logging.INFO: GREEN + FORMAT + RESET,
        logging.WARNING: YELLOW + FORMAT + RESET,
        logging.ERROR: RED + FORMAT + RESET,
        logging.CRITICAL: BOLD_RED + FORMAT + RESET
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt="%Y-%m-%d %I:%M:%S %p")
        formatter.converter = self.converter
        formatter.formatTime = self.formatTime
        return formatter.format(record)

def setup_logger(name="MainLogger"):
    """
    Sets up the logger with 4 handlers:
    1. Console (Colored)
    2. all.log (INFO+)
    3. warning.log (WARNING+)
    4. error.log (ERROR+)
    """
    
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG) 

    if logger.hasHandlers():
        logger.handlers.clear()

    # Formatter for Files
    file_fmt_str = "[%(asctime)s] [%(levelname)s] %(message)s"
    file_formatter = DhakaFormatter(file_fmt_str, datefmt="%Y-%m-%d %I:%M:%S %p")

    # Formatter for Console
    console_formatter = ColorFormatter()

    # --- HANDLER 1: all.log ---
    all_log_path = os.path.join(LOG_DIR, ALL_LOG_FILE)
    file_handler_all = logging.FileHandler(all_log_path, mode='a', encoding='utf-8')
    file_handler_all.setLevel(logging.INFO)
    file_handler_all.setFormatter(file_formatter)

    # --- HANDLER 2: warning.log (NEW) ---
    # Captures WARNING, ERROR, and CRITICAL
    warning_log_path = os.path.join(LOG_DIR, WARNING_LOG_FILE)
    file_handler_warning = logging.FileHandler(warning_log_path, mode='a', encoding='utf-8')
    file_handler_warning.setLevel(logging.WARNING) 
    file_handler_warning.setFormatter(file_formatter)

    # --- HANDLER 3: error.log ---
    # Captures only ERROR and CRITICAL
    error_log_path = os.path.join(LOG_DIR, ERROR_LOG_FILE)
    file_handler_error = logging.FileHandler(error_log_path, mode='a', encoding='utf-8')
    file_handler_error.setLevel(logging.ERROR)
    file_handler_error.setFormatter(file_formatter)

    # --- HANDLER 4: Console ---
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)

    # Add all handlers
    logger.addHandler(file_handler_all)
    logger.addHandler(file_handler_warning)
    logger.addHandler(file_handler_error)
    logger.addHandler(console_handler)

    return logger