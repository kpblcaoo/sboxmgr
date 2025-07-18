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
from sboxmgr.core.exclusions import ExclusionManager
from sboxmgr.i18n.t import t
from sboxmgr.utils.id import generate_server_id

# SUPPORTED_PROTOCOLS defined locally
SUPPORTED_PROTOCOLS = ["vless", "shadowsocks", "vmess", "trojan", "tuic", "hysteria2"]

console = Console()
rprint = console.print

# Create the exclusions command app
app = typer.Typer(
    help=t("cli.subscription.exclusions.help"),
    name="exclusions",
    add_completion=False,
)


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
                rprint(f"[red]❌ {error_msg}:[/red]")
                rprint(f"[dim]   {url}[/dim]")
                rprint(f"[yellow]💡 {t('cli.check_url_connection')}[/yellow]")
            raise typer.Exit(1) from None
        return json_data
    except Exception as e:
        if json_output:
            print(json.dumps({"error": str(e), "url": url}))
        else:
            rprint(f"[red]❌ {t('error.config_load_failed')}: {e}[/red]")
            rprint(f"[dim]URL: {url}[/dim]")
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
            rprint(f"[red]❌ {error_msg}[/red]")
            rprint(f"[yellow]💡 {t('cli.subscription_format_hint')}[/yellow]")
        raise typer.Exit(1) from None


def _show_usage_help() -> None:
    """Display usage help when no action is specified."""
    rprint(f"[yellow]💡 {t('cli.exclusions.usage_hint')}[/yellow]")
    rprint(f"[dim]{t('cli.exclusions.usage_example')}[/dim]")


@app.command("list")
def exclusions_list(
    json_output: bool = typer.Option(False, "--json", help=t("cli.json.help")),
    ctx: typer.Context = None,
):
    """List current exclusions."""
    # Get global flags from context
    verbose = ctx.obj.get("verbose", False) if ctx is not None and ctx.obj else False

    if verbose:
        typer.echo("📋 Listing exclusions...")

    manager = ExclusionManager.default()
    exclusions = manager.list_all()

    if json_output:
        data = {
            "total": len(exclusions),
            "exclusions": exclusions,
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
            exc.get("timestamp", "N/A")[:10] if exc.get("timestamp") else "N/A",
        )

    console.print(table)


@app.command("add")
def exclusions_add(
    servers: str = typer.Option(
        ..., "--servers", help="Server indices or names to exclude"
    ),
    reason: str = typer.Option("CLI operation", "--reason", help=t("cli.reason.help")),
    url: str = typer.Option(
        ...,
        "-u",
        "--url",
        help=t("cli.url.help"),
        envvar=["SBOXMGR_URL", "SINGBOX_URL", "TEST_URL"],
    ),
    json_output: bool = typer.Option(False, "--json", help=t("cli.json.help")),
    ctx: typer.Context = None,
):
    """Add servers to exclusions."""
    # Get global flags from context
    verbose = ctx.obj.get("verbose", False) if ctx is not None and ctx.obj else False

    if verbose:
        typer.echo("➕ Adding exclusions...")
        typer.echo(f"   Servers: {servers}")
        typer.echo(f"   Reason: {reason}")

    manager = ExclusionManager.default()

    # Fetch and cache server data
    json_data = _fetch_and_validate_subscription(url, json_output)
    _cache_server_data(manager, json_data, json_output)

    # Parse server list
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
        try:
            added_ids.extend(
                manager.add_by_index(json_data, indices, SUPPORTED_PROTOCOLS, reason)
            )
        except Exception as e:
            errors.append(f"Failed to add by indices: {e}")

    # Add by wildcards
    if patterns:
        try:
            added_ids.extend(
                manager.add_by_wildcard(
                    json_data, patterns, SUPPORTED_PROTOCOLS, reason
                )
            )
        except Exception as e:
            errors.append(f"Failed to add by patterns: {e}")

    if json_output:
        result = {
            "action": "add",
            "added_count": len(added_ids),
            "added_ids": added_ids,
            "total_requested": len(items),
        }
        if errors:
            result["errors"] = errors
        print(json.dumps(result, indent=2))
    else:
        if added_ids:
            rprint(f"[green]✅ Added {len(added_ids)} servers to exclusions[/green]")
        if errors:
            for error in errors:
                rprint(f"[red]❌ {error}[/red]")


