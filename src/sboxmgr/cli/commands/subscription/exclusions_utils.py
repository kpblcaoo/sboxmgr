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


def validate_server_indices(
    indices: list[int], supported_servers: list, json_output: bool
) -> None:
    """Validate server indices against available servers.

    Args:
        indices: List of server indices to validate
        supported_servers: List of available servers
        json_output: Whether to output errors in JSON format

    Raises:
        typer.Exit: If validation fails

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


def ensure_server_cache(manager: ExclusionManager, json_output: bool) -> None:
    """Ensure server cache is available.

    Args:
        manager: Exclusion manager instance
        json_output: Whether to output errors in JSON format

    Raises:
        typer.Exit: If cache is not available

    """
    if not manager.has_servers_cache():
        error_msg = "Server cache not available"
        if json_output:
            print(json.dumps({"error": error_msg}))
        else:
            console.print(f"[red]❌ {error_msg}[/red]")
        raise typer.Exit(1) from None
