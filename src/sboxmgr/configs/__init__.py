"""Config management module for sboxmgr (ADR-0017).

This module provides config-based configuration management,
allowing users to define complete configurations in a single TOML/JSON file.
"""

from .models import (  # Enums; Backward compatibility aliases; New names
    AgentConfig,
    AgentProfile,
    Config,
    ExportConfig,
    ExportFormat,
    ExportProfile,
    FilterConfig,
    FilterProfile,
    FullProfile,
    LegacyConfig,
    LegacyProfile,
    RoutingConfig,
    RoutingProfile,
    SubscriptionConfig,
    SubscriptionProfile,
    UIConfig,
    UIMode,
    UIProfile,
    UserConfig,
)

__all__ = [
    # New names
    "UserConfig",
    "Config",
    "SubscriptionConfig",
    "FilterConfig",
    "RoutingConfig",
    "ExportConfig",
    "AgentConfig",
    "UIConfig",
    "LegacyConfig",
    # Backward compatibility
    "FullProfile",
    "SubscriptionProfile",
    "FilterProfile",
    "RoutingProfile",
    "ExportProfile",
    "AgentProfile",
    "UIProfile",
    "LegacyProfile",
    # Enums
    "ExportFormat",
    "UIMode",
]
