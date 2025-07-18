"""Inbound converter for sing-box exporter v2.

This module provides functions to convert ClientProfile objects
into appropriate sing-box inbound configurations.
"""

import logging
from typing import Union

# Import new sing-box models
from sboxmgr.models.singbox import (
    DirectInbound,
    HttpInbound,
    Hysteria2Inbound,
    MixedInbound,
    ShadowsocksInbound,
    ShadowTlsInbound,
    SocksInbound,
    TrojanInbound,
    TuicInbound,
    VlessInbound,
    VmessInbound,
    WireGuardInbound,
)

from ...models import ClientProfile

logger = logging.getLogger(__name__)


def convert_client_profile_to_inbounds(
    profile: ClientProfile,
) -> list[
    Union[
        MixedInbound,
        SocksInbound,
        HttpInbound,
        ShadowsocksInbound,
        VmessInbound,
        VlessInbound,
        TrojanInbound,
        Hysteria2Inbound,
        WireGuardInbound,
        TuicInbound,
        ShadowTlsInbound,
        DirectInbound,
    ]
]:
    """Convert ClientProfile to list of sing-box inbound configurations.

    Args:
        profile: ClientProfile object to convert

    Returns:
        List of appropriate inbound model instances
    """
    inbounds = []

    try:
        # Handle inbounds configuration
        if hasattr(profile, "inbounds") and profile.inbounds:
            for inbound_config in profile.inbounds:
                inbound = _convert_single_inbound(inbound_config)
                if inbound:
                    inbounds.append(inbound)

        # Default mixed inbound if no inbounds specified
        if not inbounds:
            default_inbound = MixedInbound(
                type="mixed", tag="mixed-in", listen="127.0.0.1", listen_port=7890
            )
            inbounds.append(default_inbound)

    except Exception as e:
        logger.error(f"Failed to convert client profile to inbounds: {e}")
        # Return default mixed inbound on error
        return [
            MixedInbound(
                type="mixed", tag="mixed-in", listen="127.0.0.1", listen_port=7890
            )
        ]

    return inbounds


def _convert_single_inbound(
    inbound_config,
) -> Union[
    MixedInbound,
    SocksInbound,
    HttpInbound,
    ShadowsocksInbound,
    VmessInbound,
    VlessInbound,
    TrojanInbound,
    Hysteria2Inbound,
    WireGuardInbound,
    TuicInbound,
    ShadowTlsInbound,
    DirectInbound,
    None,
]:
    """Convert a single inbound configuration to appropriate model.

    Args:
        inbound_config: Dictionary or InboundProfile containing inbound configuration

    Returns:
        Appropriate inbound model instance or None if conversion fails
    """
    try:
        # Convert InboundProfile to dict if needed
        if hasattr(inbound_config, "model_dump"):
            inbound_dict = inbound_config.model_dump()
        elif isinstance(inbound_config, dict):
            inbound_dict = inbound_config
        else:
            logger.error(f"Unsupported inbound_config type: {type(inbound_config)}")
            return None

        inbound_type = inbound_dict.get("type", "mixed")

        # Base configuration
        base_config = {
            "type": inbound_type,
            "tag": inbound_dict.get("tag", f"{inbound_type}-in"),
            "listen": inbound_dict.get("listen", "127.0.0.1"),
        }

        # Handle port field with proper fallback logic
        listen_port = inbound_dict.get("listen_port")
        if listen_port is None:
            port_value = inbound_dict.get("port")
            listen_port = 7890 if port_value is None else port_value
        base_config["listen_port"] = listen_port

        # Add optional fields if present
        if "sniff" in inbound_dict:
            base_config["sniff"] = inbound_dict["sniff"]
        if "sniff_override_destination" in inbound_dict:
            base_config["sniff_override_destination"] = inbound_dict[
                "sniff_override_destination"
            ]
        if "domain_strategy" in inbound_dict:
            base_config["domain_strategy"] = inbound_dict["domain_strategy"]

        # Type-specific conversion
        if inbound_type == "mixed":
            return MixedInbound(**base_config)
        elif inbound_type == "socks":
            # Add SOCKS-specific fields
            if "users" in inbound_dict:
                base_config["users"] = inbound_dict["users"]
            return SocksInbound(**base_config)
        elif inbound_type == "http":
            # Add HTTP-specific fields
            if "users" in inbound_dict:
                base_config["users"] = inbound_dict["users"]
            if "tls" in inbound_dict:
                base_config["tls"] = inbound_dict["tls"]
            return HttpInbound(**base_config)
        elif inbound_type == "shadowsocks":
            # Add Shadowsocks-specific fields
            base_config["method"] = inbound_dict.get("method", "aes-256-gcm")
            base_config["password"] = inbound_dict.get("password", "")
            if "users" in inbound_dict:
                base_config["users"] = inbound_dict["users"]
            return ShadowsocksInbound(**base_config)
        elif inbound_type == "vmess":
            # Add VMess-specific fields
            base_config["users"] = inbound_dict.get("users", [])
            if "tls" in inbound_dict:
                base_config["tls"] = inbound_dict["tls"]
            if "transport" in inbound_dict:
                base_config["transport"] = inbound_dict["transport"]
            return VmessInbound(**base_config)
        elif inbound_type == "vless":
            # Add VLESS-specific fields
            base_config["users"] = inbound_dict.get("users", [])
            if "tls" in inbound_dict:
                base_config["tls"] = inbound_dict["tls"]
            if "transport" in inbound_dict:
                base_config["transport"] = inbound_dict["transport"]
            return VlessInbound(**base_config)
        elif inbound_type == "trojan":
            # Add Trojan-specific fields
            base_config["users"] = inbound_dict.get("users", [])
            if "tls" in inbound_dict:
                base_config["tls"] = inbound_dict["tls"]
            if "transport" in inbound_dict:
                base_config["transport"] = inbound_dict["transport"]
            return TrojanInbound(**base_config)
        elif inbound_type == "hysteria2":
            # Add Hysteria2-specific fields
            base_config["users"] = inbound_dict.get("users", [])
            if "tls" in inbound_dict:
                base_config["tls"] = inbound_dict["tls"]
            if "masquerade" in inbound_dict:
                base_config["masquerade"] = inbound_dict["masquerade"]
            return Hysteria2Inbound(**base_config)
        elif inbound_type == "wireguard":
            # Add WireGuard-specific fields
            base_config["private_key"] = inbound_dict.get("private_key", "")
            base_config["peers"] = inbound_dict.get("peers", [])
            return WireGuardInbound(**base_config)
        elif inbound_type == "tuic":
            # Add TUIC-specific fields
            base_config["users"] = inbound_dict.get("users", [])
            if "tls" in inbound_dict:
                base_config["tls"] = inbound_dict["tls"]
            return TuicInbound(**base_config)
        elif inbound_type == "shadowtls":
            # Add ShadowTLS-specific fields
            base_config["users"] = inbound_dict.get("users", [])
            base_config["handshake"] = inbound_dict.get("handshake", {})
            return ShadowTlsInbound(**base_config)
        elif inbound_type == "direct":
            return DirectInbound(**base_config)
        else:
            logger.warning(f"Unsupported inbound type: {inbound_type}")
            return None

    except Exception as e:
        logger.error(f"Failed to convert inbound configuration: {e}")
        return None
