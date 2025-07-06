"""Protocol handlers for sing-box exporter."""

import logging
from typing import Dict, Optional, Any

from sboxmgr.subscription.models import ParsedServer

logger = logging.getLogger(__name__)


def export_wireguard(server: ParsedServer) -> Optional[Dict[str, Any]]:
    """Export WireGuard server configuration.
    
    Args:
        server: ParsedServer object of type wireguard.
        
    Returns:
        Outbound configuration dict or None if incomplete.
    """
    required_fields = [
        server.address, server.port, server.private_key,
        server.peer_public_key, server.local_address
    ]
    
    if not all(required_fields):
        logger.warning(f"Incomplete wireguard fields, skipping: {server.address}:{server.port}")
        return None
    
    outbound = {
        "type": "wireguard",
        "server": server.address,
        "server_port": server.port,
        "private_key": server.private_key,
        "peer_public_key": server.peer_public_key,
        "local_address": server.local_address,
    }
    
    # Optional fields
    if hasattr(server, "pre_shared_key") and server.pre_shared_key:
        outbound["pre_shared_key"] = server.pre_shared_key
    
    # Meta fields
    meta = getattr(server, 'meta', {}) or {}
    if meta.get("mtu") is not None:
        outbound["mtu"] = meta["mtu"]
    if meta.get("keepalive") is not None:
        outbound["keepalive"] = meta["keepalive"]
    
    # Set tag
    outbound["tag"] = _get_server_tag(server, "wireguard")
    
    return outbound


def export_hysteria2(server: ParsedServer) -> Optional[Dict[str, Any]]:
    """Export Hysteria2 server configuration.
    
    Args:
        server: ParsedServer object of type hysteria2.
        
    Returns:
        Outbound configuration dict or None if incomplete.
    """
    required_fields = [server.address, server.port, server.password]
    
    if not all(required_fields):
        logger.warning(f"Incomplete hysteria2 fields, skipping: {server.address}:{server.port}")
        return None
    
    outbound = {
        "type": "hysteria2",
        "server": server.address,
        "server_port": server.port,
        "password": server.password,
    }
    
    # Set tag
    outbound["tag"] = _get_server_tag(server, "hysteria2")
    
    return outbound


def export_tuic(server: ParsedServer) -> Optional[Dict[str, Any]]:
    """Export TUIC server configuration.
    
    Args:
        server: ParsedServer object of type tuic.
        
    Returns:
        Outbound configuration dict or None if incomplete.
    """
    required_fields = [server.address, server.port, server.uuid, server.password]
    
    if not all(required_fields):
        logger.warning(f"Incomplete tuic fields, skipping: {server.address}:{server.port}")
        return None
    
    outbound = {
        "type": "tuic",
        "server": server.address,
        "server_port": server.port,
        "uuid": server.uuid,
        "password": server.password,
    }
    
    # Optional fields
    if hasattr(server, "congestion_control") and server.congestion_control:
        outbound["congestion_control"] = server.congestion_control
    if hasattr(server, "alpn") and server.alpn:
        outbound["alpn"] = server.alpn
    if hasattr(server, "tls") and server.tls:
        outbound["tls"] = server.tls
    
    # Meta fields
    meta = getattr(server, 'meta', {}) or {}
    if meta.get("udp_relay_mode") is not None:
        outbound["udp_relay_mode"] = meta["udp_relay_mode"]
    
    # Set tag
    outbound["tag"] = _get_server_tag(server, "tuic")
    
    return outbound


