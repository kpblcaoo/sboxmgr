from logging import error, warning

def validate_protocol(config, supported_protocols):
    """Validate protocol and extract parameters."""
    protocol = config.get("protocol")
    if protocol not in supported_protocols:
        error(f"Unsupported protocol: {protocol}")
        raise ValueError(f"Unsupported protocol: {protocol}")

    outbound = {"type": protocol, "tag": "proxy-out"}

    match protocol:
        case "vless":
            vnext = config.get("settings", {}).get("vnext", [{}])[0]
            users = vnext.get("users", [{}])[0]
            params = {
                "server": vnext.get("address"),
                "server_port": vnext.get("port"),
                "uuid": users.get("id"),
            }
            if users.get("flow"):
                params["flow"] = users.get("flow")
            outbound.update(params)
            required_keys = ["server", "server_port", "uuid"]
        case "shadowsocks":
            server = config.get("settings", {}).get("servers", [{}])[0]
            params = {
                "server": server.get("address"),
                "server_port": server.get("port"),
                "method": server.get("method"),
                "password": server.get("password"),
            }
            if server.get("plugin"):
                params["plugin"] = server.get("plugin")
            if server.get("plugin_opts"):
                params["plugin_opts"] = server.get("plugin_opts")
            outbound.update(params)
            required_keys = ["server", "server_port", "method", "password"]
        case "vmess":
            vnext = config.get("settings", {}).get("vnext", [{}])[0]
            users = vnext.get("users", [{}])[0]
            outbound.update({
                "server": vnext.get("address"),
                "server_port": vnext.get("port"),
                "uuid": users.get("id"),
                "security": users.get("security", "auto"),
            })
            required_keys = ["server", "server_port", "uuid"]
        case "trojan":
            server = config.get("settings", {}).get("servers", [{}])[0]
            outbound.update({
                "server": server.get("address"),
                "server_port": server.get("port"),
                "password": server.get("password"),
            })
            required_keys = ["server", "server_port", "password"]
        case "tuic":
            server = config.get("settings", {}).get("servers", [{}])[0]
            params = {
                "server": server.get("address"),
                "server_port": server.get("port"),
                "uuid": server.get("uuid"),
            }
            if server.get("password"):
                params["password"] = server.get("password")
            outbound.update(params)
            required_keys = ["server", "server_port", "uuid"]
        case "hysteria2":
            server = config.get("settings", {}).get("servers", [{}])[0]
            outbound.update({
                "server": server.get("address"),
                "server_port": server.get("port"),
                "password": server.get("password"),
            })
            required_keys = ["server", "server_port", "password"]
        case _:
            error(f"No handler defined for protocol: {protocol}")
            raise ValueError(f"No handler defined for protocol: {protocol}")

    for key in required_keys:
        if not outbound.get(key):
            error(f"Missing required parameter for {protocol}: {key}")
            raise ValueError(f"Missing required parameter for {protocol}: {key}")

    return outbound
