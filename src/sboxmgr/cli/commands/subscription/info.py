"""Subscription info command module.

This module provides the 'subscription info' command for displaying
subscription information and metadata.
"""

import typer

from sboxmgr.i18n.t import t

# Create the info command app
app = typer.Typer(
    help=t("cli.subscription.info.help"),
    name="info",
    add_completion=False,
)


@app.command()
def subscription_info(
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
    """Show subscription information and metadata.

    Displays detailed information about the subscription including:
    - URL and format
    - Number of servers
    - Connection status
    - Last update time
    - Data size

    Args:
        url: Subscription URL to analyze
        json_output: Output in JSON format
        ctx: Typer context containing global flags

    """
    # Get global flags from context
    verbose = ctx.obj.get("verbose", False) if ctx is not None and ctx.obj else False

    if verbose:
        typer.echo("ℹ️ Analyzing subscription...")
        typer.echo(f"   URL: {url}")

    # TODO: Implement subscription info functionality
    typer.echo("📊 Subscription Info")
    typer.echo(f"   URL: {url}")
    typer.echo("   Status: Not implemented yet")
    typer.echo("   This feature will be implemented in future phases")


__all__ = ["app"]
