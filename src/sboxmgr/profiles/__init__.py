"""Profile management module for sboxmgr (ADR-0017).

This module provides profile-based configuration management,
allowing users to define complete configurations in a single JSON file.
"""

from .models import (
    FullProfile,
    Profile,
    SubscriptionProfile,
    FilterProfile,
    RoutingProfile,
    ExportProfile,
    AgentProfile,
    UIProfile,
    LegacyProfile,
    ExportFormat,
    UIMode,
    # Type aliases
    SubscriptionConfig,
    FilterConfig,
    RoutingConfig,
    ExportConfig,
    AgentConfig,
    UIConfig,
)

__all__ = [
    "FullProfile",
    "Profile",
    "SubscriptionProfile",
    "FilterProfile",
    "RoutingProfile",
    "ExportProfile",
    "AgentProfile",
    "UIProfile",
    "LegacyProfile",
    "ExportFormat",
    "UIMode",
    "SubscriptionConfig",
    "FilterConfig",
    "RoutingConfig",
    "ExportConfig",
    "AgentConfig",
    "UIConfig",
]
