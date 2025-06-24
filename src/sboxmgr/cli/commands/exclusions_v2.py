"""Improved exclusions CLI commands with better UX."""

import typer
import json
from typing import Optional
from rich.console import Console
from rich.table import Table

from rich.prompt import Confirm, Prompt
from rich import print as rprint

from sboxmgr.core.exclusions import ExclusionManager
from sboxmgr.config.fetch import fetch_json
from sboxmgr.utils.id import generate_server_id
from sboxmgr.i18n.t import t

# SUPPORTED_PROTOCOLS defined locally
SUPPORTED_PROTOCOLS = ["vless", "shadowsocks", "vmess", "trojan", "tuic", "hysteria2"]

console = Console()

def exclusions_v2(
    url: str = typer.Option(
        ..., "-u", "--url", help=t("cli.url.help"),
        envvar=["SBOXMGR_URL", "SINGBOX_URL", "TEST_URL"]
    ),
    add: Optional[str] = typer.Option(None, "--add", help="Add exclusions (indices, names, or wildcards)"),
    remove: Optional[str] = typer.Option(None, "--remove", help="Remove exclusions (indices or IDs)"),
    view: bool = typer.Option(False, "--view", help="View current exclusions"),
    clear: bool = typer.Option(False, "--clear", help="Clear all exclusions"),
    list_servers: bool = typer.Option(False, "--list-servers", help="List available servers with indices"),
    interactive: bool = typer.Option(False, "-i", "--interactive", help="Interactive server selection"),
    reason: str = typer.Option("CLI operation", "--reason", help="Reason for exclusion"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
    show_excluded: bool = typer.Option(True, "--show-excluded/--hide-excluded", help="Show excluded servers in list"),
    debug: int = typer.Option(0, "-d", "--debug", help=t("cli.debug.help")),
):
    """Enhanced exclusions management with improved user experience.
    
    Provides comprehensive server exclusion management for subscription-based
    proxy configurations. Supports multiple input methods including indices,
    server names, wildcard patterns, and interactive selection. Features
    rich console output, JSON export, and persistent exclusion storage.
    
    Supported operations:
    - Add exclusions by index, name, or wildcard pattern
    - Remove exclusions by index or server ID
    - View current exclusions with details
    - List all available servers with exclusion status
    - Interactive mode for convenient server selection
    - Clear all exclusions with confirmation
    
    Args:
        url: Subscription URL to fetch server list from.
        add: Comma-separated list of servers to exclude (indices, names, or wildcards).
        remove: Comma-separated list of exclusions to remove (indices or IDs).
        view: Display current exclusions without fetching subscription.
        clear: Remove all exclusions with interactive confirmation.
        list_servers: Display all servers with indices and exclusion status.
        interactive: Enter interactive mode for server selection.
        reason: Reason text to record with new exclusions.
        json_output: Output results in JSON format instead of rich console.
        show_excluded: Include excluded servers in server listings.
        debug: Debug verbosity level (0-2).
        
    Raises:
        typer.Exit: On subscription fetch failure, invalid server data, or user cancellation.
        
    Examples:
        sboxmgr exclusions-v2 -u URL --add "0,1,2" --reason "Slow servers"
        sboxmgr exclusions-v2 -u URL --add "server-*,*tokyo*" --reason "Geo filtering"
        sboxmgr exclusions-v2 --view --json
        sboxmgr exclusions-v2 -u URL --interactive
    """
    
    manager = ExclusionManager.default()
    
    # Handle view-only operations first (no URL needed)
    if view:
        _view_exclusions(manager, json_output)
        return
    
    if clear:
        _handle_clear_operation(manager, json_output)
        return
    
    # For operations requiring server data, fetch and cache it
    if any([add, remove, list_servers, interactive]):
        json_data = _fetch_and_validate_subscription(url, json_output)
        _cache_server_data(manager, json_data, json_output)
    
    # Handle operations that require server data
    if list_servers:
        _list_servers(manager, json_output, show_excluded)
        return
    
    if interactive:
        _interactive_exclusions(manager, json_output, reason)
        return
    
    if add:
        _add_exclusions(manager, add, reason, json_output)
    
    if remove:
        _remove_exclusions(manager, remove, json_output)
    
    # Show help if no action specified
    if not any([add, remove, view, clear, list_servers, interactive]):
        _show_usage_help()

def _handle_clear_operation(manager: ExclusionManager, json_output: bool) -> None:
    """Handle the clear exclusions operation with confirmation."""
    if not Confirm.ask("[bold red]Are you sure you want to clear ALL exclusions?[/bold red]"):
        rprint("[yellow]Operation cancelled.[/yellow]")
        return
    
    count = manager.clear()
    if json_output:
        print(json.dumps({"action": "clear", "removed_count": count}))
    else:
        rprint(f"[green]✅ Cleared {count} exclusions.[/green]")

def _fetch_and_validate_subscription(url: str, json_output: bool) -> dict:
    """Fetch and validate subscription data from URL.
    
    Args:
        url: Subscription URL to fetch from
        json_output: Whether to output errors in JSON format
        
    Returns:
        Parsed JSON data from subscription
        
    Raises:
        typer.Exit: If fetching or parsing fails
    """
    try:
        json_data = fetch_json(url)
        if json_data is None:
            error_msg = "Failed to fetch subscription data"
            if json_output:
                print(json.dumps({"error": error_msg, "url": url}))
            else:
                rprint(f"[red]❌ {error_msg} from:[/red]")
                rprint(f"[dim]   {url}[/dim]")
                rprint("[yellow]💡 Check URL and internet connection[/yellow]")
            raise typer.Exit(1)
        return json_data
    except Exception as e:
        if json_output:
            print(json.dumps({"error": str(e), "url": url}))
        else:
            rprint(f"[red]❌ {t('error.config_load_failed')}: {e}[/red]")
            rprint(f"[dim]URL: {url}[/dim]")
        raise typer.Exit(1)

def _cache_server_data(manager: ExclusionManager, json_data: dict, json_output: bool) -> None:
    """Cache server data in exclusion manager.
    
    Args:
        manager: ExclusionManager instance
        json_data: Server data to cache
        json_output: Whether to output errors in JSON format
        
    Raises:
        typer.Exit: If server data format is invalid
    """
    try:
        manager.set_servers_cache(json_data, SUPPORTED_PROTOCOLS)
    except Exception as e:
        error_msg = f"Invalid server data format: {e}"
        if json_output:
            print(json.dumps({"error": error_msg}))
        else:
            rprint(f"[red]❌ {error_msg}[/red]")
            rprint("[yellow]💡 The subscription might not be in the expected format[/yellow]")
        raise typer.Exit(1)

def _show_usage_help() -> None:
    """Display usage help when no action is specified."""
    rprint("[yellow]💡 Use --add, --remove, --view, --clear, --list-servers, or --interactive[/yellow]")
    rprint("[dim]Example: sboxmgr exclusions --url URL --add '0,1,server-*' --reason 'Testing'[/dim]")

def _view_exclusions(manager: ExclusionManager, json_output: bool) -> None:
    """Display current exclusions in table or JSON format.
    
    Args:
        manager: ExclusionManager instance for data access.
        json_output: If True, output JSON format; otherwise rich table format.
    """
    exclusions = manager.list_all()
    
    if json_output:
        data = {
            "total": len(exclusions),
            "exclusions": exclusions  # list_all() returns dict format
        }
        print(json.dumps(data, indent=2))
        return
    
    if not exclusions:
        rprint("[dim]📝 No exclusions found.[/dim]")
        return
    
    table = Table(title=f"🚫 Current Exclusions ({len(exclusions)})")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="white")
    table.add_column("Reason", style="yellow")
    table.add_column("Added", style="dim")
    
    for exc in exclusions:
        table.add_row(
            exc["id"][:12] + "...", 
            exc.get("name", "N/A"), 
            exc.get("reason", "N/A"), 
            exc.get("timestamp", "N/A")[:10]
        )
    
    console.print(table)

