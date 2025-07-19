"""Profile show command for sboxmgr (ADR-0020).

This module provides the `profile show` command for displaying profile contents.
"""

import json

import typer

from ....configs.profile_manager import ProfileManager
from ....utils.cli_common import get_verbose_flag


def show_profile(
    name: str = typer.Argument(..., help="Profile name to show"),
    format: str = typer.Option(
        "toml", "--format", help="Output format (yaml, toml, json)"
    ),
    compact: bool = typer.Option(False, "--compact", help="Compact output"),
    validate: bool = typer.Option(
        False, "--validate", help="Validate profile before showing"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
) -> None:
    """Show profile contents.

    Displays the contents of a FullProfile configuration in the specified format.
    The profile can be validated before display.

    Examples:
        sboxctl profile show home
        sboxctl profile show work --format yaml
        sboxctl profile show test --validate --compact

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

        # Validate if requested
        if validate:
            validation_result = manager.validate_profile(profile)
            if not validation_result.valid:
                typer.echo(f"❌ Profile '{name}' is invalid:", err=True)
                for error in validation_result.errors:
                    typer.echo(f"  Error: {error}", err=True)
                for warning in validation_result.warnings:
                    typer.echo(f"  Warning: {warning}", err=True)
                raise typer.Exit(1)
            else:
                if verbose_flag:
                    typer.echo(f"✅ Profile '{name}' is valid.")

        # Prepare output data
        if compact:
            # Compact output - only essential fields
            output_data = {
                "id": profile.id,
                "description": profile.description,
                "subscriptions_count": len(profile.subscriptions),
                "export_format": profile.export.format,
                "export_output": profile.export.output_file,
                "version": profile.version,
            }
        else:
            # Full profile data
            output_data = profile.model_dump()

        # Output in requested format
        if format.lower() == "json":
            typer.echo(json.dumps(output_data, indent=2, default=str))
        elif format.lower() == "yaml":
            import yaml

            typer.echo(
                yaml.dump(output_data, default_flow_style=False, default_style=None)
            )
        elif format.lower() == "toml":
            # For TOML output, we need to convert back to TOML format
            # This is a simplified approach - in practice, you might want to use a TOML library
            typer.echo(f"# Profile: {profile.id}")
            if profile.description:
                typer.echo(f"# Description: {profile.description}")
            typer.echo(f"# Version: {profile.version}")
            typer.echo()

            # Show key sections
            typer.echo("[export]")
            typer.echo(f'format = "{profile.export.format}"')
            typer.echo(f'output_file = "{profile.export.output_file}"')
            typer.echo(f'outbound_profile = "{profile.export.outbound_profile}"')
            typer.echo(f'inbound_profile = "{profile.export.inbound_profile}"')
            typer.echo()

            typer.echo("[routing]")
            typer.echo(f'default_route = "{profile.routing.default_route}"')
            if profile.routing.custom_routes:
                typer.echo("[routing.custom_routes]")
                for route, target in profile.routing.custom_routes.items():
                    typer.echo(f'"{route}" = "{target}"')
            typer.echo()

            if profile.subscriptions:
                typer.echo("[[subscriptions]]")
                for sub in profile.subscriptions:
                    typer.echo(f'id = "{sub.id}"')
                    typer.echo(f"enabled = {str(sub.enabled).lower()}")
                    typer.echo(f"priority = {sub.priority}")
                    typer.echo()
        else:
            typer.echo(f"Unsupported format: {format}", err=True)
            typer.echo("Supported formats: json, yaml, toml")
            raise typer.Exit(1)

        if verbose_flag:
            typer.echo()
            typer.echo(f"Profile loaded from: {manager.profiles_dir / f'{name}.toml'}")

    except Exception as e:
        if verbose_flag:
            typer.echo(f"Error showing profile: {e}", err=True)
        else:
            typer.echo("Error showing profile. Use --verbose for details.", err=True)
        raise typer.Exit(1)