@app.command("remove")
def exclusions_remove(
    servers: str = typer.Option(
        ..., "--servers", help="Server indices or names to remove from exclusions"
    ),
    url: str = typer.Option(
        ...,
        "-u",
        "--url",
        help=t("cli.url.help"),
        envvar=["SBOXMGR_URL", "SINGBOX_URL", "TEST_URL"],
    ),
    json_output: bool = typer.Option(False, "--json", help=t("cli.json.help")),
    ctx: typer.Context = None,
):
    """Remove servers from exclusions."""
    # Get global flags from context
    verbose = ctx.obj.get("verbose", False) if ctx is not None and ctx.obj else False

    if verbose:
        typer.echo("➖ Removing exclusions...")
        typer.echo(f"   Servers: {servers}")

    manager = ExclusionManager.default()

    # Fetch and cache server data
    json_data = _fetch_and_validate_subscription(url, json_output)
    _cache_server_data(manager, json_data, json_output)

    # Parse server list
    items = [x.strip() for x in servers.split(",") if x.strip()]

    indices = []
    patterns = []

    # Separate indices from patterns
    for item in items:
        if item.isdigit():
            indices.append(int(item))
        else:
            patterns.append(item)

    removed_ids = []
    errors = []

    # Remove by indices
    if indices:
        try:
            removed_ids.extend(
                manager.remove_by_index(json_data, indices, SUPPORTED_PROTOCOLS)
            )
        except Exception as e:
            errors.append(f"Failed to remove by indices: {e}")

    # Remove by patterns (convert to server IDs)
    if patterns:
        try:
            # Get all servers and filter by patterns
            all_servers = manager.list_servers(json_data, SUPPORTED_PROTOCOLS)
            for pattern in patterns:
                for _index, server, is_excluded in all_servers:
                    if is_excluded and any(
                        pattern.lower() in str(server.get("tag", "")).lower()
                        or pattern.lower() in str(server.get("server", "")).lower()
                    ):
                        server_id = generate_server_id(server)
                        if manager.remove(server_id):
                            removed_ids.append(server_id)
        except Exception as e:
            errors.append(f"Failed to remove by patterns: {e}")

    if json_output:
        result = {
            "action": "remove",
            "removed_count": len(removed_ids),
            "removed_ids": removed_ids,
            "total_requested": len(items),
        }
        if errors:
            result["errors"] = errors
        print(json.dumps(result, indent=2))
    else:
        if removed_ids:
            rprint(
                f"[green]✅ Removed {len(removed_ids)} servers from exclusions[/green]"
            )
        if errors:
            for error in errors:
                rprint(f"[red]❌ {error}[/red]")


@app.command("clear")
def exclusions_clear(
    json_output: bool = typer.Option(False, "--json", help=t("cli.json.help")),
    ctx: typer.Context = None,
):
    """Clear all exclusions."""
    # Get global flags from context
    verbose = ctx.obj.get("verbose", False) if ctx is not None and ctx.obj else False
    global_yes = ctx.obj.get("yes", False) if ctx is not None and ctx.obj else False

    if verbose:
        typer.echo("🗑️ Clearing all exclusions...")

    manager = ExclusionManager.default()

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
            rprint("[yellow]💡 No exclusions to clear[/yellow]")
        return

    # Confirmation
    if not global_yes and not Confirm.ask(
        f"[bold red]{t('cli.clear_exclusions.confirm')}[/bold red]"
    ):
        rprint(f"[yellow]{t('cli.operation_cancelled')}[/yellow]")
        return

    count = manager.clear()

    if json_output:
        print(json.dumps({"action": "clear", "removed_count": count}))
    else:
        rprint(
            f"[green]✅ {t('cli.clear_exclusions.success').format(count=count)}[/green]"
        )


@app.command()
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
    """
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
        exclusions_list(json_output=json_output, ctx=ctx)
        return

    if clear:
        exclusions_clear(json_output=json_output, ctx=ctx)
        return

    # For operations requiring server data, fetch and cache it
    if any([add, remove, list_servers, interactive]):
        json_data = _fetch_and_validate_subscription(url, json_output)
        _cache_server_data(manager, json_data, json_output)

    # Handle operations that require server data
    if list_servers:
        # Use manager's list_servers functionality
        servers = manager.list_servers(json_data, SUPPORTED_PROTOCOLS, show_excluded)

        if json_output:
            server_data = []
            for index, server, is_excluded in servers:
                server_info = {
                    "index": index,
                    "tag": server.get("tag", ""),
                    "type": server.get("type", ""),
                    "server": server.get("server", ""),
                    "port": server.get("server_port", ""),
                    "excluded": is_excluded,
                }
                server_data.append(server_info)

            result = {
                "total_servers": len(servers),
                "servers": server_data,
            }
            print(json.dumps(result, indent=2))
        else:
            for index, server, is_excluded in servers:
                status = "🚫" if is_excluded else "✅"
                server_info = manager.format_server_info(server, index, is_excluded)
                rprint(f"{status} {server_info}")
        return

    if interactive:
        # Interactive functionality not implemented in this version
        typer.echo("Interactive mode not available in subscription exclusions")
        typer.echo("Use individual commands: add, remove, list, clear")
        return

    if add:
        exclusions_add(
            servers=add, reason=reason, url=url, json_output=json_output, ctx=ctx
        )

    if remove:
        exclusions_remove(servers=remove, url=url, json_output=json_output, ctx=ctx)

    # Show help if no action specified
    if not any([add, remove, view, clear, list_servers, interactive]):
        _show_usage_help()


__all__ = ["app"]
