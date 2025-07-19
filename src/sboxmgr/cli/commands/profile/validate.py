"""Profile validate command for sboxmgr (ADR-0020).

This module provides the `profile validate` command for validating profiles.
"""

import typer

from ....configs.profile_manager import ProfileManager
from ....utils.cli_common import get_verbose_flag


def validate_profile(
    name: str = typer.Argument(..., help="Profile name to validate"),
    strict: bool = typer.Option(False, "--strict", help="Strict validation"),
    show_errors: bool = typer.Option(
        False, "--show-errors", help="Show detailed errors"
    ),
    fix: bool = typer.Option(False, "--fix", help="Try to fix errors"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
) -> None:
    """Validate profile configuration.

    Validates a FullProfile configuration and reports any issues.

    Examples:
        sboxctl profile validate home
        sboxctl profile validate work --strict --show-errors

    """
    verbose_flag = get_verbose_flag(verbose)
    manager = ProfileManager()

    try:
        # Get profile
        profile = manager.get_profile(name)
        if not profile:
            typer.echo(f"Profile '{name}' not found.", err=True)
            typer.echo("Use 'sboxctl profile list' to see available profiles.")
            raise typer.Exit(1)

        # Validate profile
        validation_result = manager.validate_profile(profile)

        if validation_result.valid:
            typer.echo(f"✅ Profile '{name}' is valid")

            if validation_result.warnings:
                typer.echo("⚠️  Warnings:")
                for warning in validation_result.warnings:
                    typer.echo(f"  - {warning}")
        else:
            typer.echo(f"❌ Profile '{name}' is invalid")

            if show_errors or verbose_flag:
                typer.echo("Errors:")
                for error in validation_result.errors:
                    typer.echo(f"  - {error}")

            if validation_result.warnings:
                typer.echo("Warnings:")
                for warning in validation_result.warnings:
                    typer.echo(f"  - {warning}")

            raise typer.Exit(1)

        if verbose_flag:
            typer.echo("📊 Validation summary:")
            typer.echo(f"  - Errors: {len(validation_result.errors)}")
            typer.echo(f"  - Warnings: {len(validation_result.warnings)}")

    except Exception as e:
        if verbose_flag:
            typer.echo(f"Error validating profile: {e}", err=True)
        else:
            typer.echo("Error validating profile. Use --verbose for details.", err=True)
        raise typer.Exit(1)
