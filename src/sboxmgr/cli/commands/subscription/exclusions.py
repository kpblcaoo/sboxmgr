"""Exclusions management commands for subscription CLI.

This module provides the CLI interface for managing server exclusions
within the subscription command group. It includes commands for listing,
adding, removing, and clearing exclusions.

Legacy exclusions_main command removed - functionality fully migrated to subcommands.
All operations now available through individual commands:
- sboxctl subscription exclusions list
- sboxctl subscription exclusions add --servers 0,1,2
- sboxctl subscription exclusions remove --servers 0,1,2
- sboxctl subscription exclusions clear
- sboxctl subscription exclusions list-servers
"""

import json

import typer
from rich.console import Console

from sboxmgr.config.fetch import fetch_json
from sboxmgr.constants import SUPPORTED_PROTOCOLS
from sboxmgr.core.exclusions import ExclusionManager
from sboxmgr.i18n.t import t

from .exclusions_logic import (
    exclusions_add_logic,
    exclusions_clear_logic,
    exclusions_list_logic,
    exclusions_list_servers_logic,
    exclusions_remove_logic,
)
from .exclusions_utils import validate_subscription_url

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


def _get_context_value(ctx: typer.Context, key: str, default=None):
    """Extract value from context object with safe fallback.

    Args:
        ctx: Typer context object
        key: Key to extract from context
        default: Default value if key not found

    Returns:
        Value from context or default

    """
    return ctx.obj.get(key, default) if ctx is not None and ctx.obj else default


def _get_verbose_flag(ctx: typer.Context) -> bool:
    """Extract verbose flag from context with safe fallback.

    Args:
        ctx: Typer context object

    Returns:
        Verbose flag value or False if not found

    """
    return _get_context_value(ctx, "verbose", False)


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
    verbose = _get_verbose_flag(ctx)

    if verbose:
        typer.echo("📋 Listing exclusions...")

    manager = ExclusionManager.default()
    exclusions_list_logic(manager, json_output)


# Logic functions moved to exclusions_logic.py module


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
    url = _get_context_value(ctx, "exclusions_url")
    verbose = _get_context_value(ctx, "verbose", False)

    # Validate URL
    validate_subscription_url(url, json_output)

    manager = ExclusionManager.default()

    # Fetch and cache server data
    json_data = _fetch_and_validate_subscription(url, json_output)
    _cache_server_data(manager, json_data, json_output)

    exclusions_add_logic(manager, servers, reason, json_output, verbose)


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
    url = _get_context_value(ctx, "exclusions_url")
    verbose = _get_context_value(ctx, "verbose", False)

    # Validate URL
    validate_subscription_url(url, json_output)

    if verbose:
        typer.echo("➖ Removing exclusions...")
        typer.echo(f"   Servers: {servers}")

    manager = ExclusionManager.default()

    # Fetch and cache server data
    json_data = _fetch_and_validate_subscription(url, json_output)
    _cache_server_data(manager, json_data, json_output)

    # Use the shared logic function
    exclusions_remove_logic(manager, servers, json_output, verbose)


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
    url = _get_context_value(ctx, "exclusions_url")
    verbose = _get_context_value(ctx, "verbose", False)

    # Validate URL
    validate_subscription_url(url, json_output)

    if verbose:
        typer.echo("📡 Listing servers...")
        typer.echo(f"   URL: {url}")
        typer.echo(f"   Show excluded: {show_excluded}")

    manager = ExclusionManager.default()

    # Fetch and cache server data
    json_data = _fetch_and_validate_subscription(url, json_output)
    _cache_server_data(manager, json_data, json_output)

    # List servers with exclusion status
    exclusions_list_servers_logic(manager, json_output, show_excluded)


@app.command("clear")
def exclusions_clear(
    json_output: bool = typer.Option(False, "--json", help=t("cli.json.help")),
    ctx: typer.Context = None,
):
    """Clear all exclusions.

    Removes all server exclusions. Requires confirmation unless --yes is used.
    """
    # Get global flags from context
    verbose = _get_context_value(ctx, "verbose", False)
    global_yes = _get_context_value(ctx, "yes", False)

    if verbose:
        typer.echo("🗑️ Clearing all exclusions...")

    manager = ExclusionManager.default()
    exclusions_clear_logic(manager, json_output, global_yes)


__all__ = ["app"]
