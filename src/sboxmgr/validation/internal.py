"""Internal validation functions for sing-box configurations.

This module provides validation capabilities without external dependencies,
replacing subprocess calls to sing-box with internal Pydantic validation.
"""

import json
from typing import Dict, Any, Tuple
from pathlib import Path

from pydantic import ValidationError
from .schema import SingBoxConfig


def validate_config_dict(config_dict: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate sing-box configuration dictionary.
    
    Args:
        config_dict: Configuration dictionary to validate
        
    Returns:
        Tuple of (is_valid, message)
        
    Example:
        >>> config = {"outbounds": [{"type": "direct", "tag": "direct"}]}
        >>> is_valid, message = validate_config_dict(config)
        >>> is_valid
        True
    """
    try:
        SingBoxConfig(**config_dict)
        return True, "Configuration validation passed"
    except ValidationError as e:
        error_details = []
        for error in e.errors():
            loc = " -> ".join(str(x) for x in error['loc'])
            error_details.append(f"{loc}: {error['msg']}")
        
        message = f"Configuration validation failed:\n" + "\n".join(error_details)
        return False, message
    except Exception as e:
        return False, f"Unexpected validation error: {str(e)}"


def validate_config_json(config_json: str) -> Tuple[bool, str]:
    """Validate sing-box configuration JSON string.
    
    Args:
        config_json: JSON string to validate
        
    Returns:
        Tuple of (is_valid, message)
        
    Example:
        >>> config_json = '{"outbounds": [{"type": "direct", "tag": "direct"}]}'
        >>> is_valid, message = validate_config_json(config_json)
        >>> is_valid
        True
    """
    try:
        config_dict = json.loads(config_json)
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON: {str(e)}"
    
    return validate_config_dict(config_dict)


def validate_config_file(config_path: str) -> Tuple[bool, str]:
    """Validate sing-box configuration file.
    
    Replacement for the original validate_config_file function that used subprocess.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Tuple of (is_valid, message)
        
    Example:
        >>> is_valid, message = validate_config_file("/path/to/config.json")
        >>> is_valid
        True
    """
    try:
        config_file = Path(config_path)
        if not config_file.exists():
            return False, f"Configuration file not found: {config_path}"
        
        if not config_file.is_file():
            return False, f"Path is not a file: {config_path}"
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config_json = f.read()
        
        return validate_config_json(config_json)
        
    except PermissionError:
        return False, f"Permission denied reading file: {config_path}"
    except Exception as e:
        return False, f"Error reading configuration file: {str(e)}"


def validate_temp_config(config_json: str) -> None:
    """Validate temporary configuration, raising exception on failure.
    
    Replacement for the subprocess validation in generate_config function.
    
    Args:
        config_json: JSON configuration string
        
    Raises:
        ValueError: If configuration is invalid
        
    Example:
        >>> config = '{"outbounds": [{"type": "direct", "tag": "direct"}]}'
        >>> validate_temp_config(config)  # No exception = valid
    """
    is_valid, message = validate_config_json(config_json)
    if not is_valid:
        raise ValueError(f"Configuration validation failed: {message}") 