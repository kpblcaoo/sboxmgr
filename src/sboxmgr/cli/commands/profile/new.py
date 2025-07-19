"""Profile new command for sboxmgr (ADR-0020).

This module provides the `profile new` command for creating new profiles.
"""

from typing import Optional

import typer

from ....configs.profile_manager import ProfileManager
from ....configs.templates import get_template_description, get_template_names
from ....utils.cli_common import get_verbose_flag


def new_profile(
    name: str = typer.Argument(..., help="Profile name"),
    description: Optional[str] = typer.Option(
        None, "--description", help="Profile description"
    ),
    template: Optional[str] = typer.Option(
        None,
        "--template",
        help="Template to use (basic, vpn, server, development, minimal)",
    ),
    format: str = typer.Option("toml", "--format", help="File format (toml, yaml)"),
    edit: bool = typer.Option(False, "--edit", help="Open in editor after creation"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
) -> None:
    """Create a new profile.

    Creates a new FullProfile configuration with optional template.
    The profile will be saved to ~/.config/sboxmgr/profiles/ directory.

    Examples:
        sboxctl profile new my-profile
        sboxctl profile new work-vpn --template vpn --description "Work VPN"
        sboxctl profile new test --template basic --edit

    """
    verbose_flag = get_verbose_flag(verbose)
    manager = ProfileManager()

    try:
        # Check if profile already exists
        existing_profile = manager.get_profile(name)
        if existing_profile:
            typer.echo(f"Profile '{name}' already exists.", err=True)
            typer.echo("Use a different name or delete the existing profile first.")
            raise typer.Exit(1)

        # Validate template if provided
        if template:
            available_templates = get_template_names()
            if template not in available_templates:
                typer.echo(f"Invalid template: {template}", err=True)
                typer.echo(f"Available templates: {', '.join(available_templates)}")
                raise typer.Exit(1)

        # Create profile
        profile = manager.create_profile(name, template)

        # Set description if provided
        if description:
            profile.description = description

        # Save profile
        manager.save_profile(profile)

        # Success message
        typer.echo(f"✅ Created profile: {name}")

        if template:
            template_desc = get_template_description(template)
            typer.echo(f"📋 Template: {template} ({template_desc})")

        if description:
            typer.echo(f"📝 Description: {description}")

        typer.echo(f"📁 Location: {manager.profiles_dir / f'{name}.toml'}")

        if verbose_flag:
            typer.echo(f"🔧 Export format: {profile.export.format}")
            typer.echo(f"📄 Output file: {profile.export.output_file}")
            typer.echo(f"🔄 Default route: {profile.routing.default_route}")

        # Open in editor if requested
        if edit:
            try:
                import os
                import subprocess

                editor = os.environ.get("EDITOR", "nano")
                profile_path = manager.profiles_dir / f"{name}.toml"

                typer.echo(f"📝 Opening {name}.toml in {editor}...")
                subprocess.run([editor, str(profile_path)], check=True)

            except Exception as e:
                if verbose_flag:
                    typer.echo(f"Warning: Could not open editor: {e}", err=True)
                else:
                    typer.echo(
                        "Warning: Could not open editor. Edit manually.", err=True
                    )

        # Next steps
        typer.echo()
        typer.echo("Next steps:")
        typer.echo(f"  sboxctl profile show {name}          # View profile")
        typer.echo(f"  sboxctl profile edit {name}          # Edit profile")
        typer.echo(f"  sboxctl profile set-active {name}    # Set as active")
        typer.echo(f"  sboxctl export generate --profile {name}  # Generate config")

    except Exception as e:
        if verbose_flag:
            typer.echo(f"Error creating profile: {e}", err=True)
        else:
            typer.echo("Error creating profile. Use --verbose for details.", err=True)
        raise typer.Exit(1)
