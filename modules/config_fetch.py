import requests
import json
from logging import error

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

    if remarks:
        for item in outbounds:
            if item.get("tag") == remarks:
                return item
        raise ValueError(f"No configuration found with remarks: {remarks}")

    try:
        return outbounds[index]
    except (IndexError, TypeError):
        raise ValueError(f"No configuration found at index: {index}")