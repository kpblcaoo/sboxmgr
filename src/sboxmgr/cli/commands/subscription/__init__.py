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
app.add_typer(list.app, name="list")
app.add_typer(exclusions.app, name="exclusions")

__all__ = ["app"]
