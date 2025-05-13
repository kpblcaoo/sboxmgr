#!/usr/bin/env python3
"""
Скрипт для обновления конфигурации sing-box из удалённого JSON.

Скрипт загружает конфигурацию прокси с указанного URL, проверяет выбранный протокол,
создаёт файл конфигурации sing-box и управляет сервисом sing-box. Поддерживает протоколы:
VLESS, Shadowsocks, VMess, Trojan, TUIC, Hysteria2.

Использование:
    python3 update_singbox.py -u <URL> [-r <remarks> | -i <index>] [-d]
    Пример: python3 update_singbox.py -u https://example.com/config -r "Server1"
    Пример: python3 update_singbox.py -u https://example.com/config -i 2 -d

Переменные окружения:
    SINGBOX_LOG_FILE: Путь к файлу логов (по умолчанию: /var/log/update_singbox.log)
    SINGBOX_CONFIG_FILE: Путь к файлу конфигурации (по умолчанию: /etc/sing-box/config.json)
    SINGBOX_BACKUP_FILE: Путь к бэкапу конфигурации (по умолчанию: /etc/sing-box/config.json.bak)
    SINGBOX_TEMPLATE_FILE: Путь к шаблону конфигурации (по умолчанию: ./config.template.json)
    SINGBOX_MAX_LOG_SIZE: Макс. размер лога в байтах (по умолчанию: 1048576)

Требования:
    Python 3.10 или новее (для конструкции match).


Update sing-box configuration from a remote JSON source.

This script fetches proxy configurations from a specified URL, validates the
selected protocol, generates a sing-box configuration file, and manages the
sing-box service. It supports protocols like VLESS, Shadowsocks, VMess, Trojan,
TUIC, and Hysteria2.

Usage:
    python3 update_singbox.py -u <URL> [-r <remarks> | -i <index>] [-d]
    Example: python3 update_singbox.py -u https://example.com/config -r "Server1"
    Example: python3 update_singbox.py -u https://example.com/config -i 2 -d

Environment Variables:
    SINGBOX_LOG_FILE: Path to log file (default: /var/log/update_singbox.log)
    SINGBOX_CONFIG_FILE: Path to config file (default: /etc/sing-box/config.json)
    SINGBOX_BACKUP_FILE: Path to backup file (default: /etc/sing-box/config.json.bak)
    SINGBOX_TEMPLATE_FILE: Path to template file (default: ./config.template.json)
    SINGBOX_MAX_LOG_SIZE: Max log size in bytes (default: 1048576)

Requirements:
    Python 3.10 or later (for match statement).
"""
import argparse
import json
import logging
import logging.handlers
import os
import shutil
import subprocess
import sys
import platform
from urllib.request import Request, urlopen, ProxyHandler, build_opener, install_opener
from urllib.error import URLError

# Check Python version for match statement compatibility
if sys.version_info < (3, 10):
    print("Error: Python 3.10 or later is required for this script.", file=sys.stderr)
    sys.exit(1)

# Configuration with environment variable fallbacks
LOG_FILE = os.getenv("SINGBOX_LOG_FILE", "/var/log/update_singbox.log")
CONFIG_FILE = os.getenv("SINGBOX_CONFIG_FILE", "/etc/sing-box/config.json")
BACKUP_FILE = os.getenv("SINGBOX_BACKUP_FILE", "/etc/sing-box/config.json.bak")
TEMPLATE_FILE = os.getenv("SINGBOX_TEMPLATE_FILE", "./config.template.json")
MAX_LOG_SIZE = int(os.getenv("SINGBOX_MAX_LOG_SIZE", "1048576"))  # 1MB

# Supported protocols
SUPPORTED_PROTOCOLS = {"vless", "shadowsocks", "vmess", "trojan", "tuic", "hysteria2"}

def handle_error(message, exit_code=1):
    """Log an error message and exit with the specified code."""
    logging.error(f"Error: {message}")
    sys.exit(exit_code)

def setup_logging(debug_level):
    """Configure logging with file and syslog handlers."""
    logger = logging.getLogger()
    
    # Определяем уровень логирования в зависимости от debug_level
    if debug_level == 2:
        logger.setLevel(logging.DEBUG)  # Максимальная детализация
    elif debug_level == 1:
        logger.setLevel(logging.INFO)   # Средняя детализация
    else:
        logger.setLevel(logging.WARNING)  # Минимальная детализация

    # File handler
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setFormatter(logging.Formatter("[%(asctime)s] %(message)s", "%Y-%m-%d %H:%M:%S"))
    logger.addHandler(file_handler)

    # Syslog handler
    try:
        syslog_handler = logging.handlers.SysLogHandler(address="/dev/log")
        syslog_handler.setFormatter(logging.Formatter("sing-box-update: %(message)s"))
        logger.addHandler(syslog_handler)
    except OSError as e:
        logging.warning(f"Failed to configure syslog handler: {e}")

    rotate_logs()

