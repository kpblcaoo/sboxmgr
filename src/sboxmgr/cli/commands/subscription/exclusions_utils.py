"""Utility functions for exclusions management.

This module contains helper functions for parsing, validation,
and common operations used by exclusions logic.
"""

import json

import typer
from rich.console import Console

from sboxmgr.core.exclusions.manager import ExclusionManager

console = Console()


def parse_server_input(servers: str) -> tuple[list[int], list[str]]:
    """Parse server input string into indices and patterns.

    Args:
        servers: Comma-separated string of server indices or patterns

    Returns:
        Tuple of (indices, patterns)

    """
    items = [x.strip() for x in servers.split(",") if x.strip()]

    indices = []
    patterns = []

    for item in items:
        if item.isdigit():
            indices.append(int(item))
        else:
            patterns.append(item)

    return indices, patterns


def validate_subscription_url(url: str, json_output: bool) -> None:
    """Validate that subscription URL is provided.

    Args:
        url: Subscription URL to validate
        json_output: Whether to output errors in JSON format

    Raises:
        typer.Exit: If URL is not provided

    """
    if not url:
        error_msg = "Subscription URL is required (use -u/--url)"
        if json_output:
            print(json.dumps({"error": error_msg}))
        else:
            console.print(f"[red]❌ {error_msg}[/red]")
        raise typer.Exit(1) from None


def validate_server_indices(
    indices: list[int], supported_servers: list, json_output: bool
) -> list[str]:
    """Validate server indices against available servers.

    Args:
        indices: List of server indices to validate
        supported_servers: List of available servers
        json_output: Whether to output errors in JSON format

    Returns:
        List of validation errors (empty if all valid)

    """
    errors = []

    for index in indices:
        if index < 0 or index >= len(supported_servers):
            errors.append(
                f"Invalid server index: {index} (max: {len(supported_servers) - 1})"
            )

    if errors:
        if json_output:
            print(json.dumps({"error": "; ".join(errors)}))
        else:
            for error in errors:
                console.print(f"[red]❌ {error}[/red]")
        raise typer.Exit(1) from None

    return errors


def require_server_cache(manager: ExclusionManager) -> str | None:
    """Require server cache to be available.

    Args:
        manager: Exclusion manager instance

    Returns:
        Error message if cache is not available, None if available

    """
    if not manager.has_servers_cache():
        return "Server cache not available"
    return None
