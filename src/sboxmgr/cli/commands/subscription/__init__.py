"""Subscription management commands group.

This module provides commands for managing subscriptions, servers, and exclusions
in a unified interface under the 'subscription' command group.
"""

import typer

from sboxmgr.i18n.t import t

# Import and register subcommands
from . import exclusions, list

# Create the subscription command group
app = typer.Typer(
    help=t("cli.subscription.help"),
    name="subscription",
    add_completion=False,
)

# Register subcommands
app.add_typer(exclusions.app, name="exclusions")


# Register list as a direct command (not a group)
@app.command("list")
def list_servers(
    url: str = typer.Option(
        ...,
        "-u",
        "--url",
        help="Subscription URL to list servers from",
        envvar=["SBOXMGR_URL", "SINGBOX_URL", "TEST_URL"],
    ),
    debug: int = typer.Option(0, "-d", "--debug", help="Debug verbosity level (0-2)"),
    user_agent: str = typer.Option(
        "ClashMeta/1.0",
        "--user-agent",
        help="Override User-Agent for subscription fetcher (default: ClashMeta/1.0)",
    ),
    no_user_agent: bool = typer.Option(
        False, "--no-user-agent", help="Do not send User-Agent header at all"
    ),
    format: str = typer.Option(
        None,
        "--format",
        help="Force specific format: auto, base64, json, uri_list, clash",
    ),
    policy_details: bool = typer.Option(
        False,
        "-P",
        "--policy-details",
        help="Show policy evaluation details for each server",
    ),
    output_format: str = typer.Option(
        "table",
        "--output-format",
        help="Output format: table, json",
    ),
    ctx: typer.Context = None,
):
    """List all available servers from subscription."""
    return list.list_servers(
        url=url,
        debug=debug,
        user_agent=user_agent,
        no_user_agent=no_user_agent,
        format=format,
        policy_details=policy_details,
        output_format=output_format,
        ctx=ctx,
    )


__all__ = ["app"]
