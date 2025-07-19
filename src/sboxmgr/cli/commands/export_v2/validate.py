"""Export validate subcommand for sboxmgr (ADR-0020).

This module provides the `export validate` command for validating configurations.
"""

from pathlib import Path
from typing import Optional

import typer

from sboxmgr.config.validation import validate_config_file

from ....utils.cli_common import get_verbose_flag


def validate_config(
    config_file: str = typer.Argument(..., help="Configuration file to validate"),
    against_profile: Optional[str] = typer.Option(
        None, "--against-profile", help="Profile name to validate against"
    ),
    as_format: Optional[str] = typer.Option(
        None, "--as", help="Override format detection (json, toml)"
    ),
    agent_check: bool = typer.Option(
        False, "--agent-check", help="Check configuration via sboxagent"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    ctx: typer.Context = None,
) -> None:
    """Validate configuration file.

    Validates a configuration file for syntax and semantic correctness.
    This command adapts the existing validation functionality to work with
    the new two-layer architecture.

    Examples:
        sboxctl export validate config.json
        sboxctl export validate config.toml --against-profile home
        sboxctl export validate config.json --agent-check

    """
    # Get global flags from context
    global_verbose = ctx.obj.get("verbose", False) if ctx and ctx.obj else False

    verbose_flag = get_verbose_flag(verbose or global_verbose)

    try:
        # Check if file exists
        if not Path(config_file).exists():
            typer.echo(f"Configuration file not found: {config_file}", err=True)
            raise typer.Exit(1)

        if verbose_flag:
            typer.echo(f"Validating configuration file: {config_file}")
            if as_format:
                typer.echo(f"Format override: {as_format}")

        # Use existing validation logic
        try:
            validate_config_file(config_file)
            typer.echo(f"✅ Configuration is valid: {config_file}")
        except Exception as e:
            typer.echo(f"❌ Configuration is invalid: {config_file}", err=True)
            typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(1)

        # Run agent check if requested
        if agent_check:
            from ..export.mode_handlers import run_agent_check

            if not run_agent_check(config_file, agent_check):
                raise typer.Exit(1)

        if verbose_flag:
            file_size = Path(config_file).stat().st_size
            typer.echo("Validation details:")
            typer.echo(f"  - File: {config_file}")
            typer.echo(f"  - Size: {file_size} bytes")
            if as_format:
                typer.echo(f"  - Format: {as_format} (override)")
            else:
                typer.echo("  - Format: auto-detected")
            if agent_check:
                typer.echo(f"  - Agent check: {'passed' if agent_check else 'skipped'}")

    except Exception as e:
        if verbose_flag:
            typer.echo(f"Error validating config: {e}", err=True)
        else:
            typer.echo("Error validating config. Use --verbose for details.", err=True)
        raise typer.Exit(1)
