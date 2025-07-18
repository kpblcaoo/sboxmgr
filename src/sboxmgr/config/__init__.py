"""Configuration management package for SBoxMgr.

This package handles application configuration and settings.
"""

# This file indicates that the package supports type checking
# See PEP 561 for more details

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
