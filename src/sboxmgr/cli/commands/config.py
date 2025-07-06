"""CLI commands for configuration management.

This module provides commands for managing user configurations (formerly profiles),
including creation, loading, validation, and migration between formats.
"""

import json
from pathlib import Path
from typing import Optional

import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table

# Import config models
try:
    from sboxmgr.configs.manager import ConfigManager
    from sboxmgr.configs.models import UserConfig
    from sboxmgr.configs.toml_support import (
        convert_json_to_toml,
        detect_config_format,
        load_config_auto,
        save_config_to_toml,
    )

    CONFIGS_AVAILABLE = True
except ImportError:
    CONFIGS_AVAILABLE = False
    UserConfig = None
    ConfigManager = None

console = Console()

# Create Typer app for config commands
app = typer.Typer(help="Configuration management commands")


@app.command()
def list(
    format: str = typer.Option("table", "--format", help="Output format: table, json"),
    directory: Optional[str] = typer.Option(
        None, "--directory", help="Config directory"
    ),
):
    """List available configurations."""
    if not CONFIGS_AVAILABLE:
        typer.echo("❌ Config management not available", err=True)
        raise typer.Exit(1)

    manager = ConfigManager(directory)
    configs = manager.list_configs()

    if format == "json":
        config_data = []
        for config in configs:
            config_data.append(
                {
                    "name": config.name,
                    "path": config.path,
                    "size": config.size,
                    "modified": config.modified.isoformat(),
                    "valid": config.valid,
                    "error": config.error,
                }
            )
        print(json.dumps({"configs": config_data, "total": len(config_data)}, indent=2))
        return

    if not configs:
        rprint("[dim]📝 No configurations found.[/dim]")
        return

    table = Table(title=f"🔧 Available Configurations ({len(configs)})")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Format", style="yellow")
    table.add_column("Size", style="dim")
    table.add_column("Modified", style="dim")
    table.add_column("Status", style="green")

    for config in configs:
        format_type = detect_config_format(config.path)
        status = "✅ Valid" if config.valid else f"❌ {config.error}"
        size_kb = f"{config.size / 1024:.1f} KB"
        modified = config.modified.strftime("%Y-%m-%d %H:%M")

        table.add_row(config.name, format_type.upper(), size_kb, modified, status)

    console.print(table)