def _list_servers(manager: ExclusionManager, json_output: bool, show_excluded: bool) -> None:
    """Display server list with indices, status, and exclusion information.
    
    Args:
        manager: ExclusionManager instance with cached server data.
        json_output: If True, output JSON format; otherwise rich table format.
        show_excluded: Whether to include excluded servers in the listing.
    """
    servers_info = manager.list_servers(show_excluded=show_excluded)
    
    if json_output:
        data = {
            "total": len(servers_info),
            "servers": [
                {
                    "index": idx,
                    "id": manager._get_server_id(server),
                    "tag": server.get("tag", "N/A"),
                    "type": server.get("type", "N/A"),
                    "server": server.get("server", "N/A"),
                    "server_port": server.get("server_port", "N/A"),
                    "is_excluded": is_excluded
                }
                for idx, server, is_excluded in servers_info
            ]
        }
        print(json.dumps(data, indent=2))
        return
    
    if not servers_info:
        rprint("[dim]📡 No servers found.[/dim]")
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
            f"[{status_style}]{status}[/{status_style}]"
        )
    
    console.print(table)
    
    # Show summary
    excluded_count = sum(1 for _, _, is_excluded in servers_info if is_excluded)
    available_count = len(servers_info) - excluded_count
    rprint(f"\n[green]✅ Available: {available_count}[/green] | [red]🚫 Excluded: {excluded_count}[/red]")

