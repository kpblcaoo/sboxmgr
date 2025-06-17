import requests
import json
from logging import error

def fetch_json(url, proxy_url=None):
    """Fetch JSON from URL with optional proxy."""
    try:
        proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None
        response = requests.get(url, headers={"User-Agent": "SFI"}, proxies=proxies, timeout=10)
        response.raise_for_status()
        json_data = response.json()
        if not json_data:
            error("Received empty JSON from URL")
            return None
        return json_data
    except requests.Timeout:
        error(f"Timeout fetching configuration from {url}")
        return None
    except requests.HTTPError as e:
        error(f"HTTP error fetching configuration from {url}: {e}")
        return None
    except requests.ConnectionError as e:
        error(f"Connection error fetching configuration from {url}: {e}")
        return None
    except json.JSONDecodeError as e:
        error(f"Invalid JSON received from {url}: {e}")
        return None
    except Exception as e:
        error(f"Unexpected error fetching configuration from {url}: {e}")
        return None

def select_config(json_data, remarks, index):
    """Select proxy configuration by remarks or index."""
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