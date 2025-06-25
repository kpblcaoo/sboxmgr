"""Internal validation module for sboxmgr.

This module provides internal validation capabilities without external dependencies.
Replaces subprocess calls to sing-box with internal Pydantic-based validation.
"""

from .internal import validate_config_dict, validate_config_json
from .schema import SingBoxConfig

__all__ = [
    'validate_config_dict',
    'validate_config_json', 
    'SingBoxConfig',
] 