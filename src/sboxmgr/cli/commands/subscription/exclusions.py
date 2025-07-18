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
from sboxmgr.i18n.t import t
from sboxmgr.server.exclusions import clear_exclusions, load_exclusions, save_exclusions

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


def _cache_server_data(json_data: dict, json_output: bool) -> None:
    """Cache server data for exclusions.

    Args:
        json_data: Server data to cache
        json_output: Whether to output errors in JSON format

    Raises:
        typer.Exit: If server data format is invalid

    """
    try:
        # Validate that we have outbounds
        if "outbounds" not in json_data:
            raise ValueError("No outbounds found in subscription data")
    except Exception:
        error_msg = t("error.invalid_server_format")
        if json_output:
            print(json.dumps({"error": error_msg}))
        else:
            rprint(f"[red]❌ {error_msg}[/red]")
            rprint(f"[yellow]💡 {t('cli.subscription_format_hint')}[/yellow]")
        raise typer.Exit(1) from None


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

    exclusions_data = load_exclusions()
    exclusions = exclusions_data.get("exclusions", [])

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
            exc.get("timestamp", "N/A")[:10],
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

    # Fetch and cache server data
    json_data = _fetch_and_validate_subscription(url, json_output)
    _cache_server_data(json_data, json_output)

    # Parse server list
    server_list = [s.strip() for s in servers.split(",") if s.strip()]

    # Load current exclusions
    exclusions_data = load_exclusions()
    current_exclusions = exclusions_data.get("exclusions", [])

    added_count = 0
    for server_id in server_list:
        try:
            # Check if server_id is a number (index) or string (name/pattern)
            if server_id.isdigit():
                # Handle by index
                index = int(server_id)
                new_exclusion = {
                    "id": f"index_{index}",
                    "name": f"Server at index {index}",
                    "reason": reason,
                    "timestamp": "2025-01-01T00:00:00Z",
                }
            else:
                # Handle by name/pattern
                new_exclusion = {
                    "id": server_id,
                    "name": f"Server {server_id}",
                    "reason": reason,
                    "timestamp": "2025-01-01T00:00:00Z",
                }

            # Check if already excluded
            if not any(
                ex.get("id") == new_exclusion["id"] for ex in current_exclusions
            ):
                current_exclusions.append(new_exclusion)
                added_count += 1
            else:
                if verbose:
                    typer.echo(f"Server {server_id} already excluded")
        except Exception as e:
            if json_output:
                print(json.dumps({"error": f"Failed to add {server_id}: {e}"}))
            else:
                rprint(f"[red]❌ Failed to add {server_id}: {e}[/red]")

    # Save updated exclusions
    exclusions_data["exclusions"] = current_exclusions
    save_exclusions(exclusions_data)

    if json_output:
        print(
            json.dumps(
                {
                    "action": "add",
                    "added_count": added_count,
                    "total_requested": len(server_list),
                }
            )
        )
    else:
        rprint(f"[green]✅ Added {added_count} servers to exclusions[/green]")


@app.command("remove")
def exclusions_remove(
    servers: str = typer.Option(
        ..., "--servers", help="Server indices or names to remove from exclusions"
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

    # Load current exclusions
    exclusions_data = load_exclusions()
    current_exclusions = exclusions_data.get("exclusions", [])

    # Parse server list
    server_list = [s.strip() for s in servers.split(",") if s.strip()]

    removed_count = 0
    for server_id in server_list:
        try:
            # Remove exclusions that match the server_id
            original_count = len(current_exclusions)
            current_exclusions = [
                ex for ex in current_exclusions if ex.get("id") != server_id
            ]
            if len(current_exclusions) < original_count:
                removed_count += 1
        except Exception as e:
            if json_output:
                print(json.dumps({"error": f"Failed to remove {server_id}: {e}"}))
            else:
                rprint(f"[red]❌ Failed to remove {server_id}: {e}[/red]")

    # Save updated exclusions
    exclusions_data["exclusions"] = current_exclusions
    save_exclusions(exclusions_data)

    if json_output:
        print(
            json.dumps(
                {
                    "action": "remove",
                    "removed_count": removed_count,
                    "total_requested": len(server_list),
                }
            )
        )
    else:
        rprint(f"[green]✅ Removed {removed_count} servers from exclusions[/green]")


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

    # Load current exclusions
    exclusions_data = load_exclusions()
    current_exclusions = exclusions_data.get("exclusions", [])

    # Check if we have any exclusions
    if not current_exclusions:
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

    count = len(current_exclusions)
    clear_exclusions()

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
        _cache_server_data(json_data, json_output)

    # Handle operations that require server data
    if list_servers:
        # Redirect to subscription list command
        typer.echo("Use 'subscription list' command to list servers")
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
        exclusions_remove(servers=remove, json_output=json_output, ctx=ctx)

    # Show help if no action specified
    if not any([add, remove, view, clear, list_servers, interactive]):
        rprint(f"[yellow]💡 {t('cli.exclusions.usage_hint')}[/yellow]")
        rprint(f"[dim]{t('cli.exclusions.usage_example')}[/dim]")


__all__ = ["app"]
