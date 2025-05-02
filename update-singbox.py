#!/usr/bin/env python3
import argparse
import json
import logging
import os
import stat
import subprocess
import sys
from urllib.request import Request, urlopen
from urllib.error import URLError

# Configuration
LOG_FILE = "/var/log/update-singbox.log"
CONFIG_FILE = "/etc/sing-box/config.json"
BACKUP_FILE = "/etc/sing-box/config.json.bak"
TEMPLATE_FILE = "./config.template.json"
MAX_LOG_SIZE = 1048576  # 1MB

# Supported protocols
SUPPORTED_PROTOCOLS = {"vless", "shadowsocks", "vmess", "trojan", "tuic", "hysteria2"}

def setup_logging(debug):
    """Configure logging with rotation."""
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    handler = logging.FileHandler(LOG_FILE)
    handler.setFormatter(logging.Formatter("[%(asctime)s] %(message)s", "%Y-%m-%d %H:%M:%S"))
    logger.addHandler(handler)
    rotate_logs()

def rotate_logs():
    """Rotate log file if it exceeds MAX_LOG_SIZE."""
    if not os.path.exists(LOG_FILE):
        return
    if os.path.getsize(LOG_FILE) > MAX_LOG_SIZE:
        for i in range(5, 0, -1):
            old_log = f"{LOG_FILE}.{i}"
            new_log = f"{LOG_FILE}.{i+1}"
            if os.path.exists(old_log):
                os.rename(old_log, new_log)
        os.rename(LOG_FILE, f"{LOG_FILE}.1")
        open(LOG_FILE, "a").close()  # Create empty log file

def fetch_json(url):
    """Fetch JSON from URL."""
    try:
        req = Request(url, headers={"User-Agent": "ktor-client"})
        with urlopen(req) as response:
            return json.loads(response.read().decode())
    except URLError as e:
        logging.error(f"Failed to fetch configuration from {url}: {e}")
        sys.exit(1)
    except json.JSONDecodeError:
        logging.error("Received invalid JSON from URL")
        sys.exit(1)

def select_config(json_data, remarks, index):
    """Select proxy configuration by remarks or index."""
    if not json_data:
        logging.error("Received empty configuration")
        sys.exit(1)
    if remarks:
        for item in json_data:
            if item.get("remarks") == remarks:
                return item.get("outbounds", [{}])[0]
        logging.error(f"No configuration found with remarks: {remarks}")
        sys.exit(1)
    try:
        return json_data[index].get("outbounds", [{}])[0]
    except (IndexError, TypeError):
        logging.error(f"No configuration found at index: {index}")
        sys.exit(1)

