"""Text formatting utilities for TUI application.

This module provides formatting functions for displaying
data in the TUI interface in a user-friendly way.
"""

from typing import Optional

from sboxmgr.subscription.models import ParsedServer


def format_server_info(server: ParsedServer) -> str:
    """Format server information for display.

    Args:
        server: Server to format

    Returns:
        Formatted server information string

    """
    # Get normalized tag using middleware logic
    tag = _get_normalized_tag(server)

    # Get basic info
    protocol = server.type.upper()
    address = f"{server.address}:{server.port}"

    # Get optional metadata
    country = server.meta.get("country", "Unknown")
    latency = server.meta.get("latency")
    ping = server.meta.get("ping")
    speed = server.meta.get("speed")

    # Build formatted string starting with tag
    info_parts = [f"[{protocol}] {tag}"]

    # Add country if available
    if country and country != "Unknown":
        info_parts.append(f"📍 {country}")

    # Add performance metrics
    if ping is not None:
        info_parts.append(f"⏱️ {ping}ms")
    elif latency is not None:
        info_parts.append(f"⏱️ {latency}ms")

    if speed is not None:
        info_parts.append(f"🚀 {speed}")

    # Add address info
    info_parts.append(f"🌐 {address}")

    return " | ".join(info_parts)


def _get_normalized_tag(server: ParsedServer) -> str:
    """Get normalized tag using middleware logic.

    Priority order:
    1. meta['name'] (human-readable from source)
    2. meta['label'] (alternative human-readable label)
    3. meta['tag'] (explicit tag from source)
    4. tag (parser-generated tag)
    5. address (IP/domain fallback)

    Args:
        server: Server to get tag for

    Returns:
        Normalized tag string

    """
    # Priority 1: meta['name'] (human-readable from source)
    if server.meta and server.meta.get("name"):
        name = server.meta["name"]
        if isinstance(name, str) and name.strip():
            return name.strip()

    # Priority 2: meta['label'] (alternative human-readable label)
    if server.meta and server.meta.get("label"):
        label = server.meta["label"]
        if isinstance(label, str) and label.strip():
            return label.strip()

    # Priority 3: meta['tag'] (explicit tag from source)
    if server.meta and server.meta.get("tag"):
        tag = server.meta["tag"]
        if isinstance(tag, str) and tag.strip():
            return tag.strip()

    # Priority 4: tag (parser-generated tag)
    if server.tag and server.tag.strip():
        return server.tag.strip()

    # Priority 5: address (IP/domain fallback)
    if server.address:
        return f"{server.type}-{server.address}"

    # Fallback
    return "unnamed-server"


def format_subscription_info(
    url: str, server_count: int = 0, tags: Optional[list[str]] = None
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
