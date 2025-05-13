from logging import error, warning

def validate_protocol(config, supported_protocols):
    """Validate protocol and extract parameters."""
    protocol = config.get("type")
    if protocol not in supported_protocols:
        error(f"Unsupported protocol: {protocol}")
        raise ValueError(f"Unsupported protocol: {protocol}")

    outbound = {"type": protocol, "tag": config.get("tag", "proxy-out")}

    match protocol:
        case "vless":
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
        case "shadowsocks":
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
        case "vmess":
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
        case "trojan":
            params = {
                "server": config.get("server"),
                "server_port": config.get("server_port"),
                "password": config.get("password"),
            }
            if config.get("tls"):
                params["tls"] = config.get("tls")
            outbound.update(params)
            required_keys = ["server", "server_port", "password"]
        case "tuic":
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
        case "hysteria2":
            params = {
                "server": config.get("server"),
                "server_port": config.get("server_port"),
                "password": config.get("password"),
            }
            if config.get("tls"):
                params["tls"] = config.get("tls")
            outbound.update(params)
            required_keys = ["server", "server_port", "password"]
        case _:
            error(f"No handler defined for protocol: {protocol}")
            raise ValueError(f"No handler defined for protocol: {protocol}")

    for key in required_keys:
        if not outbound.get(key):
            error(f"Missing required parameter for {protocol}: {key}")
            raise ValueError(f"Missing required parameter for {protocol}: {key}")

    return outbound