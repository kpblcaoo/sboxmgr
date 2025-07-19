"""Subscription exclusions command module.

This module provides the 'subscription exclusions' command group for managing
server exclusions with subcommands for list, add, remove, and clear operations.
"""

import json
from typing import Optional

import typer
from rich.console import Console
from rich.prompt import Confirm
from rich.table import Table

from sboxmgr.config.fetch import fetch_json
from sboxmgr.constants import SUPPORTED_PROTOCOLS
from sboxmgr.core.exclusions import ExclusionManager
from sboxmgr.i18n.t import t
from sboxmgr.utils.id import generate_server_id

console = Console()

# Create the exclusions command app
app = typer.Typer(
    help=t("cli.subscription.exclusions.help"),
    name="exclusions",
    add_completion=False,
)


@app.callback()
def exclusions_callback(
    url: str = typer.Option(
        None,
        "-u",
        "--url",
        help=t("cli.url.help"),
        envvar=["SBOXMGR_URL", "SINGBOX_URL", "TEST_URL"],
    ),
    debug: int = typer.Option(0, "-d", "--debug", help=t("cli.debug.help")),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompts"),
    ctx: typer.Context = None,
):
    """Common options for exclusions commands.

    These options are available to all exclusions subcommands.
    """
    if ctx is not None:
        # Store common options in context for subcommands to access
        if ctx.obj is None:
            ctx.obj = {}
        ctx.obj["exclusions_url"] = url
        ctx.obj["exclusions_debug"] = debug
        ctx.obj["exclusions_yes"] = yes


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
            error_msg = t("error.subscription_fetch_failed")
            if json_output:
                print(json.dumps({"error": error_msg, "url": url}))
            else:
                console.print(f"[red]❌ {error_msg}:[/red]")
                console.print(f"[dim]   {url}[/dim]")
                console.print(f"[yellow]💡 {t('cli.check_url_connection')}[/yellow]")
            raise typer.Exit(1) from None
        return json_data
    except Exception as e:
        if json_output:
            print(json.dumps({"error": str(e), "url": url}))
        else:
            console.print(f"[red]❌ {t('error.config_load_failed')}: {e}[/red]")
            console.print(f"[dim]URL: {url}[/dim]")
        raise typer.Exit(1) from None


def _cache_server_data(
    manager: ExclusionManager, json_data: dict, json_output: bool
) -> None:
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
    except Exception:
        error_msg = t("error.invalid_server_format")
        if json_output:
            print(json.dumps({"error": error_msg}))
        else:
            console.print(f"[red]❌ {error_msg}[/red]")
            console.print(f"[yellow]💡 {t('cli.subscription_format_hint')}[/yellow]")
        raise typer.Exit(1) from None


def _show_usage_help() -> None:
    """Display usage help when no action is specified."""
    console.print(f"[yellow]💡 {t('cli.exclusions.usage_hint')}[/yellow]")
    console.print(f"[dim]{t('cli.exclusions.usage_example')}[/dim]")


@app.command("list")
def exclusions_list(
    json_output: bool = typer.Option(False, "--json", help=t("cli.json.help")),
    ctx: typer.Context = None,
):
    """List current exclusions.

    Shows all currently excluded servers with their details.
    """
    # Get global flags from context
    verbose = ctx.obj.get("verbose", False) if ctx is not None and ctx.obj else False

    if verbose:
        typer.echo("📋 Listing exclusions...")

    manager = ExclusionManager.default()
    _exclusions_list_logic(manager, json_output)


