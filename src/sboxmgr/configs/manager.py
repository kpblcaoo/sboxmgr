"""Config management system for sboxmgr.

This module provides the ConfigManager class for managing configs,
including creation, loading, validation, and active config management.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from pydantic import ValidationError

from .models import UserConfig


# Lazy logger initialization to avoid import-time logging setup requirement
def _get_logger():
    try:
        from ..logging.core import get_logger

        return get_logger(__name__)
    except RuntimeError:
        # Fallback to basic logging if not initialized
        import logging

        return logging.getLogger(__name__)


class ConfigInfo:
    """Information about a config file.

    Attributes:
        path: Path to the config file
        name: Config name (derived from filename)
        size: File size in bytes
        modified: Last modification time
        valid: Whether the config is valid
        error: Error message if config is invalid

    """

    def __init__(
        self,
        path: str,
        name: str,
        size: int,
        modified: datetime,
        valid: bool = True,
        error: Optional[str] = None,
    ):
        """Initialize ConfigInfo.

        Args:
            path: Path to the config file
            name: Config name (derived from filename)
            size: File size in bytes
            modified: Last modification time
            valid: Whether the config is valid
            error: Error message if config is invalid

        """
        self.path = path
        self.name = name
        self.size = size
        self.modified = modified
        self.valid = valid
        self.error = error


class ValidationResult:
    """Result of profile validation.

    Attributes:
        valid: Whether the profile is valid
        errors: List of validation errors
        warnings: List of validation warnings

    """

    def __init__(
        self,
        valid: bool = True,
        errors: Optional[list[str]] = None,
        warnings: Optional[list[str]] = None,
    ):
        """Initialize ValidationResult.

        Args:
            valid: Whether the profile is valid
            errors: List of validation errors
            warnings: List of validation warnings

        """
        self.valid = valid
        self.errors = errors or []
        self.warnings = warnings or []


class ConfigManager:
    """Central manager for config operations.

    This class provides methods for creating, loading, saving, and validating
    configs. It also manages the active config and provides config listing.

    Attributes:
        configs_dir: Directory for storing configs
        active_config: Currently active config
        config_cache: Cache of loaded configs

    """

    def __init__(self, configs_dir: Optional[str] = None):
        """Initialize the ConfigManager.

        Args:
            configs_dir: Directory for storing configs. If None, uses default.

        """
        self.configs_dir = Path(configs_dir or "~/.config/sboxmgr/configs").expanduser()
        self.configs_dir.mkdir(parents=True, exist_ok=True)

        self.active_config: Optional[UserConfig] = None
        self.config_cache: dict[str, UserConfig] = {}
        self.active_config_file = self.configs_dir / ".active_config"

        logger = _get_logger()
        if logger:
            logger.info(
                f"ConfigManager initialized with configs directory: {self.configs_dir}"
            )

        # Load active config from file
        self._load_active_config_from_file()

    def create_config(self, config_data: dict[str, Any]) -> UserConfig:
        """Create a new config from dictionary data.

        Args:
            config_data: Dictionary containing config data

        Returns:
            UserConfig: Created config

        Raises:
            ValidationError: If config data is invalid

        """
        logger = _get_logger()
        try:
            config = UserConfig(**config_data)
            if logger:
                logger.info(f"Created new config: {config.id}")
            return config
        except ValidationError as e:
            if logger:
                logger.error(f"Failed to create config: {e}")
            raise

    def get_active_config(self) -> Optional[UserConfig]:
        """Get the currently active config.

        Returns:
            UserConfig or None: Active config if set, None otherwise

        """
        return self.active_config

    def get_active_config_name(self) -> Optional[str]:
        """Get the name of currently active config.

        Returns:
            str or None: Active config name if set, None otherwise

        """
        if self.active_config:
            return self.active_config.id
        return None

    def set_active_config(self, config: UserConfig) -> None:
        """Set the active config and persist to file.

        Args:
            config: Config to set as active

        """
        self.active_config = config
        self._save_active_config_to_file(config.id)
        logger = _get_logger()
        if logger:
            logger.info(f"Set active config: {config.id}")

    def switch_config(self, config_name: str) -> bool:
        """Switch to a config by name with validation.

        Args:
            config_name: Name of config to switch to

        Returns:
            bool: True if switch was successful

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValidationError: If config is invalid
            Exception: For other errors (TOML syntax, etc.)

        """
        # Find config file
        config_path = None
        for ext in [".toml", ".json"]:
            path = self.configs_dir / f"{config_name}{ext}"
            if path.exists():
                config_path = path
                break

        if not config_path:
            raise FileNotFoundError(f"Config '{config_name}' not found")

        # Load and validate config
        try:
            config = self.load_config(str(config_path))

            # Additional validation
            if not config.id:
                raise ValidationError("Config ID cannot be empty")

            # Set as active
            self.set_active_config(config)
            return True

        except Exception as e:
            logger = _get_logger()
            if logger:
                logger.error(f"Failed to switch to config '{config_name}': {e}")
            raise

    def _load_active_config_from_file(self) -> None:
        """Load active config from persistent file."""
        logger = _get_logger()
        if not self.active_config_file.exists():
            # Try to set default config if available
            self._set_default_active_config()
            return

        try:
            with open(self.active_config_file, encoding="utf-8") as f:
                data = json.load(f)

            active_config_name = data.get("active_config")
            if active_config_name:
                # Try to load the config
                for ext in [".toml", ".json"]:
                    config_path = self.configs_dir / f"{active_config_name}{ext}"
                    if config_path.exists():
                        try:
                            self.active_config = self.load_config(str(config_path))
                            if logger:
                                logger.info(
                                    f"Loaded active config from file: {active_config_name}"
                                )
                            return
                        except Exception as e:
                            if logger:
                                logger.warning(
                                    f"Failed to load active config {active_config_name}: {e}"
                                )
                            break

            # If we get here, the saved active config is invalid
            self._set_default_active_config()

        except Exception as e:
            if logger:
                logger.warning(f"Failed to load active config file: {e}")
            self._set_default_active_config()

    def _save_active_config_to_file(self, config_name: str) -> None:
        """Save active config name to persistent file.

        Args:
            config_name: Name of active config to save

        """
        try:
            data = {
                "active_config": config_name,
                "last_updated": datetime.now().isoformat(),
            }
            with open(self.active_config_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            logger = _get_logger()
            if logger:
                logger.debug(f"Saved active config to file: {config_name}")

        except Exception as e:
            logger = _get_logger()
            if logger:
                logger.error(f"Failed to save active config to file: {e}")

    def _set_default_active_config(self) -> None:
        """Set default active config if available."""
        import traceback

        logger = _get_logger()

        if logger:
            logger.warning("[WARNING] _set_default_active_config called")
            logger.warning(f"[WARNING] Call stack: {traceback.format_stack()[-3:]}")

        # Look for default.toml or default.json
        for name in ["default", "home"]:
            for ext in [".toml", ".json"]:
                config_path = self.configs_dir / f"{name}{ext}"
                if config_path.exists():
                    try:
                        config = self.load_config(str(config_path))
                        self.active_config = config
                        self._save_active_config_to_file(config.id)
                        if logger:
                            logger.info(f"Set default active config: {config.id}")
                        return
                    except Exception as e:
                        if logger:
                            logger.warning(f"Failed to load default config {name}: {e}")

        # No default config found - create one
        if logger:
            logger.info("No default config found - creating default.toml")
        self._create_default_config()

    def _create_default_config(self) -> None:
        """Create default configuration file if none exists."""
        import traceback

        logger = _get_logger()

        if logger:
            logger.warning(
                "[WARNING] _create_default_config called - this will overwrite existing config!"
            )
            logger.warning(f"[WARNING] Call stack: {traceback.format_stack()[-3:]}")
        try:
            # Create default config data
            default_config_data: dict[str, Any] = {
                "id": "default",
                "description": "Default configuration for SBoxMgr",
                "version": "1.0",
                "subscriptions": [],
                "filters": {
                    "exclude_tags": [],
                    "only_tags": [],
                    "exclusions": [],
                    "only_enabled": True,
                },
                "routing": {
                    "default_route": "tunnel",
                    "by_source": {},
                    "custom_routes": {},
                },
                "export": {
                    "format": "sing-box",
                    "outbound_profile": "vless-real",
                    "inbound_profile": "tun",
                    "output_file": "config.json",
                },
                "agent": {
                    "auto_restart": False,
                    "monitor_latency": True,
                    "health_check_interval": "30s",
                    "log_level": "info",
                },
                "ui": {
                    "default_language": "en",
                    "mode": "cli",
                    "show_debug_info": False,
                },
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "metadata": {},
            }

            # Create config object
            config = UserConfig(**default_config_data)

            # Save as TOML
            default_config_path = self.configs_dir / "default.toml"
            from .toml_support import save_config_to_toml

            save_config_to_toml(config, default_config_path)

            # Set as active
            self.active_config = config
            self._save_active_config_to_file(config.id)

            if logger:
                logger.info(f"Created default config: {default_config_path}")

        except Exception as e:
            if logger:
                logger.error(f"Failed to create default config: {e}")

    def load_config(self, file_path: str) -> UserConfig:
        """Load a config from file.

        Args:
            file_path: Path to config file

        Returns:
            UserConfig: Loaded config

        Raises:
            FileNotFoundError: If file doesn't exist
            ValidationError: If config data is invalid

        """
        from .toml_support import load_config_auto

        return load_config_auto(file_path)

    def list_configs(self) -> list[ConfigInfo]:
        """List all available configs in the configs directory.

        Returns:
            List[ConfigInfo]: List of config information

        """
        logger = _get_logger()
        configs: list[ConfigInfo] = []

        if not self.configs_dir.exists():
            return configs

        for file_path in self.configs_dir.glob("*"):
            if file_path.suffix.lower() not in [".json", ".toml"]:
                continue

            try:
                stat = file_path.stat()
                name = file_path.stem

                # Try to validate the config
                try:
                    self.load_config(str(file_path))
                    valid = True
                    error = None
                except Exception as e:
                    valid = False
                    error = str(e)

                config_info = ConfigInfo(
                    path=str(file_path),
                    name=name,
                    size=stat.st_size,
                    modified=datetime.fromtimestamp(stat.st_mtime),
                    valid=valid,
                    error=error,
                )

                configs.append(config_info)

            except Exception as e:
                if logger:
                    logger.warning(f"Failed to get info for config {file_path}: {e}")

        if logger:
            logger.debug(f"Found {len(configs)} configs in {self.configs_dir}")
        return configs

    def clear_cache(self) -> None:
        """Clear the config cache."""
        self.config_cache.clear()
        logger = _get_logger()
        if logger:
            logger.debug("Config cache cleared")

    # Compatibility methods for old CLI code
    @property
    def profiles_dir(self) -> Path:
        """Get profiles directory (alias for configs_dir for compatibility).

        Returns:
            Path: Profiles directory path

        """
        return self.configs_dir

    def validate_profile(self, profile: UserConfig) -> ValidationResult:
        """Validate a profile (alias for config validation).

        Args:
            profile: Profile to validate

        Returns:
            ValidationResult: Validation result

        """
        try:
            # Basic validation - UserConfig already validates on creation
            # Additional custom validation can be added here
            return ValidationResult(valid=True)
        except Exception as e:
            return ValidationResult(valid=False, errors=[str(e)])

    def set_active_profile(self, profile: UserConfig) -> None:
        """Set active profile (alias for set_active_config).

        Args:
            profile: Profile to set as active

        """
        self.set_active_config(profile)

    def list_profiles(self) -> list[ConfigInfo]:
        """List profiles (alias for list_configs).

        Returns:
            List[ConfigInfo]: List of profile information

        """
        return self.list_configs()
