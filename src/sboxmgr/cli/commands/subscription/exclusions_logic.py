"""Logic functions for exclusions management.

This module contains the core logic for managing server exclusions,
separated from the CLI interface to maintain clean architecture.
"""

import json

import typer
from rich.console import Console

from sboxmgr.core.exclusions.manager import ExclusionManager

from .exclusions_utils import (
    parse_server_input,
    require_server_cache,
    validate_server_indices,
)

console = Console()


def _add_exclusions_by_indices(
    manager: ExclusionManager,
    indices: list[int],
    reason: str,
    json_output: bool,
) -> list[str]:
    """Add exclusions by server indices.

    Args:
        manager: Exclusion manager instance
        indices: List of server indices to exclude
        reason: Reason for exclusion
        json_output: Whether to output errors in JSON format

    Returns:
        List of added server IDs

    """
    error = require_server_cache(manager)
    if error:
        if json_output:
            print(json.dumps({"error": error}))
        else:
            console.print(f"[red]❌ {error}[/red]")
        raise typer.Exit(1) from None

    servers_data = manager._servers_cache["servers"]
    protocols = manager._servers_cache["supported_protocols"]
    supported_servers = manager._servers_cache["supported_servers"]

    validate_server_indices(indices, supported_servers, json_output)

    return manager.add_by_index(servers_data, indices, protocols, reason)


def _add_exclusions_by_patterns(
    manager: ExclusionManager,
    patterns: list[str],
    reason: str,
    json_output: bool,
) -> list[str]:
    """Add exclusions by wildcard patterns.

    Args:
        manager: Exclusion manager instance
        patterns: List of wildcard patterns to match
        reason: Reason for exclusion
        json_output: Whether to output errors in JSON format

    Returns:
        List of added server IDs

    """
    error = require_server_cache(manager)
    if error:
        if json_output:
            print(json.dumps({"error": error}))
        else:
            console.print(f"[red]❌ {error}[/red]")
        raise typer.Exit(1) from None

    servers_data = manager._servers_cache["servers"]
    protocols = manager._servers_cache["supported_protocols"]

    return manager.add_by_wildcard(servers_data, patterns, protocols, reason)


def _remove_exclusions_by_indices(
    manager: ExclusionManager,
    indices: list[int],
    json_output: bool,
) -> list[str]:
    """Remove exclusions by server indices.

    Args:
        manager: Exclusion manager instance
        indices: List of server indices to remove from exclusions
        json_output: Whether to output errors in JSON format

    Returns:
        List of removed server IDs

    """
    error = require_server_cache(manager)
    if error:
        if json_output:
            print(json.dumps({"error": error}))
        else:
            console.print(f"[red]❌ {error}[/red]")
        raise typer.Exit(1) from None

    servers_data = manager._servers_cache["servers"]
    protocols = manager._servers_cache["supported_protocols"]
    supported_servers = manager._servers_cache["supported_servers"]

    validate_server_indices(indices, supported_servers, json_output)

    return manager.remove_by_index(servers_data, indices, protocols)


def _remove_exclusions_by_ids(
    manager: ExclusionManager,
    server_ids: list[str],
) -> list[str]:
    """Remove exclusions by server IDs.

    Args:
        manager: Exclusion manager instance
        server_ids: List of server IDs to remove

    Returns:
        List of removed server IDs

    """
    removed_ids = []

    for server_id in server_ids:
        if manager.remove(server_id):
            removed_ids.append(server_id)

    return removed_ids


def exclusions_add_logic(
    manager: ExclusionManager,
    servers: str,
    reason: str,
    json_output: bool,
    verbose: bool = False,
) -> None:
    """Internal logic for adding exclusions.

    Args:
        manager (ExclusionManager): The exclusion manager instance to handle exclusions.
        servers (str): A comma-separated string of server indices or patterns to exclude.
        reason (str): The reason for excluding the servers.
        json_output (bool): Whether to output errors in JSON format.
        verbose (bool, optional): Whether to print verbose output. Defaults to False.

    Raises:
        typer.Exit: If an error occurs during the exclusion process.

    """
    if verbose:
        typer.echo("➕ Adding exclusions...")
        typer.echo(f"   Servers: {servers}")
        typer.echo(f"   Reason: {reason}")

    indices, patterns = parse_server_input(servers)
    added_ids = []

    # Add by indices
    if indices:
        added_by_index = _add_exclusions_by_indices(
            manager, indices, reason, json_output
        )
        added_ids.extend(added_by_index)

    # Add by wildcard patterns
    if patterns:
        added_by_pattern = _add_exclusions_by_patterns(
            manager, patterns, reason, json_output
        )
        added_ids.extend(added_by_pattern)

    if json_output:
        print(
            json.dumps(
                {
                    "action": "add",
                    "added_count": len(added_ids),
                    "added_ids": added_ids,
                    "reason": reason,
                }
            )
        )
    elif added_ids:
        console.print(f"[green]✅ Added {len(added_ids)} exclusions.[/green]")
    else:
        console.print(
            "[yellow]⚠️ No new exclusions added (already excluded or not found).[/yellow]"
        )


