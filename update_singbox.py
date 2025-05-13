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
import os
import sys

from logging_setup import setup_logging
from modules.config_fetch import fetch_json, select_config
from modules.protocol_validation import validate_protocol
from modules.config_generate import generate_config
from modules.service_manage import manage_service

# Configuration with environment variable fallbacks
LOG_FILE = os.getenv("SINGBOX_LOG_FILE", "/var/log/update_singbox.log")
CONFIG_FILE = os.getenv("SINGBOX_CONFIG_FILE", "/etc/sing-box/config.json")
BACKUP_FILE = os.getenv("SINGBOX_BACKUP_FILE", "/etc/sing-box/config.json.bak")
TEMPLATE_FILE = os.getenv("SINGBOX_TEMPLATE_FILE", "./config.template.json")
MAX_LOG_SIZE = int(os.getenv("SINGBOX_MAX_LOG_SIZE", "1048576"))  # 1MB
SUPPORTED_PROTOCOLS = {"vless", "shadowsocks", "vmess", "trojan", "tuic", "hysteria2"}

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

    setup_logging(args.debug, LOG_FILE, MAX_LOG_SIZE)
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
    outbound = validate_protocol(config, SUPPORTED_PROTOCOLS)
    changes_made = generate_config(outbound, TEMPLATE_FILE, CONFIG_FILE, BACKUP_FILE)

    if changes_made:
        # Manage service only if changes were made
        manage_service()
        if args.debug >= 1:
            logging.info("Service restart completed.")

    logging.info("=== Update completed successfully ===")

if __name__ == "__main__":
    main()
