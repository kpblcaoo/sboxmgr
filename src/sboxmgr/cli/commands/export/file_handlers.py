"""File handling utilities for export command."""

import json
import os
import shutil
from pathlib import Path
from typing import Optional

import typer

from sboxmgr.i18n.t import t
from sboxmgr.utils.env import get_backup_file


def determine_output_format(output_file: str, format_flag: str) -> str:
    """Determine output format based on file extension and format flag.
    
    Args:
        output_file: Output file path
        format_flag: Format flag value (json, toml, auto)
        
    Returns:
        Determined format (json or toml)
    """
    if format_flag == "auto":
        ext = Path(output_file).suffix.lower()
        if ext == ".toml":
            return "toml"
        else:
            return "json"
    return format_flag


def create_backup_if_needed(output_file: str, backup: bool) -> Optional[str]:
    """Create backup of existing config file if requested.
    
    Args:
        output_file: Path to output file
        backup: Whether to create backup
        
    Returns:
        Path to backup file if created, None otherwise
    """
    if not backup or not os.path.exists(output_file):
        return None
        
    backup_file = get_backup_file()
    if backup_file:
        shutil.copy2(output_file, backup_file)
        typer.echo(f"📦 Backup created: {backup_file}")
        return backup_file
    return None


def write_config_to_file(config_data: dict, output_file: str, output_format: str) -> None:
    """Write configuration to output file in specified format.
    
    Args:
        config_data: Configuration data to write
        output_file: Output file path  
        output_format: Output format (json or toml)
        
    Raises:
        typer.Exit: If writing fails
    """
    try:
        # Ensure output directory exists
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            
        if output_format == "toml":
            import toml
            config_content = toml.dumps(config_data)
        else:
            config_content = json.dumps(config_data, indent=2, ensure_ascii=False)
            
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(config_content)
            
        typer.echo(f"✅ Configuration written to: {output_file}")
        
    except Exception as e:
        typer.echo(f"❌ {t('cli.error_config_update')}: {e}", err=True)
        raise typer.Exit(1)
