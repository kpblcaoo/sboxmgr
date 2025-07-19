"""Profile export command for sboxmgr (ADR-0020).

This module provides the `profile export` command for exporting profiles.
"""

import json
from pathlib import Path
from typing import Optional

import typer

from ....configs.profile_manager import ProfileManager
from ....utils.cli_common import get_verbose_flag


def export_profile(
    name: str = typer.Argument(..., help="Profile name to export"),
    out: Optional[str] = typer.Option(None, "--out", help="Output file path"),
    format: str = typer.Option(
        "toml", "--format", help="Export format (toml, yaml, json)"
    ),
    include_metadata: bool = typer.Option(
        False, "--include-metadata", help="Include metadata"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
) -> None:
    """Export profile to file.

    Exports a FullProfile configuration to a file in the specified format.

    Examples:
        sboxctl profile export home
        sboxctl profile export work --out work-config.yaml --format yaml

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

        # Determine output file
        if out is None:
            out = f"{name}.{format}"

        if verbose_flag:
            typer.echo(f"Exporting profile '{name}' to {out}")
            typer.echo(f"Format: {format}")

        # Prepare data for export
        export_data = profile.model_dump()

        # Remove metadata if not requested
        if not include_metadata:
            export_data.pop("created_at", None)
            export_data.pop("updated_at", None)

        # Export based on format
        if format.lower() == "json":
            with open(out, "w") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

        elif format.lower() == "yaml":
            try:
                import yaml

                with open(out, "w") as f:
                    yaml.dump(
                        export_data, f, default_flow_style=False, allow_unicode=True
                    )
            except ImportError:
                typer.echo(
                    "PyYAML not installed. Install with: pip install PyYAML", err=True
                )
                raise typer.Exit(1)

        elif format.lower() == "toml":
            try:
                from ....configs.toml_support import save_toml

                save_toml(export_data, Path(out))
            except Exception as e:
                typer.echo(f"Failed to save TOML: {e}", err=True)
                raise typer.Exit(1)

        else:
            typer.echo(f"Unsupported format: {format}", err=True)
            typer.echo("Supported formats: toml, yaml, json")
            raise typer.Exit(1)

        typer.echo(f"Profile '{name}' exported to {out}")

        if verbose_flag:
            typer.echo("Export details:")
            typer.echo(f"  - File: {out}")
            typer.echo(f"  - Format: {format}")
            typer.echo(f"  - Size: {Path(out).stat().st_size} bytes")
            typer.echo(f"  - Metadata included: {include_metadata}")

    except Exception as e:
        if verbose_flag:
            typer.echo(f"Error exporting profile: {e}", err=True)
        else:
            typer.echo("Error exporting profile. Use --verbose for details.", err=True)
        raise typer.Exit(1)
