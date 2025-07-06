"""Configuration system for sboxmgr.

This module provides hierarchical configuration management using Pydantic BaseSettings.
Configuration sources are resolved in order: CLI args > env vars > config file > defaults.

Key features:
- Type-safe configuration with validation
- Service mode auto-detection
- Environment variable support with nested delimiter
- JSON schema generation for documentation
"""

from .detection import (
    detect_container_environment,
    detect_service_mode,
    get_environment_info,
)
from .loader import find_config_file, load_config, load_config_file, save_config
from .models import AppConfig, AppSettings, LoggingConfig, ServiceConfig

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
