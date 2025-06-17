#!/usr/bin/env python3
"""
Update sing-box configuration from a remote JSON source.

This script fetches proxy configurations from a specified URL, validates the
selected protocol, generates a sing-box configuration file, and manages the
sing-box service. It supports protocols like VLESS, Shadowsocks, VMess, Trojan,
TUIC, and Hysteria2. By default, it enables auto-selection of servers using urltest.
If a specific server is selected by remarks or index, only that server is included.

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
    SINGBOX_URL: URL for proxy configuration (optional)
    SINGBOX_REMARKS: Select server by remarks
    SINGBOX_INDEX: Select server by index
    SINGBOX_DEBUG: Set debug level: 0 for minimal, 1 for detailed, 2 for verbose
    SINGBOX_PROXY: Proxy URL (e.g., socks5://127.0.0.1:1080 or https://proxy.example.com)
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
from modules.server_management import list_servers, load_exclusions, apply_exclusions, exclude_servers, remove_exclusions, view_exclusions, clear_exclusions, load_selected_config, save_selected_config, generate_server_id

# Configuration with environment variable fallbacks
LOG_FILE = os.getenv("SINGBOX_LOG_FILE", "/var/log/update_singbox.log")
CONFIG_FILE = os.getenv("SINGBOX_CONFIG_FILE", "/etc/sing-box/config.json")
BACKUP_FILE = os.getenv("SINGBOX_BACKUP_FILE", "/etc/sing-box/config.json.bak")
TEMPLATE_FILE = os.getenv("SINGBOX_TEMPLATE_FILE", "./config.template.json")
MAX_LOG_SIZE = int(os.getenv("SINGBOX_MAX_LOG_SIZE", "1048576"))  # 1MB
SUPPORTED_PROTOCOLS = {"vless", "shadowsocks", "vmess", "trojan", "tuic", "hysteria2"}

def main():
    """Main function to update sing-box configuration."""
    def parse_comma_separated_values(value):
        return [int(v.strip()) for v in value.split(',') if v.strip().isdigit()]

    parser = argparse.ArgumentParser(description="Update sing-box configuration")
    parser.add_argument("-u", "--url", help="URL for proxy configuration")
    parser.add_argument("-r", "--remarks", nargs='*', help="Select server by remarks")
    parser.add_argument("-i", "--index", type=parse_comma_separated_values, help="Select server by index")
    parser.add_argument("-d", "--debug", type=int, choices=[0, 1, 2], default=0,
                        help="Set debug level: 0 for minimal, 1 for detailed, 2 for verbose")
    parser.add_argument("--proxy", help="Proxy URL (e.g., socks5://127.0.0.1:1080 or https://proxy.example.com)")
    parser.add_argument("-l", "--list-servers", action="store_true", help="List all servers with indices")
    parser.add_argument("-e", "--exclude", nargs='?', const='', help="Exclude servers by index or name")
    parser.add_argument("--clear-exclusions", action="store_true", help="Clear all current exclusions")
    parser.add_argument("--dry-run", action="store_true", help="Тестировать генерацию конфига без изменений")
    args = parser.parse_args()

    url = args.url or os.getenv("SINGBOX_URL")
    remarks = args.remarks or os.getenv("SINGBOX_REMARKS")
    indices = args.index if args.index is not None else os.getenv("SINGBOX_INDEX")
    debug_level = int(os.getenv("SINGBOX_DEBUG", args.debug))
    proxy = args.proxy or os.getenv("SINGBOX_PROXY")

    setup_logging(debug_level, LOG_FILE, MAX_LOG_SIZE)
    logging.info("=== Starting sing-box configuration update ===")

    if args.list_servers or args.exclude is not None:
        if not url and args.exclude is not None and args.exclude:
            print("Error: URL is required for excluding servers.")
            return

    json_data = fetch_json(url, proxy_url=proxy) if url else None
    if not json_data:
        logging.error("No configuration data fetched. Exiting.")
        return
    if debug_level >= 1:
        logging.info(f"Fetched server list from: {url}")
    if debug_level >= 2:
        logging.debug(f"Fetched configuration: {json.dumps(json_data, indent=2)}")

    if args.list_servers:
        list_servers(json_data, SUPPORTED_PROTOCOLS, debug_level)
        return

    if args.exclude is not None:
        if args.exclude == '':
            view_exclusions(debug_level)
            return
        else:
            add_exclusions = [x for x in args.exclude.split(',') if not x.startswith('-')]
            remove_exclusions = [x for x in args.exclude.split(',') if x.startswith('-')]
            if add_exclusions:
                exclude_servers(json_data, add_exclusions, SUPPORTED_PROTOCOLS, debug_level)
            if remove_exclusions:
                remove_exclusions(remove_exclusions, json_data, SUPPORTED_PROTOCOLS, debug_level)
            generate_config_after_exclusion(json_data, debug_level)
            return

    if args.clear_exclusions:
        clear_exclusions()
        return

    exclusions = load_exclusions()
    excluded_ids = {exclusion["id"] for exclusion in exclusions["exclusions"]}

    selected_indices = []
    if indices is not None:
        selected_indices = indices
    else:
        saved_config = load_selected_config()
        selected_indices = [int(item["index"]) for item in saved_config["selected"] if "index" in item]

    outbounds = []
    excluded_ips = []
    if remarks or selected_indices:
        if isinstance(selected_indices, list) and len(selected_indices) > 1:
            selected_servers = []
            for idx in selected_indices:
                config = select_config(json_data, remarks, idx)
                outbound = validate_protocol(config, SUPPORTED_PROTOCOLS)
                outbounds.append(outbound)
                if "server" in outbound:
                    if outbound["server"] in excluded_ids:
                        logging.warning(f"Server {outbound['server']} at index {idx} is in the exclusion list.")
                    excluded_ips.append(outbound["server"])
                selected_servers.append({"index": idx, "id": generate_server_id(outbound)})
                if debug_level >= 1:
                    logging.info(f"Selected server at index {idx}")
                if debug_level >= 2:
                    logging.debug(f"Selected configuration details: {json.dumps(config, indent=2)}")
            save_selected_config({"selected": selected_servers})
        else:
            idx = selected_indices[0] if selected_indices else None
            config = select_config(json_data, remarks, idx)
            outbound = validate_protocol(config, SUPPORTED_PROTOCOLS)
            outbounds = [outbound]
            if "server" in outbound:
                if outbound["server"] in excluded_ids:
                    logging.warning(f"Server {outbound['server']} at index {idx} is in the exclusion list.")
                excluded_ips.append(outbound["server"])
            save_selected_config({"selected": [{"index": idx, "id": generate_server_id(outbound)}]})
            if debug_level >= 1:
                logging.info(f"Selected server at index {idx}")
            if debug_level >= 2:
                logging.debug(f"Selected configuration details: {json.dumps(config, indent=2)}")
    else:
        if not json_data:
            print("Error: URL is required for auto-selection.")
            return
        if isinstance(json_data, dict) and "outbounds" in json_data:
            configs = [
                outbound for outbound in json_data["outbounds"]
                if outbound.get("type") in SUPPORTED_PROTOCOLS
            ]
        else:
            configs = json_data

        configs = apply_exclusions(configs, excluded_ids, debug_level)

        for idx, config in enumerate(configs):
            try:
                outbound = validate_protocol(config, SUPPORTED_PROTOCOLS)
                if not outbound["tag"].startswith("proxy-"):
                    outbounds.append(outbound)
                else:
                    outbound["tag"] = f"proxy-{chr(97 + idx)}"
                    outbounds.append(outbound)
                if "server" in outbound:
                    excluded_ips.append(outbound["server"])
            except ValueError as e:
                logging.warning(f"Skipping invalid configuration at index {idx}: {e}")

        if not outbounds:
            logging.warning("No valid configurations found for auto-selection, using direct")
            outbounds = []
        if debug_level >= 1:
            logging.info(f"Prepared {len(outbounds)} servers for auto-selection")
            logging.info(f"Excluded IPs: {excluded_ips}")

    if args.dry_run:
        import tempfile
        import subprocess
        logging.info("Режим dry-run: создаём временный конфиг и валидируем его")
        # Подготовка outbounds и excluded_ips как в основной логике
        # --- Копируем логику выбора outbounds и excluded_ips ---
        exclusions = load_exclusions()
        excluded_ids = {exclusion["id"] for exclusion in exclusions["exclusions"]}
        selected_indices = []
        if args.index is not None:
            selected_indices = args.index
        else:
            saved_config = load_selected_config()
            selected_indices = [int(item["index"]) for item in saved_config["selected"] if "index" in item]
        outbounds = []
        excluded_ips = []
        if args.remarks or selected_indices:
            if isinstance(selected_indices, list) and len(selected_indices) > 1:
                for idx in selected_indices:
                    config = select_config(json_data, args.remarks, idx)
                    outbound = validate_protocol(config, SUPPORTED_PROTOCOLS)
                    outbounds.append(outbound)
                    if "server" in outbound:
                        if outbound["server"] in excluded_ids:
                            logging.warning(f"Server {outbound['server']} at index {idx} is in the exclusion list.")
                        excluded_ips.append(outbound["server"])
            else:
                idx = selected_indices[0] if selected_indices else None
                config = select_config(json_data, args.remarks, idx)
                outbound = validate_protocol(config, SUPPORTED_PROTOCOLS)
                outbounds = [outbound]
                if "server" in outbound:
                    if outbound["server"] in excluded_ids:
                        logging.warning(f"Server {outbound['server']} at index {idx} is in the exclusion list.")
                    excluded_ips.append(outbound["server"])
        else:
            if isinstance(json_data, dict) and "outbounds" in json_data:
                configs = [
                    outbound for outbound in json_data["outbounds"]
                    if outbound.get("type") in SUPPORTED_PROTOCOLS
                ]
            else:
                configs = json_data
            configs = apply_exclusions(configs, excluded_ids, debug_level)
            for idx, config in enumerate(configs):
                try:
                    outbound = validate_protocol(config, SUPPORTED_PROTOCOLS)
                    if not outbound["tag"].startswith("proxy-"):
                        outbounds.append(outbound)
                    else:
                        outbound["tag"] = f"proxy-{chr(97 + idx)}"
                        outbounds.append(outbound)
                    if "server" in outbound:
                        excluded_ips.append(outbound["server"])
                except ValueError as e:
                    logging.warning(f"Skipping invalid configuration at index {idx}: {e}")
        # --- Конец подготовки outbounds и excluded_ips ---
        # Генерируем временный файл
        import json
        from modules.config_generate import generate_temp_config, validate_config_file
        with tempfile.NamedTemporaryFile("w+", suffix=".json", delete=False) as tmp:
            temp_path = tmp.name
            config_content = generate_temp_config(outbounds, TEMPLATE_FILE, excluded_ips)
            tmp.write(config_content)
        valid, output = validate_config_file(temp_path)
        if valid:
            logging.info("Конфиг валиден. Проверка прошла успешно.")
        else:
            logging.error(f"Конфиг невалиден:\n{output}")
        os.unlink(temp_path)
        logging.info("Временный файл удалён. Основной конфиг не изменён, сервис не перезапущен.")
        return

    changes_made = generate_config(outbounds, TEMPLATE_FILE, CONFIG_FILE, BACKUP_FILE, excluded_ips)

    if changes_made:
        manage_service()
        if debug_level >= 1:
            logging.info("Service restart completed.")

    logging.info("=== Update completed successfully ===")

def generate_config_after_exclusion(json_data, debug_level):
    """Generate configuration after applying exclusions."""
    exclusions = load_exclusions()
    excluded_ids = {exclusion["id"] for exclusion in exclusions["exclusions"]}

    if isinstance(json_data, dict) and "outbounds" in json_data:
        configs = [
            outbound for outbound in json_data["outbounds"]
            if outbound.get("type") in SUPPORTED_PROTOCOLS
        ]
    else:
        configs = json_data

    configs = apply_exclusions(configs, excluded_ids, debug_level)

    outbounds = []
    excluded_ips = []
    for idx, config in enumerate(configs):
        try:
            outbound = validate_protocol(config, SUPPORTED_PROTOCOLS)
            if not outbound["tag"].startswith("proxy-"):
                outbounds.append(outbound)
            else:
                outbound["tag"] = f"proxy-{chr(97 + idx)}"
                outbounds.append(outbound)
            if "server" in outbound:
                excluded_ips.append(outbound["server"])
        except ValueError as e:
            logging.warning(f"Skipping invalid configuration at index {idx}: {e}")

    if not outbounds:
        logging.warning("No valid configurations found for auto-selection, using direct")
        outbounds = []
    if debug_level >= 1:
        logging.info(f"Prepared {len(outbounds)} servers for auto-selection")
        logging.info(f"Excluded IPs: {excluded_ips}")

    generate_config(outbounds, TEMPLATE_FILE, CONFIG_FILE, BACKUP_FILE, excluded_ips)

if __name__ == "__main__":
    main()