import os

def get_log_file():
    return os.getenv("SBOXMGR_LOG_FILE", "/var/log/sboxmgr.log")

def get_config_file():
    return os.getenv("SBOXMGR_CONFIG_FILE", "/etc/sboxmgr/config.json")

def get_backup_file():
    return os.getenv("SBOXMGR_BACKUP_FILE", "/etc/sboxmgr/config.json.bak")

def get_template_file():
    return os.getenv("SBOXMGR_TEMPLATE_FILE", "./config.template.json")

def get_exclusion_file():
    return os.getenv("SBOXMGR_EXCLUSION_FILE", "./exclusions.json")

def get_selected_config_file():
    return os.getenv("SINGBOX_SELECTED_CONFIG_FILE", "./selected_config.json")

def get_max_log_size():
    return int(os.getenv("SBOXMGR_MAX_LOG_SIZE", "1048576"))

def get_debug_level(default=0):
    return int(os.getenv("SBOXMGR_DEBUG", str(default)))

def get_url():
    return os.getenv("SBOXMGR_URL") or os.getenv("SINGBOX_URL") or os.getenv("TEST_URL") 