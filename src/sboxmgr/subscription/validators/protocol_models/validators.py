"""Validation utilities for protocol models.

This module provides utility functions for validating protocol configurations,
generating schemas, and converting between different model types.
"""

from typing import Any, Optional

from .outbound_models import (
    BlockOutbound,
    DirectOutbound,
    DnsOutbound,
    HttpOutbound,
    HysteriaOutbound,
    OutboundConfig,
    OutboundModel,
    ShadowsocksOutbound,
    SocksOutbound,
    TrojanOutbound,
    TuicOutbound,
    VlessOutbound,
    VmessOutbound,
    WireguardOutbound,
)
from .protocol_configs import (
    ProtocolConfig,
    ShadowsocksConfig,
    TrojanConfig,
    VlessConfig,
    VmessConfig,
    WireGuardConfig,
)


def validate_protocol_config(config: dict[str, Any], protocol: str) -> ProtocolConfig:
    """Validate protocol-specific configuration.

    Args:
        config: Configuration dictionary
        protocol: Protocol type (shadowsocks, vmess, vless, trojan, wireguard)

    Returns:
        Validated protocol configuration

    Raises:
        ValueError: If configuration is invalid
    """
    protocol_map = {
        "shadowsocks": ShadowsocksConfig,
        "ss": ShadowsocksConfig,
        "vmess": VmessConfig,
        "vless": VlessConfig,
        "trojan": TrojanConfig,
        "wireguard": WireGuardConfig,
        "wg": WireGuardConfig,
    }

    if protocol not in protocol_map:
        raise ValueError(f"Unsupported protocol: {protocol}")

    config_class = protocol_map[protocol]
    return config_class(**config)


def generate_protocol_schema(protocol: str) -> dict[str, Any]:
    """Generate JSON schema for protocol configuration.

    Args:
        protocol: Protocol type

    Returns:
        JSON schema dictionary
    """
    protocol_map = {
        "shadowsocks": ShadowsocksConfig,
        "ss": ShadowsocksConfig,
        "vmess": VmessConfig,
        "vless": VlessConfig,
        "trojan": TrojanConfig,
        "wireguard": WireGuardConfig,
        "wg": WireGuardConfig,
    }

    if protocol not in protocol_map:
        raise ValueError(f"Unsupported protocol: {protocol}")

    return protocol_map[protocol].model_json_schema()


def validate_outbound_config(config: dict[str, Any]) -> OutboundModel:
    """Validate outbound configuration.

    Args:
        config: Configuration dictionary

    Returns:
        Validated outbound configuration

    Raises:
        ValueError: If configuration is invalid
    """
    outbound_type = config.get("type", "")

    outbound_map = {
        "shadowsocks": ShadowsocksOutbound,
        "vmess": VmessOutbound,
        "vless": VlessOutbound,
        "trojan": TrojanOutbound,
        "wireguard": WireguardOutbound,
        "hysteria": HysteriaOutbound,
        "tuic": TuicOutbound,
        "http": HttpOutbound,
        "socks": SocksOutbound,
        "direct": DirectOutbound,
        "block": BlockOutbound,
        "dns": DnsOutbound,
    }

    if outbound_type not in outbound_map:
        raise ValueError(f"Unsupported outbound type: {outbound_type}")

    outbound_class = outbound_map[outbound_type]
    return outbound_class(**config)


def generate_outbound_schema() -> dict[str, Any]:
    """Generate JSON schema for outbound configuration.

    Returns:
        JSON schema dictionary for OutboundModel
    """
    return OutboundConfig.model_json_schema()


def convert_protocol_to_outbound(
    protocol_config: ProtocolConfig, tag: Optional[str] = None
) -> OutboundModel:
    """Convert protocol configuration to outbound configuration.

    Args:
        protocol_config: Protocol configuration instance
        tag: Optional tag for the outbound

    Returns:
        Outbound configuration instance

    Raises:
        ValueError: If protocol type is not supported
    """
    if isinstance(protocol_config, ShadowsocksConfig):
        return ShadowsocksOutbound(
            type="shadowsocks",
            tag=tag,
            server=protocol_config.server,
            server_port=protocol_config.server_port,
            method=protocol_config.method,
            password=protocol_config.password,
            plugin=protocol_config.plugin,
            plugin_opts=protocol_config.plugin_opts,
            local_address=(
                [protocol_config.local_address]
                if protocol_config.local_address
                else None
            ),
        )

    elif isinstance(protocol_config, VmessConfig):
        # Extract first user from settings for outbound
        user = (
            protocol_config.settings.clients[0]
            if protocol_config.settings.clients
            else None
        )
        if not user:
            raise ValueError("VMess config requires at least one user")

        return VmessOutbound(
            type="vmess",
            tag=tag,
            server=protocol_config.server,
            server_port=protocol_config.server_port,
            uuid=user.id,
            security=user.security,
            multiplex=protocol_config.multiplex,
        )

    elif isinstance(protocol_config, VlessConfig):
        # Extract first user from settings for outbound
        user = (
            protocol_config.settings.clients[0]
            if protocol_config.settings.clients
            else None
        )
        if not user:
            raise ValueError("VLESS config requires at least one user")

        return VlessOutbound(
            type="vless",
            tag=tag,
            server=protocol_config.server,
            server_port=protocol_config.server_port,
            uuid=user.id,
            flow=user.flow,
            multiplex=protocol_config.multiplex,
        )

    elif isinstance(protocol_config, TrojanConfig):
        return TrojanOutbound(
            type="trojan",
            tag=tag,
            server=protocol_config.server,
            server_port=protocol_config.server_port,
            password=protocol_config.password,
            tls=protocol_config.tls,
            multiplex=protocol_config.multiplex,
            fallback=protocol_config.fallback,
        )

    elif isinstance(protocol_config, WireGuardConfig):
        # Extract first peer for outbound
        peer = protocol_config.peers[0] if protocol_config.peers else None
        if not peer:
            raise ValueError("WireGuard config requires at least one peer")

        return WireguardOutbound(
            type="wireguard",
            tag=tag,
            private_key=protocol_config.interface.private_key,
            peer_public_key=peer.public_key,
            mtu=protocol_config.interface.mtu,
            local_address=protocol_config.interface.address,
        )

    else:
        raise ValueError(f"Unsupported protocol type: {type(protocol_config)}")


def create_outbound_from_dict(
    config: dict[str, Any], tag: Optional[str] = None
) -> OutboundModel:
    """Create outbound configuration from dictionary.

    Args:
        config: Configuration dictionary
        tag: Optional tag for the outbound

    Returns:
        Outbound configuration instance
    """
    # Add tag if provided
    if tag:
        config = config.copy()
        config["tag"] = tag

    return validate_outbound_config(config)
