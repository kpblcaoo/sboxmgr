"""Configuration system for sboxmgr.

This module provides hierarchical configuration management using Pydantic BaseSettings.
Configuration sources are resolved in order: CLI args > env vars > config file > defaults.

Key features:
- Type-safe configuration with validation
- Service mode auto-detection
- Environment variable support with nested delimiter
- JSON schema generation for documentation
"""

from .models import AppConfig, LoggingConfig, ServiceConfig, AppSettings
from .loader import load_config, load_config_file, find_config_file, save_config
from .detection import detect_service_mode, detect_container_environment, get_environment_info

__all__ = [
    "AppConfig",
    "AppSettings",
    "LoggingConfig", 
    "ServiceConfig",
    "load_config",
    "load_config_file",
    "find_config_file",
    "save_config",
    "detect_service_mode",
    "detect_container_environment",
    "get_environment_info",
] 