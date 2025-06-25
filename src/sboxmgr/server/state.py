"""Server state management and tracking.

This module provides utilities for tracking server state, availability, and
performance metrics. It manages persistent state information about servers
including connection success rates, latency measurements, and historical
performance data.
"""

import json
import logging
from sboxmgr.utils.env import get_selected_config_file
from sboxmgr.utils.file import atomic_write_json, file_exists, read_json

def load_selected_config():
    """Load selected configuration from file."""
    SELECTED_CONFIG_FILE = get_selected_config_file()
    if file_exists(SELECTED_CONFIG_FILE):
        try:
            return read_json(SELECTED_CONFIG_FILE)
        except json.JSONDecodeError:
            logging.error(f"Файл {SELECTED_CONFIG_FILE} повреждён или невалиден. Сброшен до пустого состояния.")
            return {"selected": []}
    return {"selected": []}

def save_selected_config(data, selected_config_file=None):
    """Save selected configuration to file."""
    if selected_config_file is None:
        selected_config_file = get_selected_config_file()
    atomic_write_json(data, selected_config_file) 