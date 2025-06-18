import requests
import json
from logging import error
from singbox.server.exclusions import load_exclusions
from singbox.utils.id import generate_server_id

def fetch_json(url, proxy_url=None):
    """Fetch JSON from URL with optional proxy."""
    try:
        proxies = {
            "http": proxy_url,
            "https": proxy_url,
        } if proxy_url else None

        response = requests.get(url, headers={"User-Agent": "SFI"}, proxies=proxies)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        error(f"Failed to fetch configuration from {url}: {e}")
        raise
    except json.JSONDecodeError:
        error("Received invalid JSON from URL")
        raise

def select_config(json_data, remarks, index):
    """Select proxy configuration by remarks or index."""
    # If json_data is a full sing-box config, extract outbounds
    if isinstance(json_data, dict) and "outbounds" in json_data:
        outbounds = [
            outbound for outbound in json_data["outbounds"]
            if outbound.get("type") in {"vless", "shadowsocks", "vmess", "trojan", "tuic", "hysteria2"}
        ]
    else:
        outbounds = json_data

    if not outbounds:
        raise ValueError("Received empty configuration")

    exclusions = load_exclusions()
    excluded_ids = {ex["id"] for ex in exclusions["exclusions"]}

    if remarks:
        for item in outbounds:
            if item.get("tag") == remarks:
                if generate_server_id(item) in excluded_ids:
                    raise ValueError(f"Сервер с remarks '{remarks}' находится в списке исключённых (excluded). Выберите другой.")
                return item
        raise ValueError(f"No configuration found with remarks: {remarks}")

    try:
        selected = outbounds[index]
        if generate_server_id(selected) in excluded_ids:
            raise ValueError(f"Сервер с индексом {index} находится в списке исключённых (excluded). Выберите другой.")
        return selected
    except (IndexError, TypeError):
        raise ValueError(f"No configuration found at index: {index}")