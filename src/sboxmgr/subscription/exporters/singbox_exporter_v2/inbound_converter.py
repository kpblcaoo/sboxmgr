"""Inbound converter for sing-box exporter v2.

This module provides functions to convert ClientProfile objects
into appropriate sing-box inbound configurations.
"""

import logging
from typing import List, Union
from ...models import ClientProfile

# Import new sing-box models
from sboxmgr.models.singbox import (
    MixedInbound, SocksInbound, HttpInbound, ShadowsocksInbound,
    VmessInbound, VlessInbound, TrojanInbound, Hysteria2Inbound,
    WireGuardInbound, TuicInbound, ShadowTlsInbound, DirectInbound
)

logger = logging.getLogger(__name__)


def convert_client_profile_to_inbounds(profile: ClientProfile) -> List[Union[
    MixedInbound, SocksInbound, HttpInbound, ShadowsocksInbound,
    VmessInbound, VlessInbound, TrojanInbound, Hysteria2Inbound,
    WireGuardInbound, TuicInbound, ShadowTlsInbound, DirectInbound
]]:
    """Convert ClientProfile to list of sing-box inbound configurations.
    
    Args:
        profile: ClientProfile object to convert
        
    Returns:
        List of appropriate inbound model instances
    """
    inbounds = []
    
    try:
        # Handle inbounds configuration
        if hasattr(profile, 'inbounds') and profile.inbounds:
            for inbound_config in profile.inbounds:
                inbound = _convert_single_inbound(inbound_config)
                if inbound:
                    inbounds.append(inbound)
        
        # Default mixed inbound if no inbounds specified
        if not inbounds:
            default_inbound = MixedInbound(
                type="mixed",
                tag="mixed-in",
                listen="127.0.0.1",
                listen_port=7890
            )
            inbounds.append(default_inbound)
            
    except Exception as e:
        logger.error(f"Failed to convert client profile to inbounds: {e}")
        # Return default mixed inbound on error
        return [MixedInbound(
            type="mixed",
            tag="mixed-in",
            listen="127.0.0.1", 
            listen_port=7890
        )]
    
    return inbounds


def _convert_single_inbound(inbound_config: dict) -> Union[
    MixedInbound, SocksInbound, HttpInbound, ShadowsocksInbound,
    VmessInbound, VlessInbound, TrojanInbound, Hysteria2Inbound,
    WireGuardInbound, TuicInbound, ShadowTlsInbound, DirectInbound,
    None
]:
    """Convert a single inbound configuration to appropriate model.
    
    Args:
        inbound_config: Dictionary containing inbound configuration
        
    Returns:
        Appropriate inbound model instance or None if conversion fails
    """
    try:
        inbound_type = inbound_config.get("type", "mixed")
        
        # Base configuration
        base_config = {
            "type": inbound_type,
            "tag": inbound_config.get("tag", f"{inbound_type}-in"),
            "listen": inbound_config.get("listen", "127.0.0.1"),
            "listen_port": inbound_config.get("listen_port", 7890)
        }
        
        # Add optional fields if present
        if "sniff" in inbound_config:
            base_config["sniff"] = inbound_config["sniff"]
        if "sniff_override_destination" in inbound_config:
            base_config["sniff_override_destination"] = inbound_config["sniff_override_destination"]
        if "domain_strategy" in inbound_config:
            base_config["domain_strategy"] = inbound_config["domain_strategy"]
        
        # Type-specific conversion
        if inbound_type == "mixed":
            return MixedInbound(**base_config)
        elif inbound_type == "socks":
            # Add SOCKS-specific fields
            if "users" in inbound_config:
                base_config["users"] = inbound_config["users"]
            return SocksInbound(**base_config)
        elif inbound_type == "http":
            # Add HTTP-specific fields
            if "users" in inbound_config:
                base_config["users"] = inbound_config["users"]
            if "tls" in inbound_config:
                base_config["tls"] = inbound_config["tls"]
            return HttpInbound(**base_config)
        elif inbound_type == "shadowsocks":
            # Add Shadowsocks-specific fields
            base_config["method"] = inbound_config.get("method", "aes-256-gcm")
            base_config["password"] = inbound_config.get("password", "")
            if "users" in inbound_config:
                base_config["users"] = inbound_config["users"]
            return ShadowsocksInbound(**base_config)
        elif inbound_type == "vmess":
            # Add VMess-specific fields
            base_config["users"] = inbound_config.get("users", [])
            if "tls" in inbound_config:
                base_config["tls"] = inbound_config["tls"]
            if "transport" in inbound_config:
                base_config["transport"] = inbound_config["transport"]
            return VmessInbound(**base_config)
        elif inbound_type == "vless":
            # Add VLESS-specific fields
            base_config["users"] = inbound_config.get("users", [])
            if "tls" in inbound_config:
                base_config["tls"] = inbound_config["tls"]
            if "transport" in inbound_config:
                base_config["transport"] = inbound_config["transport"]
            return VlessInbound(**base_config)
        elif inbound_type == "trojan":
            # Add Trojan-specific fields
            base_config["users"] = inbound_config.get("users", [])
            if "tls" in inbound_config:
                base_config["tls"] = inbound_config["tls"]
            if "transport" in inbound_config:
                base_config["transport"] = inbound_config["transport"]
            return TrojanInbound(**base_config)
        elif inbound_type == "hysteria2":
            # Add Hysteria2-specific fields
            base_config["users"] = inbound_config.get("users", [])
            if "tls" in inbound_config:
                base_config["tls"] = inbound_config["tls"]
            if "masquerade" in inbound_config:
                base_config["masquerade"] = inbound_config["masquerade"]
            return Hysteria2Inbound(**base_config)
        elif inbound_type == "wireguard":
            # Add WireGuard-specific fields
            base_config["private_key"] = inbound_config.get("private_key", "")
            base_config["peers"] = inbound_config.get("peers", [])
            return WireGuardInbound(**base_config)
        elif inbound_type == "tuic":
            # Add TUIC-specific fields
            base_config["users"] = inbound_config.get("users", [])
            if "tls" in inbound_config:
                base_config["tls"] = inbound_config["tls"]
            return TuicInbound(**base_config)
        elif inbound_type == "shadowtls":
            # Add ShadowTLS-specific fields
            base_config["users"] = inbound_config.get("users", [])
            base_config["handshake"] = inbound_config.get("handshake", {})
            return ShadowTlsInbound(**base_config)
        elif inbound_type == "direct":
            return DirectInbound(**base_config)
        else:
            logger.warning(f"Unsupported inbound type: {inbound_type}")
            return None
            
    except Exception as e:
        logger.error(f"Failed to convert inbound configuration: {e}")
        return None 