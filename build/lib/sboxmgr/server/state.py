import json
import os
import datetime

def load_selected_config():
    """Load selected configuration from file."""
    SELECTED_CONFIG_FILE = os.getenv("SBOXMGR_SELECTED_CONFIG_FILE", "./selected_config.json")
    if os.path.exists(SELECTED_CONFIG_FILE):
        with open(SELECTED_CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {"last_modified": "", "selected": []}

def save_selected_config(selected):
    """Save selected configuration to file."""
    SELECTED_CONFIG_FILE = os.getenv("SBOXMGR_SELECTED_CONFIG_FILE", "./selected_config.json")
    selected["last_modified"] = datetime.datetime.now(datetime.UTC).isoformat().replace("+00:00", "Z")
    with open(SELECTED_CONFIG_FILE, 'w') as f:
        json.dump(selected, f, indent=2) 