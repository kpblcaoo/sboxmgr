"""CLI commands for managing server exclusions (`sboxctl exclusions`).

This module provides Typer command handlers for adding, removing, listing, and
clearing exclusions of subscription servers. Exclusions are stored in a JSON
file and applied during the subscription processing pipeline to filter out
unwanted servers.
"""
import typer
from sboxmgr.config.fetch import fetch_json
from sboxmgr.server.exclusions import exclude_servers, remove_exclusions, view_exclusions
from sboxmgr.utils.env import SUPPORTED_PROTOCOLS
from sboxmgr.i18n.t import t

def exclusions(
    url: str = typer.Option(
        ..., "-u", "--url", help=t("cli.url.help"),
        envvar=["SBOXMGR_URL", "SINGBOX_URL", "TEST_URL"]
    ),
    add: str = typer.Option(None, "--add", help=t("cli.add.help")),
    remove: str = typer.Option(None, "--remove", help=t("cli.remove.help")),
    view: bool = typer.Option(False, "--view", help=t("cli.view.help")),
    debug: int = typer.Option(0, "-d", "--debug", help=t("cli.debug.help")),
):
    """Manage exclusions: add, remove, view."""
    try:
        json_data = fetch_json(url)
    except Exception as e:
        typer.echo(f"{t('error.config_load_failed')}: {e}", err=True)
        raise typer.Exit(1)
    if view:
        view_exclusions(debug)
        raise typer.Exit(0)
    if add:
        add_exclusions = [x.strip() for x in add.split(",") if x.strip()]
        exclude_servers(json_data, add_exclusions, SUPPORTED_PROTOCOLS, debug)
    if remove:
        remove_exclusions_list = [x.strip() for x in remove.split(",") if x.strip()]
        remove_exclusions(remove_exclusions_list, json_data, SUPPORTED_PROTOCOLS, debug)
    if not (add or remove or view):
        typer.echo(t("cli.use_add_remove_view"))

def clear_exclusions(
    confirm: bool = typer.Option(False, "--yes", help=t("cli.confirm.help")),
    debug: int = typer.Option(0, "-d", "--debug", help=t("cli.debug.help")),
):
    """Clear all exclusions."""
    from sboxmgr.server.exclusions import clear_exclusions as do_clear_exclusions
    if not confirm:
        typer.echo("[Warning] Use --yes to confirm clearing all exclusions.")
        raise typer.Exit(1)
    do_clear_exclusions()
    typer.echo("All exclusions cleared.") 