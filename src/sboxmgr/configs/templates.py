"""Profile templates for sboxmgr (ADR-0020).

This module defines templates for creating new FullProfile configurations.
Templates provide pre-configured settings for common use cases.
"""

from typing import Any

# Profile templates for common use cases
PROFILE_TEMPLATES: dict[str, dict[str, Any]] = {
    "basic": {
        "description": "Basic profile template",
        "template": {
            "subscriptions": [],
            "filters": {
                "exclude_tags": [],
                "only_tags": [],
                "exclusions": [],
                "only_enabled": True,
            },
            "routing": {
                "by_source": {},
                "default_route": "tunnel",
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
                "theme": None,
                "show_debug_info": False,
            },
        },
    },
    "vpn": {
        "description": "VPN profile template with optimized settings",
        "template": {
            "subscriptions": [],
            "filters": {
                "exclude_tags": ["slow", "blocked"],
                "only_tags": [],
                "exclusions": [],
                "only_enabled": True,
            },
            "routing": {
                "by_source": {},
                "default_route": "tunnel",
                "custom_routes": {
                    "*.google.com": "tunnel",
                    "*.youtube.com": "tunnel",
                    "*.netflix.com": "tunnel",
                },
            },
            "export": {
                "format": "sing-box",
                "outbound_profile": "vless-real",
                "inbound_profile": "tun",
                "output_file": "vpn-config.json",
            },
            "agent": {
                "auto_restart": True,
                "monitor_latency": True,
                "health_check_interval": "60s",
                "log_level": "info",
            },
            "ui": {
                "default_language": "en",
                "mode": "cli",
                "theme": None,
                "show_debug_info": False,
            },
        },
    },
    "server": {
        "description": "Server profile template for transparent proxy",
        "template": {
            "subscriptions": [],
            "filters": {
                "exclude_tags": [],
                "only_tags": [],
                "exclusions": [],
                "only_enabled": True,
            },
            "routing": {
                "by_source": {},
                "default_route": "proxy",
                "custom_routes": {
                    "*.local": "direct",
                    "127.0.0.1": "direct",
                    "192.168.0.0/16": "direct",
                },
            },
            "export": {
                "format": "sing-box",
                "outbound_profile": "vless-real",
                "inbound_profile": "tproxy",
                "output_file": "server-config.json",
            },
            "agent": {
                "auto_restart": True,
                "monitor_latency": True,
                "health_check_interval": "30s",
                "log_level": "warn",
            },
            "ui": {
                "default_language": "en",
                "mode": "cli",
                "theme": None,
                "show_debug_info": False,
            },
        },
    },
    "development": {
        "description": "Development profile template with debug settings",
        "template": {
            "subscriptions": [],
            "filters": {
                "exclude_tags": [],
                "only_tags": [],
                "exclusions": [],
                "only_enabled": True,
            },
            "routing": {
                "by_source": {},
                "default_route": "tunnel",
                "custom_routes": {},
            },
            "export": {
                "format": "sing-box",
                "outbound_profile": "vless-real",
                "inbound_profile": "tun",
                "output_file": "dev-config.json",
            },
            "agent": {
                "auto_restart": False,
                "monitor_latency": False,
                "health_check_interval": "300s",
                "log_level": "debug",
            },
            "ui": {
                "default_language": "en",
                "mode": "cli",
                "theme": None,
                "show_debug_info": True,
            },
        },
    },
    "minimal": {
        "description": "Minimal profile template with essential settings only",
        "template": {
            "subscriptions": [],
            "filters": {
                "exclude_tags": [],
                "only_tags": [],
                "exclusions": [],
                "only_enabled": True,
            },
            "routing": {
                "by_source": {},
                "default_route": "tunnel",
                "custom_routes": {},
            },
            "export": {
                "format": "sing-box",
                "outbound_profile": "vless-real",
                "inbound_profile": "tun",
                "output_file": "config.json",
            },
            # No agent or ui settings for minimal template
        },
    },
}


def get_template_names() -> list[str]:
    """Get list of available template names.

    Returns:
        list[str]: List of template names.

    """
    return list(PROFILE_TEMPLATES.keys())


def get_template(template_name: str) -> dict[str, Any]:
    """Get template by name.

    Args:
        template_name: Name of the template.

    Returns:
        dict[str, Any]: Template data.

    Raises:
        ValueError: If template name is invalid.

    """
    if template_name not in PROFILE_TEMPLATES:
        available = ", ".join(get_template_names())
        raise ValueError(f"Invalid template '{template_name}'. Available: {available}")

    return PROFILE_TEMPLATES[template_name]["template"].copy()


def get_template_description(template_name: str) -> str:
    """Get template description.

    Args:
        template_name: Name of the template.

    Returns:
        str: Template description.

    Raises:
        ValueError: If template name is invalid.

    """
    if template_name not in PROFILE_TEMPLATES:
        available = ", ".join(get_template_names())
        raise ValueError(f"Invalid template '{template_name}'. Available: {available}")

    return PROFILE_TEMPLATES[template_name]["description"]