def _exclusions_add_logic(
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

    # EXACT COPY from old _add_exclusions function
    items = [x.strip() for x in servers.split(",") if x.strip()]

    indices = []
    patterns = []

    # Separate indices from patterns
    for item in items:
        if item.isdigit():
            indices.append(int(item))
        else:
            patterns.append(item)

    added_ids = []
    errors = []

    # Add by indices
    if indices:
        # Use cached servers data instead of re-caching
        if not manager.has_servers_cache():
            error_msg = "Server cache not available"
            if json_output:
                print(json.dumps({"error": error_msg}))
            else:
                console.print(f"[red]❌ {error_msg}[/red]")
            raise typer.Exit(1) from None

        servers_data = manager._servers_cache["servers"]
        protocols = manager._servers_cache["supported_protocols"]
        supported_servers = manager._servers_cache["supported_servers"]

        # Check for invalid indices before adding
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

        added_by_index = manager.add_by_index(servers_data, indices, protocols, reason)
        added_ids.extend(added_by_index)

    # Add by wildcard patterns
    if patterns:
        # Use cached servers data instead of re-caching
        if not manager.has_servers_cache():
            error_msg = "Server cache not available"
            if json_output:
                print(json.dumps({"error": error_msg}))
            else:
                console.print(f"[red]❌ {error_msg}[/red]")
            raise typer.Exit(1) from None

        servers_data = manager._servers_cache["servers"]
        protocols = manager._servers_cache["supported_protocols"]
        added_by_pattern = manager.add_by_wildcard(
            servers_data, patterns, protocols, reason
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


def _exclusions_remove_logic(
    manager: ExclusionManager,
    servers: str,
    json_output: bool,
    verbose: bool = False,
) -> None:
    """Internal logic for removing exclusions."""
    if verbose:
        typer.echo("➖ Removing exclusions...")
        typer.echo(f"   Servers: {servers}")

    # EXACT COPY from old _remove_exclusions function
    items = [x.strip() for x in servers.split(",") if x.strip()]

    indices = []
    server_ids = []

    # Separate indices from server IDs
    for item in items:
        if item.isdigit():
            indices.append(int(item))
        else:
            server_ids.append(item)

    removed_ids = []
    errors = []

    # Remove by indices
    if indices:
        # Use cached servers data instead of re-caching
        if not manager.has_servers_cache():
            error_msg = "Server cache not available"
            if json_output:
                print(json.dumps({"error": error_msg}))
            else:
                console.print(f"[red]❌ {error_msg}[/red]")
            raise typer.Exit(1) from None

        servers_data = manager._servers_cache["servers"]
        protocols = manager._servers_cache["supported_protocols"]
        supported_servers = manager._servers_cache["supported_servers"]

        # Check for invalid indices before removing
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

        removed_by_index = manager.remove_by_index(servers_data, indices, protocols)
        removed_ids.extend(removed_by_index)

    # Remove by server IDs
    for server_id in server_ids:
        if manager.remove(server_id):
            removed_ids.append(server_id)

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


def _exclusions_list_logic(
    manager: ExclusionManager,
    json_output: bool,
) -> None:
    """Internal logic for listing exclusions."""
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


def _exclusions_clear_logic(
    manager: ExclusionManager,
    json_output: bool,
    global_yes: bool = False,
) -> None:
    """Internal logic for clearing exclusions."""
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


@app.command("add")
def exclusions_add(
    servers: str = typer.Option(
        ..., "--servers", help="Server indices or names to exclude"
    ),
    reason: str = typer.Option("CLI operation", "--reason", help=t("cli.reason.help")),
    json_output: bool = typer.Option(False, "--json", help=t("cli.json.help")),
    ctx: typer.Context = None,
):
    """Add servers to exclusions.

    Exclude servers by index or wildcard pattern.

    Examples:
    - sboxctl subscription exclusions add --servers 0,1,2 --reason "slow servers"
    - sboxctl subscription exclusions add --servers "US*" --reason "US servers"

    """
    # Get common options from context
    url = ctx.obj.get("exclusions_url") if ctx is not None and ctx.obj else None
    verbose = ctx.obj.get("verbose", False) if ctx is not None and ctx.obj else False

    # Validate URL
    if not url:
        typer.echo("❌ Error: Subscription URL is required (use -u/--url)", err=True)
        raise typer.Exit(1)

    manager = ExclusionManager.default()

    # Fetch and cache server data
    json_data = _fetch_and_validate_subscription(url, json_output)
    _cache_server_data(manager, json_data, json_output)

    _exclusions_add_logic(manager, servers, reason, json_output, verbose)


@app.command("remove")
def exclusions_remove(
    servers: str = typer.Option(
        ..., "--servers", help="Server indices or names to remove from exclusions"
    ),
    json_output: bool = typer.Option(False, "--json", help=t("cli.json.help")),
    ctx: typer.Context = None,
):
    """Remove servers from exclusions.

    Remove servers from exclusions by index or server ID.

    Examples:
    - sboxctl subscription exclusions remove --servers 0,1,2
    - sboxctl subscription exclusions remove --servers "server-id-123"

    """
    # Get common options from context
    url = ctx.obj.get("exclusions_url") if ctx is not None and ctx.obj else None
    verbose = ctx.obj.get("verbose", False) if ctx is not None and ctx.obj else False

    # Validate URL
    if not url:
        typer.echo("❌ Error: Subscription URL is required (use -u/--url)", err=True)
        raise typer.Exit(1)

    if verbose:
        typer.echo("➖ Removing exclusions...")
        typer.echo(f"   Servers: {servers}")

    manager = ExclusionManager.default()

    # Fetch and cache server data
    json_data = _fetch_and_validate_subscription(url, json_output)
    _cache_server_data(manager, json_data, json_output)

    # Use the shared logic function
    _exclusions_remove_logic(manager, servers, json_output, verbose)


@app.command("list-servers")
def exclusions_list_servers(
    json_output: bool = typer.Option(False, "--json", help=t("cli.json.help")),
    show_excluded: bool = typer.Option(
        True, "--show-excluded/--hide-excluded", help=t("cli.show_excluded.help")
    ),
    ctx: typer.Context = None,
):
    """List all available servers with their exclusion status.

    Shows all servers from the subscription with their current exclusion status.
    Use --hide-excluded to show only available servers.
    """
    # Get common options from context
    url = ctx.obj.get("exclusions_url") if ctx is not None and ctx.obj else None
    verbose = ctx.obj.get("verbose", False) if ctx is not None and ctx.obj else False

    # Validate URL
    if not url:
        typer.echo("❌ Error: Subscription URL is required (use -u/--url)", err=True)
        raise typer.Exit(1)

    if verbose:
        typer.echo("📡 Listing servers...")
        typer.echo(f"   URL: {url}")
        typer.echo(f"   Show excluded: {show_excluded}")

    manager = ExclusionManager.default()

    # Fetch and cache server data
    json_data = _fetch_and_validate_subscription(url, json_output)
    _cache_server_data(manager, json_data, json_output)

    # List servers with exclusion status
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


@app.command("clear")
def exclusions_clear(
    json_output: bool = typer.Option(False, "--json", help=t("cli.json.help")),
    ctx: typer.Context = None,
):
    """Clear all exclusions.

    Removes all server exclusions. Requires confirmation unless --yes is used.
    """
    # Get global flags from context
    verbose = ctx.obj.get("verbose", False) if ctx is not None and ctx.obj else False
    global_yes = ctx.obj.get("yes", False) if ctx is not None and ctx.obj else False

    if verbose:
        typer.echo("🗑️ Clearing all exclusions...")

    manager = ExclusionManager.default()
    _exclusions_clear_logic(manager, json_output, global_yes)


@app.command(hidden=True)
def exclusions_main(
    url: str = typer.Option(
        ...,
        "-u",
        "--url",
        help=t("cli.url.help"),
        envvar=["SBOXMGR_URL", "SINGBOX_URL", "TEST_URL"],
    ),
    add: Optional[str] = typer.Option(None, "--add", help=t("cli.add.help")),
    remove: Optional[str] = typer.Option(None, "--remove", help=t("cli.remove.help")),
    view: bool = typer.Option(False, "--view", help=t("cli.view.help")),
    clear: bool = typer.Option(False, "--clear", help=t("cli.clear_exclusions.help")),
    list_servers: bool = typer.Option(
        False, "--list-servers", help=t("cli.list_servers.help")
    ),
    interactive: bool = typer.Option(
        False, "-i", "--interactive", help=t("cli.interactive.help")
    ),
    reason: str = typer.Option("CLI operation", "--reason", help=t("cli.reason.help")),
    json_output: bool = typer.Option(False, "--json", help=t("cli.json.help")),
    show_excluded: bool = typer.Option(
        True, "--show-excluded/--hide-excluded", help=t("cli.show_excluded.help")
    ),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompts"),
    debug: int = typer.Option(0, "-d", "--debug", help=t("cli.debug.help")),
    ctx: typer.Context = None,
):
    """Manage server exclusions for subscription-based proxy configurations.

    Supports adding, removing, viewing exclusions with interactive selection,
    wildcard patterns, and JSON export capabilities.

    ⚠️  DEPRECATED: This command is deprecated and will be removed in a future version.
    Use individual subcommands instead:
    - sboxctl subscription exclusions list
    - sboxctl subscription exclusions add --servers 0,1,2
    - sboxctl subscription exclusions remove --servers 0,1,2
    - sboxctl subscription exclusions clear
    - sboxctl subscription exclusions list-servers
    """
    # Show deprecation warning
    typer.secho(
        "⚠️  'exclusions-main' is deprecated and will be removed in a future version.",
        fg="yellow",
        err=True,
    )
    typer.secho(
        "💡 Use individual subcommands instead: list, add, remove, clear, list-servers",
        fg="blue",
        err=True,
    )

    # Get global flags from context
    global_yes = ctx.obj.get("yes", False) if ctx is not None and ctx.obj else False
    verbose = ctx.obj.get("verbose", False) if ctx is not None and ctx.obj else False

    # Combine local and global yes flags
    final_yes = yes or global_yes

    if verbose:
        typer.echo("🔧 Managing exclusions...")
        if url:
            typer.echo(f"   URL: {url}")
        # Track action parameters only when verbose is enabled
        actions = {
            "add": add,
            "remove": remove,
            "view": view,
            "clear": clear,
            "list_servers": list_servers,
            "interactive": interactive,
        }
        active_actions = [action for action, enabled in actions.items() if enabled]
        typer.echo(f"   Actions: {', '.join(active_actions)}")
        typer.echo(f"   Skip confirmations: {final_yes}")

    # Validate conflicting options
    if add and remove:
        typer.echo("❌ Error: --add and --remove are mutually exclusive", err=True)
        raise typer.Exit(1)

    if view and add:
        typer.echo("⚠️  Warning: --view takes precedence over --add", err=True)

    manager = ExclusionManager.default()

    # Handle view-only operations first (no URL needed)
    if view:
        _exclusions_list_logic(manager, json_output)
        return

    if clear:
        _exclusions_clear_logic(manager, json_output, final_yes)
        return

    # For operations requiring server data, fetch and cache it
    if any([add, remove, list_servers, interactive]):
        json_data = _fetch_and_validate_subscription(url, json_output)
        _cache_server_data(manager, json_data, json_output)

        # Handle operations that require server data
        if list_servers:
            # EXACT COPY from old _list_servers function
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
            return

    if interactive:
        # NOTE: Interactive mode is intentionally disabled.
        # Use explicit sub-commands (list/add/remove) instead.
        typer.echo("❌ Interactive mode is not available in subscription exclusions.")
        typer.echo("💡 Use individual commands instead:")
        typer.echo("   sboxctl subscription exclusions list")
        typer.echo("   sboxctl subscription exclusions add --servers 0,1,2")
        typer.echo("   sboxctl subscription exclusions remove --servers 0,1,2")
        typer.echo("   sboxctl subscription exclusions clear")
        raise typer.Exit(1)

    if add:
        _exclusions_add_logic(manager, add, reason, json_output, verbose)

    if remove:
        _exclusions_remove_logic(manager, remove, json_output, verbose)

    # Show help if no action specified
    if not any([add, remove, view, clear, list_servers, interactive]):
        _show_usage_help()


__all__ = ["app"]
