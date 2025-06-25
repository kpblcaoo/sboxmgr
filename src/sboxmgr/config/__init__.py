"""Configuration system for sboxmgr.

This module provides hierarchical configuration management using Pydantic BaseSettings.
Configuration sources are resolved in order: CLI args > env vars > config file > defaults.

Key features:
- Type-safe configuration with validation
- Service mode auto-detection
- Environment variable support with nested delimiter
- JSON schema generation for documentation
"""

from .models import AppConfig, LoggingConfig, ServiceConfig
from .loader import ConfigLoader, load_config
from .detection import detect_service_mode, detect_container_environment, get_environment_info
from .validation import validate_config_file, ConfigValidationError

__all__ = [
    "AppConfig",
    "LoggingConfig", 
    "ServiceConfig",
    "ConfigLoader",
    "load_config",
    "detect_service_mode",
    "detect_container_environment",
    "get_environment_info",
    "validate_config_file",
    "ConfigValidationError",
] 