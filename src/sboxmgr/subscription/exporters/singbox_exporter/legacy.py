"""Legacy functions for sing-box exporter (deprecated)."""

import warnings
from typing import List, Dict, Any, Optional

from sboxmgr.subscription.models import ParsedServer, ClientProfile
from .core import process_single_server, create_urltest_outbound
from .inbound_generator import generate_inbounds


def add_special_outbounds(outbounds: List[Dict[str, Any]]) -> None:
    """Add special outbounds for legacy compatibility.

    Args:
        outbounds: List of outbounds to modify.
    """
    # Add direct outbound
    outbounds.append({
        "type": "direct",
        "tag": "direct"
    })

    # Add block outbound
    outbounds.append({
        "type": "block",
        "tag": "block"
    })

    # Add DNS outbound
    outbounds.append({
        "type": "dns",
        "tag": "dns"
    })


def create_enhanced_routing_rules() -> List[Dict[str, Any]]:
    """Create enhanced routing rules for legacy compatibility.

    Returns:
        List of routing rules.
    """
    return [
        {
            "protocol": "dns",
            "outbound": "dns"
        },
        {
            "ip_cidr": [
                "10.0.0.0/8",
                "172.16.0.0/12",
                "192.168.0.0/16",
                "127.0.0.0/8"
            ],
            "outbound": "direct"
        },
        {
            "rule_set": ["geoip-ru"],
            "outbound": "direct"
        },
        {
            "rule_set": ["geosite-ads"],
            "outbound": "block"
        }
    ]


def singbox_export_legacy(
    servers: List[ParsedServer],
    routes: Optional[List[Dict[str, Any]]] = None,
    client_profile: Optional[ClientProfile] = None
) -> Dict[str, Any]:
    """Export parsed servers to sing-box configuration format (legacy approach).

    DEPRECATED: This function uses legacy special outbounds (direct, block, dns)
    which are deprecated in sing-box 1.11.0. Use singbox_export() instead.

    Args:
        servers: List of ParsedServer objects to export.
        routes: Routing rules configuration.
        client_profile: Optional client profile for inbound generation.

    Returns:
        Dictionary containing complete sing-box configuration with outbounds,
        routing rules, and optional inbounds section.
    """
    warnings.warn(
        "singbox_export_legacy() is deprecated. Use singbox_export() for modern sing-box 1.11.0 compatibility.",
        DeprecationWarning,
        stacklevel=2
    )

    outbounds = []
    proxy_tags = []

    # Process each server
    for server in servers:
        outbound = process_single_server(server)
        if outbound:
            outbounds.append(outbound)
            proxy_tags.append(outbound["tag"])

    # Add URLTest outbound if there are proxy servers
    if proxy_tags:
        urltest_outbound = create_urltest_outbound(proxy_tags)
        outbounds.insert(0, urltest_outbound)

    # Add special outbounds for backward compatibility
    add_special_outbounds(outbounds)

    # Use provided routing rules or create enhanced defaults
    if routes:
        routing_rules = routes
    else:
        routing_rules = create_enhanced_routing_rules()

    # Build final configuration
    config = {
        "outbounds": outbounds,
        "route": {
            "rules": routing_rules,
            "rule_set": [
                {
                    "tag": "geoip-ru",
                    "type": "remote",
                    "format": "binary",
                    "url": "https://raw.githubusercontent.com/SagerNet/sing-geoip/rule-set/geoip-ru.srs",
                    "download_detour": "direct"
                }
            ],
            "final": "auto" if proxy_tags else "direct"
        },
        "experimental": {
            "cache_file": {
                "enabled": True
            }
        }
    }

    # Add inbounds if client profile provided
    if client_profile is not None:
        config["inbounds"] = generate_inbounds(client_profile)

    return config
