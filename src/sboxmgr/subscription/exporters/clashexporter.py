"""Clash configuration exporter implementation.

This module provides the ClashExporter class for converting parsed server
configurations into Clash-compatible YAML format. It handles Clash-specific
configuration structure, proxy groups, and routing rules for seamless
integration with Clash clients.
"""

from typing import Any, Dict, List

from ..base_exporter import BaseExporter
from ..models import ParsedServer


def clash_export(
    servers: List[ParsedServer], routes: List[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Export servers to Clash configuration format.

    Args:
        servers: List of parsed server configurations.
        routes: Optional routing rules (not used in Clash format).

    Returns:
        Dictionary containing Clash configuration.

    """
    # Basic Clash configuration structure
    config = {
        "port": 7890,
        "socks-port": 7891,
        "allow-lan": True,
        "mode": "rule",
        "log-level": "info",
        "external-controller": "127.0.0.1:9090",
        "proxies": [],
        "proxy-groups": [],
        "rules": [],
    }

    # Convert servers to Clash proxy format
    for server in servers:
        proxy = _convert_server_to_clash_proxy(server)
        if proxy:
            config["proxies"].append(proxy)

    # Add default proxy group
    if config["proxies"]:
        config["proxy-groups"].append(
            {
                "name": "Proxy",
                "type": "select",
                "proxies": [proxy["name"] for proxy in config["proxies"]],
            }
        )

    # Add basic rules
    config["rules"] = [
        "DOMAIN-SUFFIX,google.com,Proxy",
        "DOMAIN-SUFFIX,facebook.com,Proxy",
        "DOMAIN-SUFFIX,youtube.com,Proxy",
        "GEOIP,CN,DIRECT",
        "MATCH,DIRECT",
    ]

    return config


def _convert_server_to_clash_proxy(server: ParsedServer) -> Dict[str, Any]:
    """Convert ParsedServer to Clash proxy format.

    Args:
        server: ParsedServer object.

    Returns:
        Dictionary with Clash proxy configuration.

    """
    if not server or not hasattr(server, "type"):
        return None

    # Use server.tag (normalized by middleware) for name
    proxy_name = server.tag if server.tag else f"{server.type}-{server.address}"

    proxy = {
        "name": proxy_name,
        "type": server.type,
        "server": server.address,
        "port": server.port,
    }

    # Add protocol-specific configuration
    if server.type == "vmess":
        proxy.update(
            {
                "uuid": getattr(server, "uuid", ""),
                "alterId": getattr(server, "alter_id", 0),
                "cipher": getattr(server, "security", "auto"),
            }
        )
    elif server.type == "vless":
        # VLESS configuration for ClashMeta
        proxy.update(
            {
                "uuid": getattr(server, "uuid", ""),
                "network": "tcp",  # Default to tcp
                "udp": True,
            }
        )

        # Handle TLS/Reality
        security = server.meta.get("security") if server.meta else None
        if security == "reality":
            proxy.update(
                {
                    "tls": True,
                    "servername": server.meta.get("sni", ""),
                    "reality-opts": {
                        "public-key": server.meta.get("pbk", ""),
                        "short-id": server.meta.get("sid", ""),
                    },
                    "client-fingerprint": server.meta.get("fp", "chrome"),
                }
            )
            # Add flow if present
            if server.meta.get("flow"):
                proxy["flow"] = server.meta["flow"]
        elif security == "tls":
            proxy.update(
                {
                    "tls": True,
                    "servername": server.meta.get("sni", ""),
                }
            )

        # Add ALPN if present
        if server.meta and "alpn" in server.meta:
            proxy["alpn"] = server.meta["alpn"]
    elif server.type == "trojan":
        proxy.update({"password": getattr(server, "password", "")})
    elif server.type in ["ss", "shadowsocks"]:
        # Get method from meta or server attributes
        method = server.meta.get("method") if server.meta else None
        if not method:
            method = getattr(server, "method", "chacha20-ietf-poly1305")

        # Get password from meta or server attributes
        password = server.meta.get("password") if server.meta else None
        if not password:
            password = getattr(server, "password", "")

        proxy.update(
            {
                "cipher": method,
                "password": password,
            }
        )

    return proxy


class ClashExporter(BaseExporter):
    """ClashExporter exports parsed servers to config.

    Example:
    exporter = ClashExporter()
    config = exporter.export(servers)

    """

    def export(self, servers):
        """Export parsed servers to config.

        Args:
            servers (list[ParsedServer]): List of servers.

        Returns:
            dict: Exported config.

        """
        return clash_export(servers)
