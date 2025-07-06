"""CLI command for configuration export (`sboxctl export`).

This module implements the unified export command that replaces the previous
run and dry-run commands. It generates configurations from subscriptions and
exports them to various formats while following ADR-0014 principles:
- sboxmgr only generates configurations
- sboxagent handles service management
- No direct service restart from sboxmgr

This file now serves as a compatibility layer that imports the refactored
export functionality from the export module.
"""

# Import the refactored export command
from .export import export, app

__all__ = [
    'export',
    'app'
]
