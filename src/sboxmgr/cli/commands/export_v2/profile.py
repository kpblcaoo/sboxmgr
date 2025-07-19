"""Export profile subcommand for sboxmgr (ADR-0020).

This module provides the `export profile` command for exporting optimized
FullProfile configurations.
"""

import json
from pathlib import Path
from typing import Optional

import typer

from ....configs.profile_manager import ProfileManager
from ....utils.cli_common import get_verbose_flag


def export_profile_config(
    profile_name: str = typer.Argument(..., help="Profile name to export"),
    output: Optional[str] = typer.Option(None, "--output", help="Output file path"),
    out_format: str = typer.Option(
        "toml", "--out-format", help="Export format: toml, yaml, json"
    ),
    optimize: bool = typer.Option(
        False, "--optimize", help="Optimize profile for export"
    ),
    no_optimize: bool = typer.Option(
        False, "--no-optimize", help="Disable profile optimization"
    ),
    include_metadata: bool = typer.Option(
        False, "--include-metadata", help="Include metadata in export"
    ),
    postprocessors: str = typer.Option(
        None,
        "--postprocessors",
        help="Comma-separated list of postprocessors to add",
    ),
    middleware: str = typer.Option(
        None,
        "--middleware",
        help="Comma-separated list of middleware to add",
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    ctx: typer.Context = None,
) -> None:
    """Export optimized FullProfile configuration.

    Exports a FullProfile configuration optimized for sharing or deployment.
    This command adapts the existing profile export functionality to work with
    the new two-layer architecture.

    Examples:
        sboxctl export profile home
        sboxctl export profile work --output work-deploy.toml --out-format toml
        sboxctl export profile home --postprocessors geo_filter,tag_filter

    """
    # Get global flags from context
    global_verbose = ctx.obj.get("verbose", False) if ctx and ctx.obj else False

    verbose_flag = get_verbose_flag(verbose or global_verbose)
    manager = ProfileManager()

    # Handle optimize flags - optimize by default unless no_optimize is set
    should_optimize = not no_optimize

    # Check for conflicting flags
    if include_metadata and should_optimize:
        typer.echo("⚠️  Warning: --include-metadata conflicts with --optimize", err=True)
        typer.echo("   Optimization will be disabled to include metadata", err=True)
        should_optimize = False

    try:
        # Get profile
        profile = manager.get_profile(profile_name)
        if not profile:
            typer.echo(f"Profile '{profile_name}' not found.", err=True)
            typer.echo("Use 'sboxctl profile list' to see available profiles.")
            raise typer.Exit(1)

        # Determine output file
        if output is None:
            output = f"{profile_name}-export.{out_format}"

        if verbose_flag:
            typer.echo(f"Exporting optimized profile: {profile_name}")
            typer.echo(f"Output: {output}")
            typer.echo(f"Format: {out_format}")
            typer.echo(f"Optimize: {should_optimize}")

        # Prepare profile data for export
        export_data = profile.model_dump()

        # Remove metadata if not requested
        if not include_metadata:
            export_data.pop("created_at", None)
            export_data.pop("updated_at", None)

        # Add postprocessors and middleware if provided
        if postprocessors or middleware:
            if "metadata" not in export_data:
                export_data["metadata"] = {}

            metadata = export_data["metadata"]

            # Add postprocessors
            if postprocessors:
                postprocessors_list = [
                    p.strip() for p in postprocessors.split(",") if p.strip()
                ]
                metadata["postprocessors"] = {
                    "chain": [
                        {"type": proc, "config": {}} for proc in postprocessors_list
                    ],
                    "execution_mode": "sequential",
                    "error_strategy": "continue",
                }

            # Add middleware
            if middleware:
                middleware_list = [
                    m.strip() for m in middleware.split(",") if m.strip()
                ]
                metadata["middleware"] = {
                    "chain": [{"type": mw, "config": {}} for mw in middleware_list]
                }

        # Optimize profile if requested
        if should_optimize:
            # Remove unnecessary fields for deployment
            export_data.pop("created_at", None)
            export_data.pop("updated_at", None)

            # Ensure required fields are present
            if "export" not in export_data:
                export_data["export"] = {
                    "format": "sing-box",
                    "output_file": "config.json",
                }

        # Export based on format
        if out_format.lower() == "json":
            with open(output, "w") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

        elif out_format.lower() == "yaml":
            try:
                import yaml

                with open(output, "w") as f:
                    yaml.dump(
                        export_data, f, default_flow_style=False, allow_unicode=True
                    )
            except ImportError:
                typer.echo(
                    "PyYAML not installed. Install with: pip install PyYAML", err=True
                )
                raise typer.Exit(1)

        elif out_format.lower() == "toml":
            try:
                from ....configs.toml_support import save_toml

                save_toml(export_data, Path(output))
            except Exception as e:
                typer.echo(f"Failed to save TOML: {e}", err=True)
                raise typer.Exit(1)

        else:
            typer.echo(f"Unsupported format: {out_format}", err=True)
            typer.echo("Supported formats: toml, yaml, json")
            raise typer.Exit(1)

        typer.echo(f"✅ Profile '{profile_name}' exported to {output}")

        if verbose_flag:
            file_size = Path(output).stat().st_size
            typer.echo("Export details:")
            typer.echo(f"  - File: {output}")
            typer.echo(f"  - Format: {out_format}")
            typer.echo(f"  - Size: {file_size} bytes")
            typer.echo(f"  - Optimized: {should_optimize}")
            typer.echo(f"  - Metadata included: {include_metadata}")
            if postprocessors:
                typer.echo(f"  - Postprocessors added: {postprocessors}")
            if middleware:
                typer.echo(f"  - Middleware added: {middleware}")

    except Exception as e:
        if verbose_flag:
            typer.echo(f"Error exporting profile: {e}", err=True)
        else:
            typer.echo("Error exporting profile. Use --verbose for details.", err=True)
        raise typer.Exit(1)
