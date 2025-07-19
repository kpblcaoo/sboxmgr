"""Profile delete command for sboxmgr (ADR-0020).

This module provides the `profile delete` command for deleting profiles.
"""

import typer

from ....configs.profile_manager import ProfileManager
from ....utils.cli_common import get_verbose_flag


def delete_profile(
    name: str = typer.Argument(..., help="Profile name to delete"),
    force: bool = typer.Option(
        False, "--force", help="Force deletion without confirmation"
    ),
    backup: bool = typer.Option(
        False, "--backup", help="Create backup before deletion"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
) -> None:
    """Delete profile.

    Deletes a FullProfile configuration from the system.

    Examples:
        sboxctl profile delete test
        sboxctl profile delete old-profile --force --backup

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

        # Check if it's the active profile
        active_profile_name = manager.get_active_profile_name()
        if name == active_profile_name:
            typer.echo(f"⚠️  Warning: '{name}' is the active profile.", err=True)
            if not force:
                typer.echo("Use --force to delete the active profile.", err=True)
                raise typer.Exit(1)

        # Confirm deletion (unless --force)
        if not force:
            typer.echo(f"Are you sure you want to delete profile '{name}'?")
            typer.echo("This action cannot be undone.")

            # TODO: Add interactive confirmation
            typer.echo("TODO: Add interactive confirmation")
            typer.echo("Use --force to skip confirmation")

        # TODO: Create backup if requested
        if backup:
            typer.echo("TODO: Create backup before deletion")

        # Delete profile
        success = manager.delete_profile(name)
        if success:
            typer.echo(f"✅ Deleted profile: {name}")

            if verbose_flag:
                typer.echo("🗑️  Profile file removed")
                if name == active_profile_name:
                    typer.echo("🔄 Active profile cleared")
        else:
            typer.echo(f"❌ Failed to delete profile: {name}", err=True)
            raise typer.Exit(1)

    except Exception as e:
        if verbose_flag:
            typer.echo(f"Error deleting profile: {e}", err=True)
        else:
            typer.echo("Error deleting profile. Use --verbose for details.", err=True)
        raise typer.Exit(1)