def export_shadowtls(server: ParsedServer) -> Optional[Dict[str, Any]]:
    """Export ShadowTLS server configuration.
    
    Args:
        server: ParsedServer object of type shadowtls.
        
    Returns:
        Outbound configuration dict or None if incomplete.
    """
    required_fields = [server.address, server.port, server.password, server.version]
    
    if not all(required_fields):
        logger.warning(f"Incomplete shadowtls fields, skipping: {server.address}:{server.port}")
        return None
    
    outbound = {
        "type": "shadowtls",
        "server": server.address,
        "server_port": server.port,
        "password": server.password,
        "version": server.version,
    }
    
    # Optional fields
    if hasattr(server, "handshake") and server.handshake:
        outbound["handshake"] = server.handshake
    if hasattr(server, "tls") and server.tls:
        outbound["tls"] = server.tls
    
    # Set tag
    outbound["tag"] = _get_server_tag(server, "shadowtls")
    
    return outbound


def export_anytls(server: ParsedServer) -> Optional[Dict[str, Any]]:
    """Export AnyTLS server configuration.
    
    Args:
        server: ParsedServer object of type anytls.
        
    Returns:
        Outbound configuration dict or None if incomplete.
    """
    required_fields = [server.address, server.port, server.uuid]
    
    if not all(required_fields):
        logger.warning(f"Incomplete anytls fields, skipping: {server.address}:{server.port}")
        return None
    
    outbound = {
        "type": "anytls",
        "server": server.address,
        "server_port": server.port,
        "uuid": server.uuid,
    }
    
    # Optional fields
    if hasattr(server, "tls") and server.tls:
        outbound["tls"] = server.tls
    
    # Set tag
    outbound["tag"] = _get_server_tag(server, "anytls")
    
    return outbound


def export_tor(server: ParsedServer) -> Optional[Dict[str, Any]]:
    """Export Tor server configuration.
    
    Args:
        server: ParsedServer object of type tor.
        
    Returns:
        Outbound configuration dict or None if incomplete.
    """
    required_fields = [server.address, server.port]
    
    if not all(required_fields):
        logger.warning(f"Incomplete tor fields, skipping: {server.address}:{server.port}")
        return None
    
    outbound = {
        "type": "tor",
        "server": server.address,
        "server_port": server.port,
    }
    
    # Set tag
    outbound["tag"] = _get_server_tag(server, "tor")
    
    return outbound


def export_ssh(server: ParsedServer) -> Optional[Dict[str, Any]]:
    """Export SSH server configuration.
    
    Args:
        server: ParsedServer object of type ssh.
        
    Returns:
        Outbound configuration dict or None if incomplete.
    """
    required_fields = [server.address, server.port, server.username]
    
    if not all(required_fields):
        logger.warning(f"Incomplete ssh fields, skipping: {server.address}:{server.port}")
        return None
    
    outbound = {
        "type": "ssh",
        "server": server.address,
        "server_port": server.port,
        "username": server.username,
    }
    
    # Optional fields
    if hasattr(server, "password") and server.password:
        outbound["password"] = server.password
    if hasattr(server, "private_key") and server.private_key:
        outbound["private_key"] = server.private_key
    if hasattr(server, "tls") and server.tls:
        outbound["tls"] = server.tls
    
    # Set tag
    outbound["tag"] = _get_server_tag(server, "ssh")
    
    return outbound


def _get_server_tag(server: ParsedServer, protocol_type: str) -> str:
    """Get server tag from meta, server.tag or generate default.
    
    Args:
        server: ParsedServer object.
        protocol_type: Protocol type for default tag.
        
    Returns:
        Server tag string.
    """
    meta = getattr(server, 'meta', {}) or {}
    
    if meta.get("name"):
        return meta["name"]
    elif hasattr(server, "tag") and server.tag:
        return server.tag
    else:
        return f"{protocol_type}-{server.address}"


def get_protocol_dispatcher() -> Dict[str, callable]:
    """Get protocol dispatcher mapping.
    
    Returns:
        Dictionary mapping protocol types to export functions.
    """
    return {
        "wireguard": export_wireguard,
        "hysteria2": export_hysteria2,
        "tuic": export_tuic,
        "shadowtls": export_shadowtls,
        "anytls": export_anytls,
        "tor": export_tor,
        "ssh": export_ssh,
    }