def validate_protocol(config):
    """Validate protocol and extract parameters."""
    protocol = config.get("protocol")
    if protocol not in SUPPORTED_PROTOCOLS:
        logging.error(f"Unsupported protocol: {protocol}")
        sys.exit(1)
    outbound = {"type": protocol, "tag": "proxy-out"}

    if protocol == "vless":
        vnext = config.get("settings", {}).get("vnext", [{}])[0]
        users = vnext.get("users", [{}])[0]
        outbound.update({
            "server": vnext.get("address"),
            "server_port": vnext.get("port"),
            "uuid": users.get("id"),
        })
        if users.get("flow"):
            outbound["flow"] = users.get("flow")
    elif protocol == "shadowsocks":
        server = config.get("settings", {}).get("servers", [{}])[0]
        outbound.update({
            "server": server.get("address"),
            "server_port": server.get("port"),
            "method": server.get("method"),
            "password": server.get("password"),
        })
        if server.get("plugin"):
            outbound["plugin"] = server.get("plugin")
        if server.get("plugin_opts"):
            outbound["plugin_opts"] = server.get("plugin_opts")
    elif protocol == "vmess":
        vnext = config.get("settings", {}).get("vnext", [{}])[0]
        users = vnext.get("users", [{}])[0]
        outbound.update({
            "server": vnext.get("address"),
            "server_port": vnext.get("port"),
            "uuid": users.get("id"),
            "security": users.get("security", "auto"),
        })
    elif protocol == "trojan":
        server = config.get("settings", {}).get("servers", [{}])[0]
        outbound.update({
            "server": server.get("address"),
            "server_port": server.get("port"),
            "password": server.get("password"),
        })
    elif protocol == "tuic":
        server = config.get("settings", {}).get("servers", [{}])[0]
        outbound.update({
            "server": server.get("address"),
            "server_port": server.get("port"),
            "uuid": server.get("uuid"),
        })
        if server.get("password"):
            outbound["password"] = server.get("password")
    elif protocol == "hysteria2":
        server = config.get("settings", {}).get("servers", [{}])[0]
        outbound.update({
            "server": server.get("address"),
            "server_port": server.get("port"),
            "password": server.get("password"),
        })

    for key in ["server", "server_port"] + (["uuid"] if protocol in {"vless", "vmess", "tuic"} else []) + (["password"] if protocol in {"shadowsocks", "trojan", "hysteria2"} else []) + (["method"] if protocol == "shadowsocks" else []):
        if not outbound.get(key):
            logging.error(f"Missing required parameter for {protocol}: {key}")
            sys.exit(1)

    # Handle security and transport (skip for shadowsocks)
    if protocol != "shadowsocks":
        stream_settings = config.get("streamSettings", {})
        security = stream_settings.get("security", "none")
        transport = stream_settings.get("network", "tcp")

        if protocol == "vless" and security == "reality":
            if transport in {"ws", "tuic", "hysteria2", "shadowtls"}:
                logging.error(f"Transport {transport} is incompatible with reality")
                sys.exit(1)
        if security == "reality" and protocol != "vless":
            logging.error(f"Security reality is only supported for VLESS")
            sys.exit(1)

        if security == "reality":
            reality_settings = stream_settings.get("realitySettings", {})
            tls = {
                "enabled": True,
                "reality": {
                    "enabled": True,
                    "public_key": reality_settings.get("publicKey"),
                    "short_id": reality_settings.get("shortId"),
                },
            }
            if reality_settings.get("serverName"):
                tls["server_name"] = reality_settings.get("serverName")
            if reality_settings.get("fingerprint"):
                tls["utls"] = {"enabled": True, "fingerprint": reality_settings.get("fingerprint", "chrome")}
            if not all(tls["reality"].get(k) for k in ["public_key", "short_id"]):
                logging.error("Missing required parameters for reality: publicKey, shortId")
                sys.exit(1)
            outbound["tls"] = tls
        elif security == "tls":
            tls_settings = stream_settings.get("tlsSettings", {})
            tls = {"enabled": True, "server_name": tls_settings.get("serverName")}
            if not tls["server_name"]:
                logging.error("Missing serverName for tls")
                sys.exit(1)
            if tls_settings.get("fingerprint"):
                tls["utls"] = {"enabled": True, "fingerprint": tls_settings.get("fingerprint", "chrome")}
            if tls_settings.get("alpn"):
                tls["alpn"] = tls_settings.get("alpn")
            outbound["tls"] = tls
        elif security != "none":
            logging.error(f"Unknown security type: {security}")
            sys.exit(1)

        if security != "reality" or transport != "tcp" or protocol != "vless":
            transport_settings = {}
            if transport == "ws":
                ws_settings = stream_settings.get("wsSettings", {})
                transport_settings = {"type": "ws"}
                if ws_settings.get("path"):
                    transport_settings["path"] = ws_settings.get("path")
                if ws_settings.get("headers", {}).get("Host"):
                    transport_settings["headers"] = {"Host": ws_settings["headers"]["Host"]}
            elif transport == "grpc":
                grpc_settings = stream_settings.get("grpcSettings", {})
                transport_settings = {"type": "grpc", "service_name": grpc_settings.get("serviceName")}
                if not transport_settings["service_name"]:
                    logging.error("Missing serviceName for grpc")
                    sys.exit(1)
            elif transport == "http":
                http_settings = stream_settings.get("httpSettings", {})
                transport_settings = {"type": "http"}
                if http_settings.get("path"):
                    transport_settings["path"] = http_settings.get("path")
                if http_settings.get("host"):
                    transport_settings["headers"] = {"Host": http_settings["host"]}
            elif transport == "tcp":
                transport_settings = {"type": "tcp"}
            else:
                logging.error(f"Unknown transport type: {transport}")
                sys.exit(1)
            if transport_settings:
                outbound["transport"] = transport_settings
    else:
        if config.get("streamSettings", {}).get("security", "none") != "none":
            logging.warning("Security settings ignored for Shadowsocks")
        if config.get("streamSettings", {}).get("network", "tcp") != "tcp":
            logging.warning("Transport settings ignored for Shadowsocks")

    return outbound

def generate_config(outbound):
    """Generate sing-box configuration from template."""
    if os.path.exists(CONFIG_FILE):
        os.rename(CONFIG_FILE, BACKUP_FILE)
        logging.info(f"Created backup: {BACKUP_FILE}")
    
    with open(TEMPLATE_FILE) as f:
        template = f.read()
    
    # Replace $outbound_json with JSON string
    config = template.replace("$outbound_json", json.dumps(outbound, indent=2))
    
    with open(CONFIG_FILE, "w") as f:
        f.write(config)
    logging.info(f"Configuration updated for {outbound['type']}")

def manage_service():
    """Restart or start sing-box service."""
    try:
        result = subprocess.run(["systemctl", "is-active", "--quiet", "sing-box.service"], check=False)
        action = "restart" if result.returncode == 0 else "start"
        subprocess.run(["systemctl", action, "sing-box.service"], check=True)
        logging.info(f"Service {action}ed")
    except subprocess.CalledProcessError:
        logging.error(f"Failed to {action} sing-box service")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Update sing-box configuration")
    parser.add_argument("-u", "--url", required=True, help="URL for proxy configuration")
    parser.add_argument("-r", "--remarks", help="Select server by remarks")
    parser.add_argument("-i", "--index", type=int, default=0, help="Select server by index (default: 0)")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    setup_logging(args.debug)
    logging.info("=== Starting sing-box configuration update ===")

    json_data = fetch_json(args.url)
    config = select_config(json_data, args.remarks, args.index)
    outbound = validate_protocol(config)
    generate_config(outbound)
    manage_service()
    logging.info("Update completed")

if __name__ == "__main__":
    main()