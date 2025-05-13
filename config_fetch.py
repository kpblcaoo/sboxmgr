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

        response = requests.get(url, headers={"User-Agent": "ktor-client"}, proxies=proxies)
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
    if not json_data:
        raise ValueError("Received empty configuration")
    if remarks:
        for item in json_data:
            if item.get("remarks") == remarks:
                return item.get("outbounds", [{}])[0]
        raise ValueError(f"No configuration found with remarks: {remarks}")
    try:
        return json_data[index].get("outbounds", [{}])[0]
    except (IndexError, TypeError):
        raise ValueError(f"No configuration found at index: {index}")