def _interactive_exclusions(manager: ExclusionManager, json_output: bool, reason: str) -> None:
    """Interactive server selection for exclusions."""
    servers_info = manager.list_servers(show_excluded=True)
    
    if not servers_info:
        rprint("[red]❌ No servers found.[/red]")
        return
    
    # Show available servers
    _list_servers(manager, False, True)
    
    while True:
        rprint("\n[bold blue]🎯 Interactive Exclusion Manager[/bold blue]")
        rprint("[dim]Commands: add <indices>, remove <indices>, wildcard <pattern>, view, clear, quit[/dim]")
        
        command = Prompt.ask("Enter command", default="quit").strip().lower()
        
        if command in ["quit", "q", "exit"]:
            break
        elif command is "view":
            _view_exclusions(manager, False)
        elif command == "clear":
            if Confirm.ask("[red]Clear all exclusions?[/red]"):
                count = manager.clear()
                rprint(f"[green]✅ Cleared {count} exclusions.[/green]")
        elif command.startswith("add "):
            indices_str = command[4:].strip()
            _add_exclusions(manager, indices_str, reason, False)
        elif command.startswith("remove "):
            indices_str = command[7:].strip()
            _remove_exclusions(manager, indices_str, False)
        elif command.startswith("wildcard "):
            pattern = command[9:].strip()
            if not manager._servers_cache:
                rprint("[red]❌ Server cache not available[/red]")
                continue
            servers = manager._servers_cache['servers']
            protocols = manager._servers_cache['supported_protocols']
            added = manager.add_by_wildcard(servers, [pattern], protocols, reason)
            rprint(f"[green]✅ Added {len(added)} servers matching '{pattern}'.[/green]")
        else:
            rprint("[yellow]❓ Unknown command. Try: add 0,1,2 or remove 0,1 or wildcard server-* or quit[/yellow]")

def _add_exclusions(manager: ExclusionManager, add_str: str, reason: str, json_output: bool) -> None:
    """Add exclusions by indices, names, or wildcards."""
    items = [x.strip() for x in add_str.split(",") if x.strip()]
    
    indices = []
    patterns = []
    
    # Separate indices from patterns
    for item in items:
        if item.isdigit():
            indices.append(int(item))
        else:
            patterns.append(item)
    
    added_ids = []
    
    # Add by indices
    if indices:
        # Use cached servers data instead of re-caching
        if not manager._servers_cache:
            rprint("[red]❌ Server cache not available[/red]")
            return
        
        servers = manager._servers_cache['servers']
        protocols = manager._servers_cache['supported_protocols']
        added_by_index = manager.add_by_index(servers, indices, protocols, reason)
        added_ids.extend(added_by_index)
    
    # Add by wildcard patterns
    if patterns:
        # Use cached servers data instead of re-caching
        if not manager._servers_cache:
            rprint("[red]❌ Server cache not available[/red]")
            return
            
        servers = manager._servers_cache['servers']
        protocols = manager._servers_cache['supported_protocols']
        added_by_pattern = manager.add_by_wildcard(servers, patterns, protocols, reason)
        added_ids.extend(added_by_pattern)
    
    if json_output:
        print(json.dumps({
            "action": "add",
            "added_count": len(added_ids),
            "added_ids": added_ids,
            "reason": reason
        }))
    else:
        if added_ids:
            rprint(f"[green]✅ Added {len(added_ids)} exclusions.[/green]")
        else:
            rprint("[yellow]⚠️ No new exclusions added (already excluded or not found).[/yellow]")

def _remove_exclusions(manager: ExclusionManager, remove_str: str, json_output: bool) -> None:
    """Remove exclusions by indices or IDs."""
    items = [x.strip() for x in remove_str.split(",") if x.strip()]
    
    indices = []
    server_ids = []
    
    # Separate indices from server IDs
    for item in items:
        if item.isdigit():
            indices.append(int(item))
        else:
            server_ids.append(item)
    
    removed_ids = []
    
    # Remove by indices
    if indices:
        # Use cached servers data instead of re-caching
        if not manager._servers_cache:
            rprint("[red]❌ Server cache not available[/red]")
            return
            
        servers = manager._servers_cache['servers']
        protocols = manager._servers_cache['supported_protocols']
        removed_by_index = manager.remove_by_index(servers, indices, protocols)
        removed_ids.extend(removed_by_index)
    
    # Remove by server IDs
    for server_id in server_ids:
        if manager.remove(server_id):
            removed_ids.append(server_id)
    
    if json_output:
        print(json.dumps({
            "action": "remove",
            "removed_count": len(removed_ids),
            "removed_ids": removed_ids
        }))
    else:
        if removed_ids:
            rprint(f"[green]✅ Removed {len(removed_ids)} exclusions.[/green]")
        else:
            rprint("[yellow]⚠️ No exclusions removed (not found or not excluded).[/yellow]")

# Helper method for getting server ID (should be added to manager)
def _get_server_id(server: dict) -> str:
    """Get server ID - temporary helper until added to manager."""
    return generate_server_id(server)

# Monkey patch for now
ExclusionManager._get_server_id = lambda self, server: _get_server_id(server) 