def exclusions_remove_logic(
    manager: ExclusionManager,
    servers: str,
    json_output: bool,
    verbose: bool = False,
) -> None:
    """Internal logic for removing exclusions."""
    if verbose:
        typer.echo("➖ Removing exclusions...")
        typer.echo(f"   Servers: {servers}")

    indices, server_ids = parse_server_input(servers)
    removed_ids = []

    # Remove by indices
    if indices:
        removed_by_index = _remove_exclusions_by_indices(manager, indices, json_output)
        removed_ids.extend(removed_by_index)

    # Remove by server IDs
    if server_ids:
        removed_by_id = _remove_exclusions_by_ids(manager, server_ids)
        removed_ids.extend(removed_by_id)

    if json_output:
        print(
            json.dumps(
                {
                    "action": "remove",
                    "removed_count": len(removed_ids),
                    "removed_ids": removed_ids,
                }
            )
        )
    elif removed_ids:
        console.print(f"[green]✅ Removed {len(removed_ids)} exclusions.[/green]")
    else:
        console.print("[yellow]⚠️ No exclusions removed (not found).[/yellow]")


def exclusions_list_logic(
    manager: ExclusionManager,
    json_output: bool,
) -> None:
    """Internal logic for listing exclusions."""
    from rich.table import Table

    exclusions = manager.list_all()

    if json_output:
        data = {"total": len(exclusions), "exclusions": exclusions}
        print(json.dumps(data, indent=2))
    else:
        if not exclusions:
            console.print("[dim]📝 No exclusions found.[/dim]")
            return

        table = Table(title=f"📝 Exclusions ({len(exclusions)})")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="white")
        table.add_column("Reason", style="blue")
        table.add_column("Timestamp", style="green")

        for exclusion in exclusions:
            table.add_row(
                exclusion.get("id", "N/A"),
                exclusion.get("name", "N/A"),
                exclusion.get("reason", "N/A"),
                exclusion.get("timestamp", "N/A"),
            )

        console.print(table)


def exclusions_clear_logic(
    manager: ExclusionManager,
    json_output: bool,
    global_yes: bool = False,
) -> None:
    """Internal logic for clearing exclusions."""
    from rich.prompt import Confirm

    from sboxmgr.i18n.t import t

    # Check if we have any exclusions
    exclusions = manager.list_all()
    if not exclusions:
        if json_output:
            print(
                json.dumps(
                    {
                        "action": "clear",
                        "removed_count": 0,
                        "message": "No exclusions to clear",
                    }
                )
            )
        else:
            console.print("[yellow]💡 No exclusions to clear[/yellow]")
        return

    # Confirmation
    if not global_yes and not Confirm.ask(
        f"[bold red]{t('cli.clear_exclusions.confirm')}[/bold red]"
    ):
        console.print(f"[yellow]{t('cli.operation_cancelled')}[/yellow]")
        return

    count = manager.clear()

    if json_output:
        print(json.dumps({"action": "clear", "removed_count": count}))
    else:
        console.print(
            f"[green]✅ {t('cli.clear_exclusions.success').format(count=count)}[/green]"
        )


def exclusions_list_servers_logic(
    manager: ExclusionManager,
    json_output: bool,
    show_excluded: bool = True,
) -> None:
    """Internal logic for listing servers with exclusion status."""
    from rich.table import Table

    from sboxmgr.utils.id import generate_server_id

    servers_info = manager.list_servers(show_excluded=show_excluded)

    if json_output:
        data = {
            "total": len(servers_info),
            "servers": [
                {
                    "index": idx,
                    "id": generate_server_id(server),
                    "tag": server.get("tag", "N/A"),
                    "type": server.get("type", "N/A"),
                    "server": server.get("server", "N/A"),
                    "server_port": server.get("server_port", "N/A"),
                    "is_excluded": is_excluded,
                }
                for idx, server, is_excluded in servers_info
            ],
        }
        print(json.dumps(data, indent=2))
        return

    if not servers_info:
        console.print("[dim]📡 No servers found.[/dim]")
        return

    table = Table(title=f"📡 Available Servers ({len(servers_info)})")
    table.add_column("Index", style="cyan", justify="right")
    table.add_column("Tag", style="white")
    table.add_column("Type", style="blue")
    table.add_column("Server:Port", style="green")
    table.add_column("Status", style="bold")

    for idx, server, is_excluded in servers_info:
        status = "🚫 EXCLUDED" if is_excluded else "✅ Available"
        status_style = "red" if is_excluded else "green"

        table.add_row(
            str(idx),
            server.get("tag", "N/A"),
            server.get("type", "N/A"),
            f"{server.get('server', 'N/A')}:{server.get('server_port', 'N/A')}",
            f"[{status_style}]{status}[/{status_style}]",
        )

    console.print(table)
