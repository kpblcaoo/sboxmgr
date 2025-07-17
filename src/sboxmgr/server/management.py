"""Server management and configuration persistence.

This module handles server configuration management including saving selected
configurations, managing server state, and providing utilities for server
lifecycle management. It includes atomic file operations for safe configuration
updates.
"""

import datetime
import json
import logging
import os

from sboxmgr.utils.file import handle_temp_file as atomic_handle_temp_file
from sboxmgr.utils.id import generate_server_id

SELECTED_CONFIG_FILE = os.getenv(
    "SINGBOX_SELECTED_CONFIG_FILE", "./selected_config.json"
)


def list_servers(json_data, supported_protocols, debug_level=0, dry_run=False):
    """List all supported outbounds with indices and details."""
    servers = json_data.get("outbounds", json_data)
    logging.info("Index | Name | Protocol | Port")
    logging.info("--------------------------------")
    for index, server in enumerate(servers):
        if server.get("type") not in supported_protocols:
            continue
        name = server.get("tag", "N/A")
        protocol = server.get("type", "N/A")
        port = server.get("server_port", "N/A")
        logging.info(f"{index} | {name} | {protocol} | {port}")


def load_selected_config():
    """Load selected configuration from file."""
    if os.path.exists(SELECTED_CONFIG_FILE):
        with open(SELECTED_CONFIG_FILE) as f:
            return json.load(f)
    return {"last_modified": "", "selected": []}


def save_selected_config(selected):
    """Save selected server configuration to persistent storage.

    Saves the selected server configuration with a timestamp and performs
    atomic file operations to ensure data integrity during writes.

    Args:
        selected: Dictionary containing selected server configuration data.

    """
    selected["last_modified"] = (
        datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
    )
    atomic_handle_temp_file(
        selected, SELECTED_CONFIG_FILE, lambda x: True
    )  # Add proper validation


def apply_exclusions(configs, excluded_ids, debug_level):
    """Apply exclusions to the list of server configurations."""
    valid_configs = []
    for _idx, config in enumerate(configs):
        server_id = generate_server_id(config)
        if server_id in excluded_ids:
            if debug_level >= 1:
                logging.info(
                    f"Skipping server {config.get('name', 'N/A')} (ID: {server_id}) due to exclusion."
                )
            continue
        valid_configs.append(config)
    return valid_configs
