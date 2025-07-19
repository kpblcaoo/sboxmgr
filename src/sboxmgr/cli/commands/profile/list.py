"""Profile list command for sboxmgr (ADR-0020).

This module provides the `profile list` command for listing available profiles.
"""

import json

import typer

from ....configs.profile_manager import ProfileManager
from ....utils.cli_common import get_verbose_flag


def list_profiles(
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
    show_active: bool = typer.Option(
        False, "--show-active", help="Show active profile"
    ),
    show_details: bool = typer.Option(
        False, "--show-details", help="Show profile details"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
) -> None:
    """List available profiles.

    Shows all available FullProfile configurations with their status and details.
    Profiles are stored in ~/.config/sboxmgr/profiles/ directory.

    Examples:
        sboxctl profile list
        sboxctl profile list --show-active
        sboxctl profile list --json --show-details

    """
    verbose_flag = get_verbose_flag(verbose)
    manager = ProfileManager()

    try:
        profiles = manager.list_profiles()
        active_profile_name = manager.get_active_profile_name()

        if json_output:
            # JSON output for automation
            output_data = {
                "profiles": [
                    {
                        "name": profile.name,
                        "path": profile.path,
                        "size": profile.size,
                        "modified": profile.modified.isoformat(),
                        "valid": profile.valid,
                        "error": profile.error,
                        "is_active": profile.name == active_profile_name,
                    }
                    for profile in profiles
                ],
                "active_profile": active_profile_name,
                "total_count": len(profiles),
            }
            typer.echo(json.dumps(output_data, indent=2))
            return

        # Human-readable output
        if not profiles:
            typer.echo("📋 No profiles found.")
            typer.echo("Create your first profile with: sboxctl profile new <name>")
            return

        typer.echo("📋 Available Profiles:")
        typer.echo()

        for profile in profiles:
            # Status indicator
            status = "✅" if profile.valid else "❌"
            active_indicator = " *" if profile.name == active_profile_name else ""

            # Basic info
            typer.echo(f"  {profile.name}{active_indicator}")

            if show_details:
                # Detailed info
                typer.echo(f"    Path: {profile.path}")
                typer.echo(f"    Size: {profile.size} bytes")
                typer.echo(
                    f"    Modified: {profile.modified.strftime('%Y-%m-%d %H:%M:%S')}"
                )
                typer.echo(f"    Status: {status}")

                if not profile.valid and profile.error:
                    typer.echo(f"    Error: {profile.error}")

                if verbose_flag:
                    # Load profile for additional details
                    full_profile = manager.get_profile(profile.name)
                    if full_profile:
                        typer.echo(
                            f"    Description: {full_profile.description or 'No description'}"
                        )
                        typer.echo(
                            f"    Subscriptions: {len(full_profile.subscriptions)}"
                        )
                        typer.echo(f"    Version: {full_profile.version}")

                typer.echo()
            else:
                # Compact info
                if not profile.valid:
                    typer.echo(f"    {status} Invalid")
                elif show_active and profile.name == active_profile_name:
                    typer.echo(f"    {status} Active")
                else:
                    typer.echo(f"    {status} Valid")

        if show_active and active_profile_name:
            typer.echo()
            typer.echo(f"* = active profile ({active_profile_name})")

        if verbose_flag:
            typer.echo()
            typer.echo(f"Total profiles: {len(profiles)}")
            typer.echo(f"Valid profiles: {sum(1 for p in profiles if p.valid)}")
            typer.echo(f"Invalid profiles: {sum(1 for p in profiles if not p.valid)}")

    except Exception as e:
        if verbose_flag:
            typer.echo(f"Error listing profiles: {e}", err=True)
        else:
            typer.echo("Error listing profiles. Use --verbose for details.", err=True)
        raise typer.Exit(1)
