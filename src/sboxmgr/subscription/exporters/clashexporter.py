"""Clash configuration exporter implementation.

This module provides the ClashExporter class for converting parsed server
configurations into Clash-compatible YAML format. It handles Clash-specific
configuration structure, proxy groups, and routing rules for seamless
integration with Clash clients.
"""

from typing import Any

from ..base_exporter import BaseExporter
from ..models import ParsedServer


def clash_export(
    servers: list[ParsedServer], routes: list[dict[str, Any]] = None
) -> dict[str, Any]:
    """Export servers to Clash configuration format.

    Args:
        servers: List of parsed server configurations.
        routes: Optional routing rules (not used in Clash format).

    Returns:
        Dictionary containing Clash configuration.

    """
    # Basic Clash configuration structure
    config: dict[str, Any] = {
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
            proxies = config["proxies"]
            if isinstance(proxies, list):
                proxies.append(proxy)

    # Add default proxy group
    proxies = config["proxies"]
    if proxies and isinstance(proxies, list):
        proxy_groups = config["proxy-groups"]
        if isinstance(proxy_groups, list):
            proxy_groups.append(
                {
                    "name": "Proxy",
                    "type": "select",
                    "proxies": [proxy["name"] for proxy in proxies],
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


def _convert_server_to_clash_proxy(server: ParsedServer) -> dict[str, Any]:
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
        # Get UUID from meta or server attributes
        uuid = server.meta.get("uuid") if server.meta else None
        if not uuid:
            uuid = getattr(server, "uuid", "")

        proxy.update(
            {
                "uuid": uuid,
                "network": server.meta.get("network", "tcp") if server.meta else "tcp",
                "udp": server.meta.get("udp", True) if server.meta else True,
            }
        )

        # Handle TLS/Reality
        # Check for Reality (has tls: true and reality-opts)
        if server.meta and server.meta.get("tls") and server.meta.get("reality-opts"):
            reality_opts = server.meta.get("reality-opts", {})
            proxy.update(
                {
                    "tls": True,
                    "servername": server.meta.get("servername", ""),
                    "reality-opts": {
                        "public-key": reality_opts.get("public-key", ""),
                        "short-id": reality_opts.get("short-id", ""),
                    },
                    "client-fingerprint": server.meta.get(
                        "client-fingerprint", "chrome"
                    ),
                }
            )
            # Add flow if present
            if server.meta.get("flow"):
                proxy["flow"] = server.meta["flow"]
        elif server.meta and server.meta.get("tls"):
            # Regular TLS
            proxy.update(
                {
                    "tls": True,
                    "servername": server.meta.get("servername", ""),
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
