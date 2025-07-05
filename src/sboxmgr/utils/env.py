"""Environment variable utilities for sboxmgr.

Supported environment variables:
- SBOXMGR_LOG_FILE: Log file path
- SBOXMGR_CONFIG_FILE: Sing-box config file path  
- SBOXMGR_BACKUP_FILE: Backup config file path
- SBOXMGR_TEMPLATE_FILE: Template config file path
- SBOXMGR_EXCLUSION_FILE: Exclusions file path
- SBOXMGR_SELECTED_CONFIG_FILE: Selected config file path
- SBOXMGR_MAX_LOG_SIZE: Maximum log file size in bytes
- SBOXMGR_DEBUG: Debug level (0-2)
- SBOXMGR_URL: Subscription URL (alias: SINGBOX_URL, TEST_URL)
- SBOXMGR_FETCH_TIMEOUT: HTTP request timeout in seconds (default: 30)
- SBOXMGR_FETCH_SIZE_LIMIT: Maximum fetch size in bytes (default: 2MB)
"""

import os
from pathlib import Path

def get_log_file():
    """Get log file path with safe defaults.
    
    Priority:
    1. SBOXMGR_LOG_FILE environment variable (explicit path)
    2. ~/.local/share/sboxmgr/sboxmgr.log (user data directory)
    3. ./sboxmgr.log (current directory fallback)
    
    Returns:
        str: Log file path

    """
    if os.getenv("SBOXMGR_LOG_FILE"):
        return os.getenv("SBOXMGR_LOG_FILE")
    
    # Try user data directory first (XDG Base Directory spec)
    try:
        user_data_dir = Path.home() / ".local" / "share" / "sboxmgr"
        user_data_dir.mkdir(parents=True, exist_ok=True)
        log_path = user_data_dir / "sboxmgr.log"
        # Test if we can write to this location
        test_file = user_data_dir / ".write_test"
        test_file.touch()
        test_file.unlink()
        return str(log_path)
    except (OSError, PermissionError):
        # Fallback to current directory if user data dir is not writable
        return "./sboxmgr.log"

def get_config_file():
    """Get sing-box configuration file path.
    
    Returns:
        str: Configuration file path from SBOXMGR_CONFIG_FILE environment
             variable or default '/etc/sing-box/config.json'.

    """
    # Default matches sing-box config location
    return os.getenv("SBOXMGR_CONFIG_FILE", "/etc/sing-box/config.json")

def get_backup_file():
    """Get backup configuration file path.
    
    Returns:
        str: Backup file path from SBOXMGR_BACKUP_FILE environment
             variable or default '/etc/sing-box/config.json.bak'.

    """
    # Default matches sing-box config location
    return os.getenv("SBOXMGR_BACKUP_FILE", "/etc/sing-box/config.json.bak")

def get_template_file():
    """Get configuration template file path.
    
    Returns:
        str: Template file path from SBOXMGR_TEMPLATE_FILE environment
             variable or default './config.template.json'.

    """
    return os.getenv("SBOXMGR_TEMPLATE_FILE", "./config.template.json")

def get_exclusion_file():
    """Get server exclusions file path.
    
    Returns:
        str: Exclusions file path from SBOXMGR_EXCLUSION_FILE environment
             variable or default './exclusions.json'.

    """
    return os.getenv("SBOXMGR_EXCLUSION_FILE", "./exclusions.json")

def get_selected_config_file():
    """Get selected configuration file path.
    
    Returns:
        str: Selected config file path from SBOXMGR_SELECTED_CONFIG_FILE
             environment variable or default './selected_config.json'.

    """
    return os.getenv("SBOXMGR_SELECTED_CONFIG_FILE", "./selected_config.json")

def get_max_log_size():
    """Get maximum log file size in bytes.
    
    Returns:
        int: Maximum log size from SBOXMGR_MAX_LOG_SIZE environment
             variable or default 1048576 (1MB).

    """
    return int(os.getenv("SBOXMGR_MAX_LOG_SIZE", "1048576"))

def get_debug_level(default=0):
    """Get debug verbosity level.
    
    Args:
        default: Default debug level if environment variable not set.
        
    Returns:
        int: Debug level from SBOXMGR_DEBUG environment variable or default.

    """
    return int(os.getenv("SBOXMGR_DEBUG", str(default)))

def get_fetch_timeout():
    """Get HTTP request timeout in seconds.
    
    Environment variable: SBOXMGR_FETCH_TIMEOUT
    Default: 30 seconds
    
    Returns:
        int: Request timeout in seconds

    """
    try:
        return int(os.getenv("SBOXMGR_FETCH_TIMEOUT", "30"))
    except ValueError:
        return 30

def get_fetch_size_limit():
    """Get maximum fetch size limit in bytes.
    
    Environment variable: SBOXMGR_FETCH_SIZE_LIMIT  
    Default: 2MB (2097152 bytes)
    
    Returns:
        int: Size limit in bytes

    """
    try:
        return int(os.getenv("SBOXMGR_FETCH_SIZE_LIMIT", "2097152"))
    except ValueError:
        return 2097152

def get_url():
    """Get subscription URL from environment variables.
    
    Checks multiple environment variables in order of preference:
    SBOXMGR_URL, SINGBOX_URL, TEST_URL.
    
    Returns:
        str or None: Subscription URL if found in environment variables.

    """
    return os.getenv("SBOXMGR_URL") or os.getenv("SINGBOX_URL") or os.getenv("TEST_URL") 