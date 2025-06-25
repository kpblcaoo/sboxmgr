"""Configuration loading and file handling.

Implements hierarchical configuration loading with support for:
- TOML configuration files
- Environment variable override
- CLI argument integration
- Validation and error handling
"""

import os
from pathlib import Path
from typing import Dict, Optional, Any
import toml
from pydantic import ValidationError

from .models import AppConfig
from .validation import validate_config_file, ConfigValidationError


class ConfigLoader:
    """Configuration loader with hierarchical resolution.
    
    Implements the configuration hierarchy from ADR-0009:
    CLI args > environment variables > config file > defaults
    """
    
    def __init__(self):
        self.config_search_paths = [
            Path.cwd() / "sboxmgr.toml",
            Path.cwd() / "config.toml", 
            Path.home() / ".config" / "sboxmgr" / "config.toml",
            Path("/etc/sboxmgr/config.toml"),
        ]
    
    def load(
        self,
        config_file_path: Optional[str] = None,
        cli_overrides: Optional[Dict[str, Any]] = None
    ) -> AppConfig:
        """Load configuration with hierarchical resolution.
        
        Args:
            config_file_path: Explicit config file path
            cli_overrides: CLI argument overrides
            
        Returns:
            AppConfig: Validated configuration object
            
        Raises:
            ConfigValidationError: If configuration is invalid
            ValidationError: If Pydantic validation fails
        """
        # 1. Start with base configuration (includes env vars)
        config_data = {}
        
        # 2. Load from config file
        if config_file_path:
            # Explicit config file
            file_data = self._load_config_file(config_file_path)
            config_data.update(file_data)
        else:
            # Search for config file in standard locations
            for search_path in self.config_search_paths:
                if search_path.exists():
                    file_data = self._load_config_file(str(search_path))
                    config_data.update(file_data)
                    config_data["config_file"] = str(search_path)
                    break
        
        # 3. Apply CLI overrides
        if cli_overrides:
            config_data.update(cli_overrides)
        
        # 4. Create and validate configuration
        try:
            # Let Pydantic handle environment variables automatically
            if config_data:
                config = AppConfig(**config_data)
            else:
                config = AppConfig()
            
            return config
            
        except ValidationError as e:
            raise ConfigValidationError(f"Configuration validation failed: {e}")
    
    def _load_config_file(self, file_path: str) -> Dict[str, Any]:
        """Load configuration from TOML file.
        
        Args:
            file_path: Path to configuration file
            
        Returns:
            Dict containing configuration data
            
        Raises:
            ConfigValidationError: If file cannot be loaded or parsed
        """
        try:
            # Validate file first
            validate_config_file(file_path)
            
            # Load TOML content
            with open(file_path, 'r') as f:
                config_data = toml.load(f)
            
            return config_data
            
        except toml.TomlDecodeError as e:
            raise ConfigValidationError(f"Invalid TOML syntax in {file_path}: {e}")
        
        except FileNotFoundError:
            raise ConfigValidationError(f"Configuration file not found: {file_path}")
        
        except PermissionError:
            raise ConfigValidationError(f"Cannot read configuration file: {file_path}")
        
        except Exception as e:
            raise ConfigValidationError(f"Error loading configuration file {file_path}: {e}")


def load_config(
    config_file_path: Optional[str] = None,
    cli_overrides: Optional[Dict[str, Any]] = None
) -> AppConfig:
    """Convenience function to load configuration.
    
    This is the primary entry point for configuration loading.
    
    Args:
        config_file_path: Optional explicit config file path
        cli_overrides: Optional CLI argument overrides
        
    Returns:
        AppConfig: Validated configuration object
    """
    loader = ConfigLoader()
    return loader.load(config_file_path=config_file_path, cli_overrides=cli_overrides)


def find_config_file() -> Optional[str]:
    """Find configuration file in standard locations.
    
    Returns:
        str: Path to configuration file if found, None otherwise
    """
    loader = ConfigLoader()
    for search_path in loader.config_search_paths:
        if search_path.exists() and search_path.is_file():
            return str(search_path)
    return None


def create_default_config_file(output_path: str) -> None:
    """Create a default configuration file template.
    
    Args:
        output_path: Path where to create the config file
        
    Raises:
        ConfigValidationError: If file cannot be created
    """
    default_config = {
        "debug": False,
        "verbose": False,
        
        "logging": {
            "level": "INFO",
            "format": "text",
            "sinks": ["auto"],
            "enable_trace_id": True,
        },
        
        "service": {
            "service_mode": False,
            "health_check_enabled": True,
            "health_check_port": 8080,
            "metrics_enabled": True,
            "metrics_port": 9090,
        }
    }
    
    try:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            toml.dump(default_config, f)
            
    except Exception as e:
        raise ConfigValidationError(f"Cannot create config file {output_path}: {e}")


def merge_cli_args_to_config(
    base_config: AppConfig,
    log_level: Optional[str] = None,
    debug: Optional[bool] = None,
    verbose: Optional[bool] = None,
    service_mode: Optional[bool] = None,
    config_file: Optional[str] = None
) -> AppConfig:
    """Merge CLI arguments into configuration.
    
    Helper function for CLI integration to override configuration
    with command-line arguments.
    
    Args:
        base_config: Base configuration object
        log_level: Override log level
        debug: Override debug mode
        verbose: Override verbose mode
        service_mode: Override service mode
        config_file: Override config file path
        
    Returns:
        AppConfig: Updated configuration object
    """
    config_dict = base_config.dict()
    
    # Apply CLI overrides
    if log_level is not None:
        config_dict["logging"]["level"] = log_level.upper()
    
    if debug is not None:
        config_dict["debug"] = debug
        if debug:
            config_dict["logging"]["level"] = "DEBUG"
    
    if verbose is not None:
        config_dict["verbose"] = verbose
    
    if service_mode is not None:
        config_dict["service"]["service_mode"] = service_mode
    
    if config_file is not None:
        config_dict["config_file"] = config_file
    
    # Create new configuration with overrides
    return AppConfig(**config_dict) 