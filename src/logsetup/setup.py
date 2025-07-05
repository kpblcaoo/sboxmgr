"""Logging setup module for SBoxMgr."""

import logging
import logging.handlers
import os
from sboxmgr.utils.env import get_log_file, get_max_log_size, get_debug_level

def setup_logging(debug_level=None, log_file=None, max_log_size=None):
    """Configure logging with file and syslog handlers."""
    if debug_level is None:
        debug_level = get_debug_level()
    if log_file is None:
        log_file = get_log_file()
    if max_log_size is None:
        max_log_size = get_max_log_size()

    logger = logging.getLogger()

    if debug_level == 2:
        logger.setLevel(logging.DEBUG)
    elif debug_level == 1:
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.WARNING)

    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(logging.Formatter("[%(asctime)s] %(message)s", "%Y-%m-%d %H:%M:%S"))
    logger.addHandler(file_handler)

    try:
        syslog_handler = logging.handlers.SysLogHandler(address="/dev/log")
        syslog_handler.setFormatter(logging.Formatter("sing-box-update: %(message)s"))
        logger.addHandler(syslog_handler)
    except OSError as e:
        logging.warning(f"Failed to configure syslog handler: {e}")

    rotate_logs(log_file, max_log_size)

def rotate_logs(log_file, max_log_size):
    """Rotate log file if it exceeds max_log_size.
    
    Args:
        log_file: Path to log file
        max_log_size: Maximum size in bytes before rotation
        
    """
    if not os.path.exists(log_file):
        return
    log_size = os.path.getsize(log_file)
    if log_size > max_log_size:
        for i in range(5, 0, -1):
            old_log = f"{log_file}.{i}"
            new_log = f"{log_file}.{i+1}"
            if os.path.exists(old_log):
                os.rename(old_log, new_log)
        os.rename(log_file, f"{log_file}.1")
        open(log_file, "a").close()
