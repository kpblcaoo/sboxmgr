"""Protocol-specific configuration handling.

This module contains protocol-specific utilities for handling different VPN
protocol configurations (VMess, VLESS, Trojan, Shadowsocks, etc.). It provides
normalization, validation, and conversion functions for protocol parameters
and connection details.
"""
from logging import error

def validate_protocol(config, supported_protocols):
    """Validate protocol and extract parameters."""
    protocol = config.get("type")
    if protocol not in supported_protocols:
        error(f"Unsupported protocol: {protocol}")
        raise ValueError(f"Unsupported protocol: {protocol}")

    outbound = {"type": protocol, "tag": config.get("tag", "proxy-out")}

    if protocol == "vless":
        params = {
            "server": config.get("server"),
            "server_port": config.get("server_port"),
            "uuid": config.get("uuid"),
        }
        if config.get("flow"):
            params["flow"] = config.get("flow")
        if config.get("tls"):
            params["tls"] = config.get("tls")
        outbound.update(params)
        required_keys = ["server", "server_port", "uuid"]
    elif protocol == "shadowsocks":
        params = {
            "server": config.get("server"),
            "server_port": config.get("server_port"),
            "method": config.get("method"),
            "password": config.get("password"),
        }
        if config.get("network"):
            params["network"] = config.get("network")
        outbound.update(params)
        required_keys = ["server", "server_port", "method", "password"]
    elif protocol == "vmess":
        params = {
            "server": config.get("server"),
            "server_port": config.get("server_port"),
            "uuid": config.get("uuid"),
            "security": config.get("security", "auto"),
        }
        if config.get("tls"):
            params["tls"] = config.get("tls")
        outbound.update(params)
        required_keys = ["server", "server_port", "uuid"]
    elif protocol == "trojan":
        params = {
            "server": config.get("server"),
            "server_port": config.get("server_port"),
            "password": config.get("password"),
        }
        if config.get("tls"):
            params["tls"] = config.get("tls")
        outbound.update(params)
        required_keys = ["server", "server_port", "password"]
    elif protocol == "tuic":
        params = {
            "server": config.get("server"),
            "server_port": config.get("server_port"),
            "uuid": config.get("uuid"),
        }
        if config.get("password"):
            params["password"] = config.get("password")
        if config.get("tls"):
            params["tls"] = config.get("tls")
        outbound.update(params)
        required_keys = ["server", "server_port", "uuid"]
    elif protocol == "hysteria2":
        params = {
            "server": config.get("server"),
            "server_port": config.get("server_port"),
            "password": config.get("password"),
        }
        if config.get("tls"):
            params["tls"] = config.get("tls")
        outbound.update(params)
        required_keys = ["server", "server_port", "password"]
    else:
        error(f"No handler defined for protocol: {protocol}")
        raise ValueError(f"No handler defined for protocol: {protocol}")

    for key in required_keys:
        if not outbound.get(key):
            error(f"Missing required parameter for {protocol}: {key}")
            raise ValueError(f"Missing required parameter for {protocol}: {key}")

    return outbound
