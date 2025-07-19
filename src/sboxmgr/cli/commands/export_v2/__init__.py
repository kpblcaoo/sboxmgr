"""Export command group for sboxmgr (ADR-0020).

This module provides the new export command group with subcommands:
- generate: Generate ClientConfig from FullProfile
- validate: Validate configurations
- dry-run: Test mode without saving
- profile: Export optimized FullProfile
"""

import typer

from .dry_run import dry_run_config
from .generate import generate_config
from .profile import export_profile_config
from .validate import validate_config

# Create the export command group
app = typer.Typer(
    name="export",
    help="Export configurations and profiles",
    no_args_is_help=True,
)

# Register subcommands
app.command(name="generate")(generate_config)
app.command(name="validate")(validate_config)
app.command(name="dry-run")(dry_run_config)
app.command(name="profile")(export_profile_config)

__all__ = ["app"]
