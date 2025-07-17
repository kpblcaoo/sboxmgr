"""Input validation utilities for TUI application.

This module provides validation functions for user inputs
in the TUI interface, ensuring data integrity and user feedback.
"""

import os
from typing import Optional
from urllib.parse import urlparse


def validate_subscription_url(url: str) -> tuple[bool, Optional[str]]:
    """Validate subscription URL format.

    Args:
        url: URL to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not url:
        return False, "URL cannot be empty"

    if not url.strip():
        return False, "URL cannot be empty"

    try:
        parsed = urlparse(url.strip())
        if not parsed.scheme or not parsed.netloc:
            return False, "Invalid URL format"

        # Check for supported protocols
        supported_schemes = {
            "http",
            "https",  # HTTP subscriptions
            "vmess",
            "vless",
            "ss",
            "trojan",
            "tuic",
            "hysteria2",  # Direct server links
        }

        if parsed.scheme not in supported_schemes:
            return False, f"Unsupported protocol: {parsed.scheme}"

        return True, None

    except Exception as e:
        return False, f"Invalid URL format: {str(e)}"


def validate_output_path(path: str) -> tuple[bool, Optional[str]]:
    """Validate output file path.

    Args:
        path: File path to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not path:
        return False, "Output path cannot be empty"

    if not path.strip():
        return False, "Output path cannot be empty"

    try:
        # Resolve path
        resolved_path = os.path.expanduser(path.strip())

        # Check if directory exists and is writable
        dir_path = os.path.dirname(resolved_path) or "."

        if not os.path.exists(dir_path):
            return False, f"Directory does not exist: {dir_path}"

        if not os.access(dir_path, os.W_OK):
            return False, f"Directory is not writable: {dir_path}"

        # Check if file exists and is writable
        if os.path.exists(resolved_path):
            if not os.access(resolved_path, os.W_OK):
                return False, f"File is not writable: {resolved_path}"

        return True, None

    except Exception as e:
        return False, f"Invalid path: {str(e)}"


def validate_tags(tags_text: str) -> tuple[bool, Optional[str], list[str]]:
    """Validate and parse tags input.

    Args:
        tags_text: Comma-separated tags string

    Returns:
        Tuple of (is_valid, error_message, parsed_tags)
    """
    if not tags_text or not tags_text.strip():
        return True, None, []

    try:
        # Split by comma and clean up
        tags = [tag.strip() for tag in tags_text.split(",") if tag.strip()]

        # Validate individual tags
        for tag in tags:
            if len(tag) > 50:
                return False, f"Tag too long: {tag}", []

            if not tag.replace("-", "").replace("_", "").isalnum():
                return False, f"Invalid tag format: {tag}", []

        return True, None, tags

    except Exception as e:
        return False, f"Invalid tags format: {str(e)}", []