def rotate_logs():
    """Rotate log file if it exceeds MAX_LOG_SIZE."""
    if not os.path.exists(LOG_FILE):
        return
    log_size = os.path.getsize(LOG_FILE)  # Cache file size
    if log_size > MAX_LOG_SIZE:
        for i in range(5, 0, -1):
            old_log = f"{LOG_FILE}.{i}"
            new_log = f"{LOG_FILE}.{i+1}"
            if os.path.exists(old_log):
                os.rename(old_log, new_log)
        os.rename(LOG_FILE, f"{LOG_FILE}.1")
        open(LOG_FILE, "a").close()  # Create empty log file

import requests
import json

def fetch_json(url, proxy_url=None):
    """Fetch JSON from URL with optional proxy."""
    try:
        # Настройка прокси, если указано
        proxies = {
            "http": proxy_url,
            "https": proxy_url,
        } if proxy_url else None

        # Выполняем запрос
        response = requests.get(url, headers={"User-Agent": "ktor-client"}, proxies=proxies)
        response.raise_for_status()  # Проверка на ошибки HTTP
        return response.json()
    except requests.RequestException as e:
        handle_error(f"Failed to fetch configuration from {url}: {e}")
    except json.JSONDecodeError:
        handle_error("Received invalid JSON from URL")

def select_config(json_data, remarks, index):
    """Select proxy configuration by remarks or index."""
    if not json_data:
        handle_error("Received empty configuration")
    if remarks:
        for item in json_data:
            if item.get("remarks") == remarks:
                return item.get("outbounds", [{}])[0]
        handle_error(f"No configuration found with remarks: {remarks}")
    try:
        return json_data[index].get("outbounds", [{}])[0]
    except (IndexError, TypeError):
        handle_error(f"No configuration found at index: {index}")

def validate_protocol(config):
    """Validate protocol and extract parameters."""
    protocol = config.get("protocol")
    if protocol not in SUPPORTED_PROTOCOLS:
        handle_error(f"Unsupported protocol: {protocol}")

    outbound = {"type": protocol, "tag": "proxy-out"}

    # Protocol-specific handling using match statement
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
            handle_error(f"No handler defined for protocol: {protocol}")

    # Validate required parameters
    for key in required_keys:
        if not outbound.get(key):
            handle_error(f"Missing required parameter for {protocol}: {key}")

    # Handle security and transport settings
    outbound = handle_security_and_transport(config, outbound, protocol)
    return outbound

def handle_security_and_transport(config, outbound, protocol):
    """Handle security and transport settings."""
    if protocol == "shadowsocks":
        # Shadowsocks ignores security and non-tcp transport settings
        if config.get("streamSettings", {}).get("security", "none") != "none":
            logging.warning("Security settings ignored for Shadowsocks")
        if config.get("streamSettings", {}).get("network", "tcp") != "tcp":
            logging.warning("Transport settings ignored for Shadowsocks")
        return outbound

    stream_settings = config.get("streamSettings", {})
    security = stream_settings.get("security", "none")
    transport = stream_settings.get("network", "tcp")

    # Validate compatibility of transport and security
    if protocol == "vless" and security == "reality":
        if transport in {"ws", "tuic", "hysteria2", "shadowtls"}:
            handle_error(f"Transport {transport} is incompatible with reality")
    if security == "reality" and protocol != "vless":
        handle_error(f"Security reality is only supported for VLESS")

    # Configure TLS for reality or tls security
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
            handle_error("Missing required parameters for reality: publicKey, shortId")
        outbound["tls"] = tls
    elif security == "tls":
        tls_settings = stream_settings.get("tlsSettings", {})
        tls = {"enabled": True, "server_name": tls_settings.get("serverName")}
        if not tls["server_name"]:
            handle_error("Missing serverName for tls")
        if tls_settings.get("fingerprint"):
            tls["utls"] = {"enabled": True, "fingerprint": tls_settings.get("fingerprint", "chrome")}
        if tls_settings.get("alpn"):
            tls["alpn"] = tls_settings.get("alpn")
        outbound["tls"] = tls
    elif security != "none":
        handle_error(f"Unknown security type: {security}")

    # Configure transport settings (except for reality+tcp+vless)
    if security != "reality" or transport != "tcp" or protocol != "vless":
        transport_settings = {}
        match transport:
            case "ws":
                ws_settings = stream_settings.get("wsSettings", {})
                transport_settings = {"type": "ws"}
                if ws_settings.get("path"):
                    transport_settings["path"] = ws_settings.get("path")
                if ws_settings.get("headers", {}).get("Host"):
                    transport_settings["headers"] = {"Host": ws_settings["headers"]["Host"]}
            case "grpc":
                grpc_settings = stream_settings.get("grpcSettings", {})
                transport_settings = {"type": "grpc", "service_name": grpc_settings.get("serviceName")}
                if not transport_settings["service_name"]:
                    handle_error("Missing serviceName for grpc")
            case "http":
                http_settings = stream_settings.get("httpSettings", {})
                transport_settings = {"type": "http"}
                if http_settings.get("path"):
                    transport_settings["path"] = http_settings.get("path")
                if http_settings.get("host"):
                    transport_settings["headers"] = {"Host": http_settings["host"]}
            case "tcp":
                transport_settings = {"type": "tcp"}
            case _:
                handle_error(f"Unknown transport type: {transport}")
        if transport_settings:
            outbound["transport"] = transport_settings
    return outbound

