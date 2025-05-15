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
from modules.server_management import list_servers, load_exclusions, apply_exclusions, exclude_servers, view_exclusions, clear_exclusions

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
    parser.add_argument("-u", "--url", help="URL for proxy configuration")
    parser.add_argument("-r", "--remarks", help="Select server by remarks")
    parser.add_argument("-i", "--index", type=int, default=None, help="Select server by index")
    parser.add_argument("-d", "--debug", type=int, choices=[0, 1, 2], default=0,
                        help="Set debug level: 0 for minimal, 1 for detailed, 2 for verbose")
    parser.add_argument("--proxy", help="Proxy URL (e.g., socks5://127.0.0.1:1080 or https://proxy.example.com)")
    parser.add_argument("-l", "--list-servers", action="store_true", help="List all servers with indices")
    parser.add_argument("-e", "--exclude", nargs='*', help="Exclude servers by index or name")
    parser.add_argument("--clear-exclusions", action="store_true", help="Clear all current exclusions")
    args = parser.parse_args()

    # Initialize logging
    setup_logging(args.debug, LOG_FILE, MAX_LOG_SIZE)
    logging.info("=== Starting sing-box configuration update ===")

    if args.list_servers or args.exclude is not None:
        if not args.url and args.exclude is not None and len(args.exclude) > 0:
            print("Error: URL is required for excluding servers.")
            return

    # Fetching configuration
    json_data = fetch_json(args.url, proxy_url=args.proxy) if args.url else None
    if args.debug >= 1 and json_data:
        logging.info(f"Fetched server list from: {args.url}")
    if args.debug >= 2 and json_data:
        logging.debug(f"Fetched configuration: {json.dumps(json_data, indent=2)}")

    # List servers if requested
    if args.list_servers:
        if json_data:
            list_servers(json_data, SUPPORTED_PROTOCOLS, args.debug)
        else:
            print("Error: URL is required to list servers.")
        return

    # Exclude servers if requested
    if args.exclude is not None:
        if len(args.exclude) == 0:
            view_exclusions(args.debug)
        else:
            if json_data:
                exclude_servers(json_data, args.exclude, SUPPORTED_PROTOCOLS, args.debug)
                generate_config_after_exclusion(json_data, args.debug)
            else:
                print("Error: URL is required to exclude servers.")
        return

    # Clear exclusions if requested
    if args.clear_exclusions:
        clear_exclusions()
        return

    # Load exclusions
    exclusions = load_exclusions()
    excluded_ids = {exclusion["id"] for exclusion in exclusions["exclusions"]}

    # Prepare outbounds based on selection
    if args.remarks or args.index is not None:
        if not json_data:
            print("Error: URL is required to select server by remarks or index.")
            return
        # Single server selection
        config = select_config(json_data, args.remarks, args.index if args.index is not None else 0)
        outbound = validate_protocol(config, SUPPORTED_PROTOCOLS)
        outbounds = [outbound]
        if args.debug >= 1:
            logging.info(f"Selected configuration by remarks: {args.remarks} or index: {args.index}")
        if args.debug >= 2:
            logging.debug(f"Selected configuration details: {json.dumps(config, indent=2)}")
    else:
        if not json_data:
            print("Error: URL is required for auto-selection.")
            return
        # Auto-selection: process all servers
        if isinstance(json_data, dict) and "outbounds" in json_data:
            configs = [
                outbound for outbound in json_data["outbounds"]
                if outbound.get("type") in SUPPORTED_PROTOCOLS
            ]
        else:
            configs = json_data

        # Apply exclusions
        configs = apply_exclusions(configs, excluded_ids, args.debug)

        outbounds = []
        for idx, config in enumerate(configs):
            try:
                outbound = validate_protocol(config, SUPPORTED_PROTOCOLS)
                # Use original tag if available, else generate proxy-a, proxy-b, etc.
                if not outbound["tag"].startswith("proxy-"):
                    outbounds.append(outbound)
                else:
                    outbound["tag"] = f"proxy-{chr(97 + idx)}"
                    outbounds.append(outbound)
            except ValueError as e:
                logging.warning(f"Skipping invalid configuration at index {idx}: {e}")

        if not outbounds:
            logging.warning("No valid configurations found for auto-selection, using direct")
            outbounds = []  # Empty outbounds will use direct via route.final
        if args.debug >= 1:
            logging.info(f"Prepared {len(outbounds)} servers for auto-selection")
            logging.debug(f"Outbounds for auto-selection: {json.dumps(outbounds, indent=2)}")

    # Generate configuration
    changes_made = generate_config(outbounds, TEMPLATE_FILE, CONFIG_FILE, BACKUP_FILE)

    if changes_made:
        # Manage service only if changes were made
        manage_service()
        if args.debug >= 1:
            logging.info("Service restart completed.")

    logging.info("=== Update completed successfully ===")

def generate_config_after_exclusion(json_data, debug_level):
    """Generate configuration after applying exclusions."""
    exclusions = load_exclusions()
    excluded_ids = {exclusion["id"] for exclusion in exclusions["exclusions"]}

    # Prepare outbounds based on selection
    if isinstance(json_data, dict) and "outbounds" in json_data:
        configs = [
            outbound for outbound in json_data["outbounds"]
            if outbound.get("type") in SUPPORTED_PROTOCOLS
        ]
    else:
        configs = json_data

    # Apply exclusions
    configs = apply_exclusions(configs, excluded_ids, debug_level)

    outbounds = []
    excluded_ips = []
    for idx, config in enumerate(configs):
        try:
            outbound = validate_protocol(config, SUPPORTED_PROTOCOLS)
            # Ensure each outbound has a unique tag
            if not outbound["tag"].startswith("proxy-"):
                outbounds.append(outbound)
            else:
                outbound["tag"] = f"proxy-{chr(97 + idx)}"
                outbounds.append(outbound)

            # Add server IP to exclusion list
            if "server" in outbound:
                excluded_ips.append(outbound["server"])
        except ValueError as e:
            logging.warning(f"Skipping invalid configuration at index {idx}: {e}")

    if not outbounds:
        logging.warning("No valid configurations found for auto-selection, using direct")
        outbounds = []  # Empty outbounds will use direct via route.final
    if debug_level >= 1:
        logging.info(f"Prepared {len(outbounds)} servers for auto-selection")
        logging.info(f"Excluded IPs: {excluded_ips}")

    # Pass excluded IPs to generate_config
    generate_config(outbounds, TEMPLATE_FILE, CONFIG_FILE, BACKUP_FILE, excluded_ips)

if __name__ == "__main__":
    main()