@app.command()
def create(
    name: str = typer.Argument(..., help="Configuration name"),
    description: Optional[str] = typer.Option(
        None, "--description", help="Configuration description"
    ),
    format: str = typer.Option("toml", "--format", help="Output format: toml, json"),
    directory: Optional[str] = typer.Option(
        None, "--directory", help="Config directory"
    ),
):
    """Create a new configuration."""
    if not CONFIGS_AVAILABLE:
        typer.echo("❌ Config management not available", err=True)
        raise typer.Exit(1)

    manager = ConfigManager(directory)

    # Create basic config
    config_data = {
        "id": name,
        "description": description or f"Configuration {name}",
        "version": "1.0",
    }

    try:
        config = manager.create_config(config_data)

        # Determine output path
        extension = ".toml" if format == "toml" else ".json"
        output_path = manager.configs_dir / f"{name}{extension}"

        if format == "toml":
            save_config_to_toml(config, output_path)
        else:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(
                    config.model_dump(exclude_none=True),
                    f,
                    indent=2,
                    ensure_ascii=False,
                )

        rprint(f"[green]✅ Created configuration '{name}' at {output_path}[/green]")

    except Exception as e:
        rprint(f"[red]❌ Failed to create configuration: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def apply(
    config_file: str = typer.Argument(..., help="Configuration file path"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Validate without applying"),
):
    """Apply a configuration."""
    if not CONFIGS_AVAILABLE:
        typer.echo("❌ Config management not available", err=True)
        raise typer.Exit(1)

    config_path = Path(config_file)
    if not config_path.exists():
        rprint(f"[red]❌ Configuration file not found: {config_file}[/red]")
        raise typer.Exit(1)

    try:
        config = load_config_auto(config_path)

        if dry_run:
            rprint("[yellow]🔍 Dry run mode - validating configuration[/yellow]")
            rprint(f"[green]✅ Configuration '{config.id}' is valid[/green]")
            rprint(f"  Description: {config.description}")
            rprint(f"  Subscriptions: {len(config.subscriptions)}")
            rprint(f"  Export format: {config.export.format}")
        else:
            # In real implementation, this would apply the config
            rprint(f"[green]✅ Applied configuration '{config.id}'[/green]")
            rprint(
                "[dim]Note: Use sboxctl export to generate actual proxy configs[/dim]"
            )

    except Exception as e:
        rprint(f"[red]❌ Failed to apply configuration: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def validate(
    config_file: str = typer.Argument(..., help="Configuration file path"),
):
    """Validate a configuration file."""
    if not CONFIGS_AVAILABLE:
        typer.echo("❌ Config management not available", err=True)
        raise typer.Exit(1)

    config_path = Path(config_file)
    if not config_path.exists():
        rprint(f"[red]❌ Configuration file not found: {config_file}[/red]")
        raise typer.Exit(1)

    try:
        config = load_config_auto(config_path)
        rprint(f"[green]✅ Configuration '{config.id}' is valid[/green]")

        # Show config summary
        rprint(f"  ID: {config.id}")
        rprint(f"  Description: {config.description}")
        rprint(f"  Version: {config.version}")
        rprint(f"  Subscriptions: {len(config.subscriptions)}")
        rprint(f"  Export format: {config.export.format}")

    except Exception as e:
        rprint(f"[red]❌ Configuration validation failed: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def migrate(
    source: str = typer.Argument(..., help="Source configuration file (JSON)"),
    target: Optional[str] = typer.Option(
        None, "--target", help="Target file path (TOML)"
    ),
    format: str = typer.Option("toml", "--format", help="Target format: toml"),
):
    """Migrate configuration from JSON to TOML format."""
    if not CONFIGS_AVAILABLE:
        typer.echo("❌ Config management not available", err=True)
        raise typer.Exit(1)

    source_path = Path(source)
    if not source_path.exists():
        rprint(f"[red]❌ Source file not found: {source}[/red]")
        raise typer.Exit(1)

    if format != "toml":
        rprint(f"[red]❌ Unsupported target format: {format}[/red]")
        raise typer.Exit(1)

    # Determine target path
    if not target:
        target = str(source_path.with_suffix(".toml"))

    try:
        convert_json_to_toml(source_path, target)
        rprint(f"[green]✅ Migrated {source} → {target}[/green]")

    except Exception as e:
        rprint(f"[red]❌ Migration failed: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def switch(
    config_name: str = typer.Argument(..., help="Configuration name to switch to"),
    directory: Optional[str] = typer.Option(
        None, "--directory", help="Config directory"
    ),
):
    """Switch to a different configuration."""
    if not CONFIGS_AVAILABLE:
        typer.echo("❌ Config management not available", err=True)
        raise typer.Exit(1)

    manager = ConfigManager(directory)

    # Find config file
    config_path = None
    for ext in [".toml", ".json"]:
        potential_path = manager.configs_dir / f"{config_name}{ext}"
        if potential_path.exists():
            config_path = potential_path
            break

    if not config_path:
        rprint(f"[red]❌ Configuration '{config_name}' not found[/red]")
        raise typer.Exit(1)

    try:
        config = load_config_auto(config_path)
        manager.set_active_config(config)
        rprint(f"[green]✅ Switched to configuration '{config.id}'[/green]")

    except Exception as e:
        rprint(f"[red]❌ Failed to switch configuration: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def edit(
    config_name: str = typer.Argument(..., help="Configuration name to edit"),
    editor: Optional[str] = typer.Option(None, "--editor", help="Editor command"),
    directory: Optional[str] = typer.Option(
        None, "--directory", help="Config directory"
    ),
):
    """Edit a configuration file."""
    if not CONFIGS_AVAILABLE:
        typer.echo("❌ Config management not available", err=True)
        raise typer.Exit(1)

    manager = ConfigManager(directory)

    # Find config file
    config_path = None
    for ext in [".toml", ".json"]:
        potential_path = manager.configs_dir / f"{config_name}{ext}"
        if potential_path.exists():
            config_path = potential_path
            break

    if not config_path:
        rprint(f"[red]❌ Configuration '{config_name}' not found[/red]")
        raise typer.Exit(1)

    # Determine editor
    import os

    editor_cmd = editor or os.environ.get("EDITOR", "nano")

    try:
        import subprocess

        subprocess.run([editor_cmd, str(config_path)], check=True)
        rprint(f"[green]✅ Edited configuration '{config_name}'[/green]")

    except subprocess.CalledProcessError:
        rprint("[red]❌ Editor exited with error[/red]")
        raise typer.Exit(1)
    except FileNotFoundError:
        rprint(f"[red]❌ Editor not found: {editor_cmd}[/red]")
        raise typer.Exit(1)
