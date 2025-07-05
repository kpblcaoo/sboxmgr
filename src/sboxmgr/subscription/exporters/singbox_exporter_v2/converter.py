"""Core conversion logic for sing-box exporter v2.

This module provides the main conversion function that transforms ParsedServer
objects into appropriate sing-box outbound models using the modular Pydantic models.
"""

import logging
from typing import Optional, Union
from ...models import ParsedServer

# Import new sing-box models
from sboxmgr.models.singbox import (
    ShadowsocksOutbound, VmessOutbound, VlessOutbound, TrojanOutbound,
    Hysteria2Outbound, WireGuardOutbound, HttpOutbound, SocksOutbound,
    TuicOutbound, ShadowTlsOutbound, DnsOutbound, DirectOutbound,
    BlockOutbound, SelectorOutbound, UrlTestOutbound, HysteriaOutbound,
    AnyTlsOutbound, SshOutbound, TorOutbound
)

from .protocol_converters import (
    convert_shadowsocks, convert_vmess, convert_vless, convert_trojan,
    convert_hysteria2, convert_wireguard, convert_tuic, convert_shadowtls,
    convert_anytls, convert_tor, convert_ssh, convert_http, convert_socks,
    convert_direct
)

logger = logging.getLogger(__name__)


def convert_parsed_server_to_outbound(server: ParsedServer) -> Optional[Union[
    ShadowsocksOutbound, VmessOutbound, VlessOutbound, TrojanOutbound,
    Hysteria2Outbound, WireGuardOutbound, HttpOutbound, SocksOutbound,
    TuicOutbound, ShadowTlsOutbound, DnsOutbound, DirectOutbound,
    BlockOutbound, SelectorOutbound, UrlTestOutbound, HysteriaOutbound,
    AnyTlsOutbound, SshOutbound, TorOutbound
]]:
    """Convert ParsedServer to appropriate sing-box outbound model.
    
    Args:
        server: ParsedServer object to convert
        
    Returns:
        Appropriate outbound model instance or None if conversion fails
    """
    try:
        # Normalize protocol type
        protocol_type = server.type
        if protocol_type == "ss":
            protocol_type = "shadowsocks"
        
        # Create base outbound data
        outbound_data = {
            "type": protocol_type,
            "server": server.address,
            "server_port": server.port,
        }
        
        # Add tag
        if server.tag:
            outbound_data["tag"] = server.tag
        elif server.meta.get("name"):
            outbound_data["tag"] = server.meta["name"]
        else:
            outbound_data["tag"] = f"{protocol_type}-{server.address}"
        
        # Protocol-specific conversion
        converter_map = {
            "shadowsocks": convert_shadowsocks,
            "vmess": convert_vmess,
            "vless": convert_vless,
            "trojan": convert_trojan,
            "hysteria2": convert_hysteria2,
            "wireguard": convert_wireguard,
            "tuic": convert_tuic,
            "shadowtls": convert_shadowtls,
            "anytls": convert_anytls,
            "tor": convert_tor,
            "ssh": convert_ssh,
            "http": convert_http,
            "socks": convert_socks,
            "direct": convert_direct,
        }
        
        converter = converter_map.get(protocol_type)
        if converter:
            return converter(server, outbound_data)
        else:
            logger.warning(f"Unsupported protocol type: {protocol_type}")
            return None
            
    except Exception as e:
        logger.error(f"Failed to convert server {server.address}:{server.port}: {e}")
        return None 