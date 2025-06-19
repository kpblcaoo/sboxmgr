#!/usr/bin/env python3
"""
sboxctl — CLI для управления конфигом sing-box, exclusions, dry-run и др.

Usage:
    sboxctl -u <URL> [-r <remarks> | -i <index>] [-d]
    Example: sboxctl -u https://example.com/config -r "Server1"
    Example: sboxctl -u https://example.com/config -i 2 -d

Environment Variables:
    SBOXMGR_LOG_FILE: Path to log file (default: /var/log/sboxmgr.log)
    SBOXMGR_CONFIG_FILE: Path to config file (default: /etc/sboxmgr/config.json)
    SBOXMGR_BACKUP_FILE: Path to backup file (default: /etc/sboxmgr/config.json.bak)
    SBOXMGR_TEMPLATE_FILE: Path to template file (default: ./config.template.json)
    SBOXMGR_MAX_LOG_SIZE: Max log size in bytes (default: 1048576)
    SINGBOX_URL: URL for proxy configuration (optional)
    SBOXMGR_REMARKS: Select server by remarks
    SBOXMGR_INDEX: Select server by index
    SBOXMGR_DEBUG: Set debug level: 0 for minimal, 1 for detailed, 2 for verbose
    SBOXMGR_PROXY: Proxy URL (e.g., socks5://127.0.0.1:1080 or https://proxy.example.com)
"""
import argparse
import logging
import os
import sys
import json
from logsetup.setup import setup_logging
import json
from dotenv import load_dotenv

from sboxmgr.config.fetch import fetch_json, select_config
from sboxmgr.config.protocol import validate_protocol
from sboxmgr.config.generate import generate_config, generate_temp_config, validate_config_file
from sboxmgr.service.manage import manage_service
from sboxmgr.server.selection import list_servers
from sboxmgr.server.management import apply_exclusions
from sboxmgr.server.exclusions import load_exclusions, save_exclusions, exclude_servers, remove_exclusions, view_exclusions, clear_exclusions
from sboxmgr.server.state import load_selected_config, save_selected_config
from sboxmgr.utils.id import generate_server_id
from sboxmgr.utils.cli_common import prepare_selection

# Configuration with environment variable fallbacks
LOG_FILE = os.getenv("SBOXMGR_LOG_FILE", "/var/log/sboxmgr.log")
CONFIG_FILE = os.getenv("SBOXMGR_CONFIG_FILE", "/etc/sboxmgr/config.json")
BACKUP_FILE = os.getenv("SBOXMGR_BACKUP_FILE", "/etc/sboxmgr/config.json.bak")
TEMPLATE_FILE = os.getenv("SBOXMGR_TEMPLATE_FILE", "./config.template.json")
MAX_LOG_SIZE = int(os.getenv("SBOXMGR_MAX_LOG_SIZE", "1048576"))  # 1MB
SUPPORTED_PROTOCOLS = {"vless", "shadowsocks", "vmess", "trojan", "tuic", "hysteria2"}

load_dotenv()

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
    parser.add_argument("--exclude-only", action="store_true", help="Только обновить exclusions.json, не генерировать конфиг")
    args = parser.parse_args()

    LOG_FILE = os.getenv("SBOXMGR_LOG_FILE", "/var/log/sboxmgr.log")
    MAX_LOG_SIZE = int(os.getenv("SBOXMGR_MAX_LOG_SIZE", "1048576"))

    # Обработка clear-exclusions до любых проверок URL
    if args.clear_exclusions:
        debug_level = int(os.getenv("SBOXMGR_DEBUG", args.debug))
        setup_logging(debug_level, LOG_FILE, MAX_LOG_SIZE)
        logging.info("=== CLI: clear-exclusions ===")
        clear_exclusions()
        return

    url = args.url or os.getenv("SINGBOX_URL")
    remarks = args.remarks or os.getenv("SBOXMGR_REMARKS")
    indices = args.index if args.index is not None else os.getenv("SBOXMGR_INDEX")
    debug_level = int(os.getenv("SBOXMGR_DEBUG", args.debug))
    proxy = args.proxy or os.getenv("SBOXMGR_PROXY")

    setup_logging(debug_level, LOG_FILE, MAX_LOG_SIZE)
    logging.info("=== Starting sing-box configuration update ===")

    if args.list_servers or args.exclude is not None:
        if not url and args.exclude is not None and args.exclude:
            print("Error: URL is required for excluding servers.")
            return

    json_data = fetch_json(url, proxy_url=proxy) if url else None
    if not json_data:
        print("[Ошибка] Не удалось загрузить конфигурацию с указанного URL. Проверьте адрес и доступность ресурса.")
        logging.error("No configuration data fetched. Exiting.")
        sys.exit(1)
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
            remove_exclusions_list = [x for x in args.exclude.split(',') if x.startswith('-')]
            if add_exclusions:
                exclude_servers(json_data, add_exclusions, SUPPORTED_PROTOCOLS, debug_level)
            if remove_exclusions_list:
                remove_exclusions(remove_exclusions_list, json_data, SUPPORTED_PROTOCOLS, debug_level)
            if args.exclude_only:
                return
            generate_config_after_exclusion(json_data, debug_level, args.dry_run)
            return

    exclusions = load_exclusions(dry_run=args.dry_run)
    selected_indices = []
    if indices is not None:
        selected_indices = indices
    else:
        saved_config = load_selected_config()
        selected_indices = [int(item["index"]) for item in saved_config["selected"] if "index" in item]

    outbounds, excluded_ips, selected_servers = prepare_selection(
        json_data,
        selected_indices,
        remarks,
        SUPPORTED_PROTOCOLS,
        exclusions,
        debug_level=debug_level,
        dry_run=args.dry_run
    )

    if remarks or selected_indices:
        if not args.dry_run and selected_servers:
            save_selected_config({"selected": selected_servers})
    else:
        if not json_data:
            print("Error: URL is required for auto-selection.")
            return

    if args.dry_run:
        import tempfile
        import subprocess
        logging.info("Режим dry-run: создаём временный конфиг и валидируем его")
        from sboxmgr.config.generate import generate_temp_config, validate_config_file
        with tempfile.NamedTemporaryFile("w+", suffix=".json", delete=False) as tmp:
            temp_path = tmp.name
            config_content = generate_temp_config(outbounds, TEMPLATE_FILE, excluded_ips)
            tmp.write(config_content)
        valid, output = validate_config_file(temp_path)
        if valid:
            print("Dry run: config is valid")
            logging.info("Конфиг валиден. Проверка прошла успешно.")
        else:
            logging.error(f"Конфиг невалиден:\n{output}")
        os.unlink(temp_path)
        logging.info("Временный файл удалён. Основной конфиг не изменён, сервис не перезапущен.")
        return

    try:
        changes_made = generate_config(outbounds, TEMPLATE_FILE, CONFIG_FILE, BACKUP_FILE, excluded_ips)
        if changes_made:
            try:
                manage_service()
                if debug_level >= 1:
                    logging.info("Service restart completed.")
            except Exception as e:
                if os.environ.get("MOCK_MANAGE_SERVICE") == "1":
                    print("[Info] manage_service mock: ignoring error and exiting with code 0")
                    sys.exit(0)
                else:
                    raise
    except Exception as e:
        logging.error(f"Error during config update: {e}")
        sys.exit(1)

    logging.info("=== Update completed successfully ===")

def generate_config_after_exclusion(json_data, debug_level, dry_run):
    """Generate configuration after applying exclusions."""
    exclusions = load_exclusions(dry_run=dry_run)
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