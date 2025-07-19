"""Profile edit command for sboxmgr (ADR-0020).

This module provides the `profile edit` command for editing profiles.
"""

import os
import subprocess
import tempfile
from typing import Optional

import typer

from ....configs.profile_manager import ProfileManager
from ....utils.cli_common import get_verbose_flag


def edit_profile(
    name: str = typer.Argument(..., help="Profile name to edit"),
    editor: Optional[str] = typer.Option(None, "--editor", help="Editor to use"),
    validate: bool = typer.Option(False, "--validate", help="Validate after editing"),
    backup: bool = typer.Option(False, "--backup", help="Create backup before editing"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
) -> None:
    """Edit profile in external editor.

    Opens the profile in the specified editor (or $EDITOR).

    Examples:
        sboxctl profile edit home
        sboxctl profile edit work --editor code --validate

    """
    verbose_flag = get_verbose_flag(verbose)
    manager = ProfileManager()

    try:
        # Check if profile exists
        profile = manager.get_profile(name)
        if not profile:
            typer.echo(f"Profile '{name}' not found.", err=True)
            typer.echo("Use 'sboxctl profile list' to see available profiles.")
            raise typer.Exit(1)

        # Create backup if requested
        if backup:
            backup_name = f"{name}.backup"
            manager.save_profile(profile, backup_name)
            if verbose_flag:
                typer.echo(f"Created backup: {backup_name}")

        # Get editor
        editor_cmd = editor or os.environ.get("EDITOR", "nano")

        # Create temporary file with current profile content
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".toml", delete=False
        ) as tmp_file:
            # Save current profile to temp file
            manager.save_profile_to_file(profile, tmp_file.name)
            tmp_file_path = tmp_file.name

        try:
            # Open editor
            if verbose_flag:
                typer.echo(f"Opening profile in editor: {editor_cmd}")

            result = subprocess.run([editor_cmd, tmp_file_path], check=True)

            if result.returncode != 0:
                typer.echo("Editor exited with error.", err=True)
                raise typer.Exit(1)

            # Load edited profile
            edited_profile = manager.load_profile_from_file(tmp_file_path)

            # Validate if requested
            if validate:
                if verbose_flag:
                    typer.echo("Validating edited profile...")

                validation_result = manager.validate_profile(edited_profile)
                if not validation_result.is_valid:
                    typer.echo("Profile validation failed:", err=True)
                    for error in validation_result.errors:
                        typer.echo(f"  - {error}", err=True)
                    raise typer.Exit(1)

                if verbose_flag:
                    typer.echo("Profile validation passed.")

            # Save the edited profile
            manager.save_profile(edited_profile, name)
            typer.echo(f"Profile '{name}' updated successfully.")

        finally:
            # Clean up temporary file
            try:
                os.unlink(tmp_file_path)
            except OSError:
                pass

    except subprocess.CalledProcessError as e:
        typer.echo(f"Editor error: {e}", err=True)
        raise typer.Exit(1)
    except Exception as e:
        if verbose_flag:
            typer.echo(f"Error editing profile: {e}", err=True)
        else:
            typer.echo("Error editing profile. Use --verbose for details.", err=True)
        raise typer.Exit(1)
