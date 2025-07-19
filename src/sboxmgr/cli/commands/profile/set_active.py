"""Profile set-active command for sboxmgr (ADR-0020).

This module provides the `profile set-active` command for setting active profiles.
"""

import typer

from ....configs.profile_manager import ProfileManager
from ....utils.cli_common import get_verbose_flag


def set_active_profile(
    name: str = typer.Argument(..., help="Profile name to set as active"),
    persistent: bool = typer.Option(
        False, "--persistent", help="Save to configuration"
    ),
    validate: bool = typer.Option(
        False, "--validate", help="Validate before setting active"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
) -> None:
    """Set active profile.

    Sets the specified profile as the active profile for the system.

    Examples:
        sboxctl profile set-active home
        sboxctl profile set-active work --persistent --validate

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

        # Validate if requested
        if validate:
            validation_result = manager.validate_profile(profile)
            if not validation_result.valid:
                typer.echo(f"❌ Profile '{name}' is invalid:", err=True)
                for error in validation_result.errors:
                    typer.echo(f"  Error: {error}", err=True)
                raise typer.Exit(1)

        # Set as active
        success = manager.set_active_profile(name)
        if success:
            typer.echo(f"✅ Set active profile: {name}")

            if verbose_flag:
                typer.echo(
                    f"📁 Profile location: {manager.profiles_dir / f'{name}.toml'}"
                )
                typer.echo(f"📝 Description: {profile.description or 'No description'}")
                typer.echo(f"🔧 Export format: {profile.export.format}")
                typer.echo(f"📄 Output file: {profile.export.output_file}")
        else:
            typer.echo(f"❌ Failed to set active profile: {name}", err=True)
            raise typer.Exit(1)

    except Exception as e:
        if verbose_flag:
            typer.echo(f"Error setting active profile: {e}", err=True)
        else:
            typer.echo(
                "Error setting active profile. Use --verbose for details.", err=True
            )
        raise typer.Exit(1)
