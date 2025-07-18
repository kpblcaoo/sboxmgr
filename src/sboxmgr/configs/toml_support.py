"""TOML support for sboxmgr configurations.

This module provides utilities for loading and saving configurations in TOML format,
which is more user-friendly than JSON for manual editing.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Union

import toml

from .models import UserConfig

# Optional logging - only if initialized
try:
    from ..logging.core import get_logger

    logger = get_logger(__name__)
except RuntimeError:
    logger = None


def load_config_from_toml(file_path: Union[str, Path]) -> UserConfig:
    """Load configuration from TOML file.

    Args:
        file_path: Path to TOML configuration file

    Returns:
        UserConfig: Loaded configuration

    Raises:
        FileNotFoundError: If file doesn't exist
        toml.TomlDecodeError: If TOML is invalid
        ValidationError: If config data is invalid

    """
    path = Path(file_path).expanduser().resolve()

    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {file_path}")

    if logger:
        logger.debug(f"Loading config from TOML: {path}")

    try:
        with open(path, encoding="utf-8") as f:
            toml_data = toml.load(f)

        # Convert TOML data to UserConfig
        config = UserConfig(**toml_data)
        if logger:
            logger.info(f"Successfully loaded config '{config.id}' from TOML")
        return config

    except toml.TomlDecodeError as e:
        if logger:
            logger.error(f"Invalid TOML syntax in {path}: {e}")
        raise
    except Exception as e:
        if logger:
            logger.error(f"Failed to load config from {path}: {e}")
        raise


def save_config_to_toml(config: UserConfig, file_path: Union[str, Path]) -> None:
    """Save configuration to TOML file.

    Args:
        config: Configuration to save
        file_path: Path where to save the TOML file

    """
    path = Path(file_path).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)

    if logger:
        logger.debug(f"Saving config to TOML: {path}")

    try:
        # Convert config to dictionary and add metadata
        config_dict = config.model_dump(exclude_none=True)
        config_dict["updated_at"] = datetime.now().isoformat()

        # Create TOML content with comments
        toml_content = _create_toml_with_comments(config_dict)

        with open(path, "w", encoding="utf-8") as f:
            f.write(toml_content)

        if logger:
            logger.info(f"Successfully saved config '{config.id}' to TOML")

    except Exception as e:
        if logger:
            logger.error(f"Failed to save config to {path}: {e}")
        raise


def _create_toml_with_comments(config_dict: dict[str, Any]) -> str:
    """Create TOML content with helpful comments.

    Args:
        config_dict: Configuration dictionary

    Returns:
        str: TOML content with comments

    """
    lines = []

    # Header comment
    lines.append("# sboxmgr User Configuration")
    lines.append("# Generated on: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    lines.append("")

    # Basic info
    if "id" in config_dict:
        lines.append(f'id = "{config_dict["id"]}"')
    if "description" in config_dict:
        lines.append(f'description = "{config_dict["description"]}"')
    if "version" in config_dict:
        lines.append(f'version = "{config_dict["version"]}"')
    lines.append("")

    # Subscriptions section
    if "subscriptions" in config_dict and config_dict["subscriptions"]:
        lines.append("# Subscription configurations")
        for sub in config_dict["subscriptions"]:
            lines.append("[[subscriptions]]")
            lines.append(f'id = "{sub["id"]}"')
            lines.append(f"enabled = {str(sub.get('enabled', True)).lower()}")
            lines.append(f"priority = {sub.get('priority', 1)}")
            lines.append("")

    # Filters section
    if "filters" in config_dict:
        lines.append("# Filtering and exclusion rules")
        lines.append("[filters]")
        filters = config_dict["filters"]
        if filters.get("exclude_tags"):
            lines.append(f"exclude_tags = {json.dumps(filters['exclude_tags'])}")
        if filters.get("only_tags"):
            lines.append(f"only_tags = {json.dumps(filters['only_tags'])}")
        if filters.get("exclusions"):
            lines.append(f"exclusions = {json.dumps(filters['exclusions'])}")
        lines.append(f"only_enabled = {str(filters.get('only_enabled', True)).lower()}")
        lines.append("")

    # Routing section
    if "routing" in config_dict:
        lines.append("# Routing configuration")
        lines.append("[routing]")
        routing = config_dict["routing"]
        lines.append(f'default_route = "{routing.get("default_route", "tunnel")}"')
        if routing.get("by_source"):
            lines.append("[routing.by_source]")
            for source, route in routing["by_source"].items():
                lines.append(f'"{source}" = "{route}"')
        if routing.get("custom_routes"):
            lines.append("[routing.custom_routes]")
            for domain, route in routing["custom_routes"].items():
                lines.append(f'"{domain}" = "{route}"')
        lines.append("")

    # Export section
    if "export" in config_dict:
        lines.append("# Export settings")
        lines.append("[export]")
        export = config_dict["export"]
        format_val = export.get("format", "sing-box")
        # Handle enum values
        if hasattr(format_val, "value"):
            format_val = format_val.value
        elif str(format_val).startswith("ExportFormat."):
            format_val = format_val.split(".")[-1].lower().replace("_", "-")
        lines.append(f'format = "{format_val}"')
        if export.get("output_file"):
            lines.append(f'output_file = "{export["output_file"]}"')
        if export.get("outbound_profile"):
            lines.append(f'outbound_profile = "{export["outbound_profile"]}"')
        if export.get("inbound_profile"):
            lines.append(f'inbound_profile = "{export["inbound_profile"]}"')
        if export.get("inbound_types"):
            lines.append(f"inbound_types = {json.dumps(export['inbound_types'])}")
        lines.append("")

    # Agent section
    if "agent" in config_dict and config_dict["agent"]:
        lines.append("# Agent configuration")
        lines.append("[agent]")
        agent = config_dict["agent"]
        lines.append(f"auto_restart = {str(agent.get('auto_restart', False)).lower()}")
        lines.append(
            f"monitor_latency = {str(agent.get('monitor_latency', True)).lower()}"
        )
        if agent.get("health_check_interval"):
            lines.append(f'health_check_interval = "{agent["health_check_interval"]}"')
        if agent.get("log_level"):
            lines.append(f'log_level = "{agent["log_level"]}"')
        lines.append("")

    # UI section
    if "ui" in config_dict and config_dict["ui"]:
        lines.append("# UI preferences")
        lines.append("[ui]")
        ui = config_dict["ui"]
        lines.append(f'default_language = "{ui.get("default_language", "en")}"')

        # Handle UI mode enum
        mode_val = ui.get("mode", "cli")
        if hasattr(mode_val, "value"):
            mode_val = mode_val.value
        elif str(mode_val).startswith("UIMode."):
            mode_val = mode_val.split(".")[-1].lower()
        lines.append(f'mode = "{mode_val}"')

        lines.append(
            f"show_debug_info = {str(ui.get('show_debug_info', False)).lower()}"
        )
        if ui.get("theme"):
            lines.append(f'theme = "{ui["theme"]}"')
        lines.append("")

    # Metadata section
    if "metadata" in config_dict and config_dict["metadata"]:
        lines.append("# Additional metadata")
        metadata = config_dict["metadata"]

        # Handle subscription URLs
        if "subscription_urls" in metadata:
            lines.append("[metadata.subscription_urls]")
            for sub_id, url in metadata["subscription_urls"].items():
                lines.append(f'"{sub_id}" = "{url}"')
            lines.append("")

        # Handle other metadata (but not subscription_urls which is already handled)
        for key, value in metadata.items():
            if key != "subscription_urls":  # Already handled above
                if isinstance(value, dict):
                    lines.append(f"[metadata.{key}]")
                    for sub_key, sub_value in value.items():
                        if isinstance(sub_value, str):
                            lines.append(f'"{sub_key}" = "{sub_value}"')
                        else:
                            lines.append(f'"{sub_key}" = {json.dumps(sub_value)}')
                    lines.append("")
                elif isinstance(value, str):
                    lines.append("[metadata]")
                    lines.append(f'{key} = "{value}"')
                    lines.append("")
                else:
                    lines.append("[metadata]")
                    lines.append(f"{key} = {json.dumps(value)}")
                    lines.append("")

    # Timestamps
    if "created_at" in config_dict:
        lines.append(f'created_at = "{config_dict["created_at"]}"')
    if "updated_at" in config_dict:
        lines.append(f'updated_at = "{config_dict["updated_at"]}"')

    return "\n".join(lines)


def convert_json_to_toml(
    json_path: Union[str, Path], toml_path: Union[str, Path]
) -> None:
    """Convert JSON config to TOML format.

    Args:
        json_path: Path to JSON config file
        toml_path: Path where to save TOML file

    """
    json_path = Path(json_path).expanduser().resolve()
    toml_path = Path(toml_path).expanduser().resolve()

    if not json_path.exists():
        raise FileNotFoundError(f"JSON config not found: {json_path}")

    if logger:
        logger.info(f"Converting {json_path} to {toml_path}")

    try:
        # Load JSON config
        with open(json_path, encoding="utf-8") as f:
            json_data = json.load(f)

        # Create UserConfig from JSON data
        config = UserConfig(**json_data)

        # Save as TOML
        save_config_to_toml(config, toml_path)

        if logger:
            logger.info(f"Successfully converted {json_path} to {toml_path}")

    except Exception as e:
        if logger:
            logger.error(f"Failed to convert {json_path} to TOML: {e}")
        raise


def detect_config_format(file_path: Union[str, Path]) -> str:
    """Detect configuration file format.

    Args:
        file_path: Path to config file

    Returns:
        str: Format name ('json', 'toml', 'unknown')

    """
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".json":
        return "json"
    elif suffix in [".toml", ".tml"]:
        return "toml"
    else:
        return "unknown"


def load_config_auto(file_path: Union[str, Path]) -> UserConfig:
    """Load configuration with automatic format detection.

    Args:
        file_path: Path to config file

    Returns:
        UserConfig: Loaded configuration

    Raises:
        ValueError: If format is not supported

    """
    format_type = detect_config_format(file_path)

    if format_type == "toml":
        return load_config_from_toml(file_path)
    elif format_type == "json":
        # Load JSON and convert to UserConfig
        with open(file_path, encoding="utf-8") as f:
            json_data = json.load(f)
        return UserConfig(**json_data)
    else:
        raise ValueError(f"Unsupported config format: {Path(file_path).suffix}")
