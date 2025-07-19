"""Profile import command for sboxmgr (ADR-0020).

This module provides the `profile import` command for importing profiles.
"""

import os
from pathlib import Path
from typing import Optional

import typer

from ....configs.profile_manager import ProfileManager
from ....utils.cli_common import get_verbose_flag


def import_profile(
    file_path: str = typer.Argument(..., help="Profile file to import"),
    name: Optional[str] = typer.Option(
        None, "--name", help="Profile name (default: from file)"
    ),
    overwrite: bool = typer.Option(
        False, "--overwrite", help="Overwrite existing profile"
    ),
    validate: bool = typer.Option(False, "--validate", help="Validate after import"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
) -> None:
    """Import profile from file.

    Imports a FullProfile configuration from a file.

    Examples:
        sboxctl profile import my-profile.toml
        sboxctl profile import config.yaml --name imported-profile --validate

    """
    verbose_flag = get_verbose_flag(verbose)
    manager = ProfileManager()

    try:
        # Check if file exists
        if not os.path.exists(file_path):
            typer.echo(f"File not found: {file_path}", err=True)
            raise typer.Exit(1)

        # Determine profile name
        if name is None:
            name = Path(file_path).stem

        if verbose_flag:
            typer.echo(f"Importing profile from: {file_path}")
            typer.echo(f"Profile name will be: {name}")

        # Check if profile already exists
        existing_profile = manager.get_profile(name)
        if existing_profile and not overwrite:
            typer.echo(f"Profile '{name}' already exists.", err=True)
            typer.echo(
                "Use --overwrite to replace it or --name to specify a different name."
            )
            raise typer.Exit(1)

        # Load profile from file
        try:
            imported_profile = manager.load_profile_from_file(file_path)
        except Exception as e:
            typer.echo(f"Failed to load profile from {file_path}: {e}", err=True)
            raise typer.Exit(1)

        # Update profile ID to match the new name
        imported_profile.id = name

        # Validate if requested
        if validate:
            if verbose_flag:
                typer.echo("Validating imported profile...")

            validation_result = manager.validate_profile(imported_profile)
            if not validation_result.is_valid:
                typer.echo("Profile validation failed:", err=True)
                for error in validation_result.errors:
                    typer.echo(f"  - {error}", err=True)
                raise typer.Exit(1)

            if validation_result.warnings:
                typer.echo("Profile validation warnings:")
                for warning in validation_result.warnings:
                    typer.echo(f"  - {warning}")

            if verbose_flag:
                typer.echo("Profile validation passed.")

        # Save the imported profile
        manager.save_profile(imported_profile)
        typer.echo(f"Profile '{name}' imported successfully.")

        if verbose_flag:
            typer.echo("Profile details:")
            typer.echo(f"  - ID: {imported_profile.id}")
            typer.echo(f"  - Description: {imported_profile.description}")
            typer.echo(f"  - Subscriptions: {len(imported_profile.subscriptions)}")
            typer.echo(f"  - Created: {imported_profile.created_at}")

    except Exception as e:
        if verbose_flag:
            typer.echo(f"Error importing profile: {e}", err=True)
        else:
            typer.echo("Error importing profile. Use --verbose for details.", err=True)
        raise typer.Exit(1)