def generate_config(outbound):
    """Generate sing-box configuration from template."""
    if not os.path.exists(TEMPLATE_FILE):
        handle_error(f"Template file not found: {TEMPLATE_FILE}")

    # Использование временного файла
    temp_config_file = f"{CONFIG_FILE}.tmp"

    with open(TEMPLATE_FILE) as f:
        template = f.read()

    # Замена $outbound_json в шаблоне
    config = template.replace("$outbound_json", json.dumps(outbound, indent=2))

    # Сравнение с текущим конфигом
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as current_config_file:
            current_config = current_config_file.read()
            if current_config.strip() == config.strip():
                logging.info("Configuration has not changed. Skipping update.")
                return False  # No changes, skip further actions

    with open(temp_config_file, "w") as f:
        f.write(config)
    logging.info(f"Temporary configuration written to {temp_config_file}")

    # Проверка конфигурации с помощью sing-box
    try:
        subprocess.run(["sing-box", "check", "-c", temp_config_file], check=True)
        logging.info("Temporary configuration validated successfully")
    except (subprocess.CalledProcessError, FileNotFoundError):
        handle_error("Temporary configuration is invalid or sing-box not found")

    # Если проверка успешна, делаем резервное копирование и заменяем основной файл
    if os.path.exists(CONFIG_FILE):
        os.rename(CONFIG_FILE, BACKUP_FILE)
        logging.info(f"Created backup: {BACKUP_FILE}")

    os.rename(temp_config_file, CONFIG_FILE)
    logging.info(f"Configuration updated for {outbound['type']}")
    return True  # Changes were made

def manage_service():
    """Restart or start sing-box service."""
    if not shutil.which("systemctl"):
        handle_error("systemctl not found; cannot manage sing-box service")
    try:
        result = subprocess.run(["systemctl", "is-active", "--quiet", "sing-box.service"], check=False)
        action = "restart" if result.returncode == 0 else "start"
        subprocess.run(["systemctl", action, "sing-box.service"], check=True)
        logging.info(f"Service {action}ed")
    except subprocess.CalledProcessError:
        handle_error(f"Failed to {action} sing-box service")

def main():
    """Main function to update sing-box configuration."""
    parser = argparse.ArgumentParser(description="Update sing-box configuration")
    parser.add_argument("-u", "--url", required=True, help="URL for proxy configuration")
    parser.add_argument("-r", "--remarks", help="Select server by remarks")
    parser.add_argument("-i", "--index", type=int, default=0, help="Select server by index (default: 0)")
    parser.add_argument("-d", "--debug", type=int, choices=[0, 1, 2], default=0,
                        help="Set debug level: 0 for minimal, 1 for detailed, 2 for verbose")
    parser.add_argument("--proxy", help="Proxy URL (e.g., socks5://127.0.0.1:1080 or https://proxy.example.com)")
    args = parser.parse_args()

    setup_logging(args.debug)
    logging.info("=== Starting sing-box configuration update ===")

    # Fetching configuration
    json_data = fetch_json(args.url, proxy_url=args.proxy)
    if args.debug >= 1:
        logging.info(f"Fetched server list from: {args.url}")
    if args.debug >= 2:
        logging.debug(f"Fetched configuration: {json.dumps(json_data, indent=2)}")

    # Selecting configuration
    config = select_config(json_data, args.remarks, args.index)
    if args.debug >= 1:
        logging.info(f"Selected configuration by remarks: {args.remarks} or index: {args.index}")
    if args.debug >= 2:
        logging.debug(f"Selected configuration details: {json.dumps(config, indent=2)}")

    # Validate and generate configuration
    outbound = validate_protocol(config)
    changes_made = generate_config(outbound)

    if changes_made:
        # Manage service only if changes were made
        manage_service()
        if args.debug >= 1:
            logging.info("Service restart completed.")

    logging.info("=== Update completed successfully ===")
    
if __name__ == "__main__":
    main()
