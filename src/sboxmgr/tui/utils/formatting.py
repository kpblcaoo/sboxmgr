"""Text formatting utilities for TUI application.

This module provides formatting functions for displaying
data in the TUI interface in a user-friendly way.
"""

from typing import List, Optional

from sboxmgr.subscription.models import ParsedServer


def format_server_info(server: ParsedServer) -> str:
    """Format server information for display.

    Args:
        server: Server to format

    Returns:
        Formatted server information string
    """
    # Get basic info
    name = server.name or f"{server.type}-{server.address}"
    protocol = server.type.upper()
    address = f"{server.address}:{server.port}"

    # Get optional metadata
    country = server.meta.get("country", "Unknown")
    latency = server.meta.get("latency")
    tags = server.meta.get("tags", [])

    # Build formatted string
    info_parts = [f"[{protocol}] {name}"]

    if country != "Unknown":
        info_parts.append(f"📍 {country}")

    if latency is not None:
        info_parts.append(f"⏱️ {latency}ms")

    if tags:
        info_parts.append(f"🏷️ {', '.join(tags)}")

    return f"{address} - {' | '.join(info_parts)}"


def format_subscription_info(
    url: str, server_count: int = 0, tags: Optional[List[str]] = None
) -> str:
    """Format subscription information for display.

    Args:
        url: Subscription URL
        server_count: Number of servers in subscription
        tags: Optional list of tags

    Returns:
        Formatted subscription information string
    """
    # Truncate URL if too long
    display_url = url
    if len(url) > 50:
        display_url = url[:47] + "..."

    info_parts = [display_url]

    if server_count > 0:
        info_parts.append(f"📊 {server_count} servers")

    if tags:
        info_parts.append(f"🏷️ {', '.join(tags)}")

    return " | ".join(info_parts)


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted size string
    """
    if size_bytes == 0:
        return "0 B"

    units = ["B", "KB", "MB", "GB"]
    unit_index = 0
    size = float(size_bytes)

    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1

    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"
    else:
        return f"{size:.1f} {units[unit_index]}"


def format_duration(seconds: float) -> str:
    """Format duration in human-readable format.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string
    """
    if seconds < 1:
        return f"{int(seconds * 1000)}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        remaining_seconds = int(seconds % 60)
        return f"{minutes}m {remaining_seconds}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def truncate_text(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """Truncate text to maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text

    return text[: max_length - len(suffix)] + suffix
