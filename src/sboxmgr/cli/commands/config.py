"""Configuration management CLI commands.

Provides commands for configuration debugging, validation, and management.
Implements the --dump-config quick win from Stage 3 acceptance criteria.
"""

import json
import sys
from pathlib import Path
from typing import Optional

import click
import yaml
from pydantic import ValidationError

from ...config import AppConfig, load_config, get_environment_info, ConfigValidationError


@click.group(name="config")
def config_group():
    """Configuration management commands."""
    pass


@config_group.command(name="dump")
@click.option(
    "--format",
    type=click.Choice(["yaml", "json", "env"]),
    default="yaml",
    help="Output format for configuration dump"
)
@click.option(
    "--include-defaults",
    is_flag=True,
    default=False,
    help="Include default values in output"
)
@click.option(
    "--include-env-info",
    is_flag=True,
    default=False,
    help="Include environment detection information"
)
@click.option(
    "--config-file",
    type=click.Path(exists=True, readable=True),
    help="Configuration file to load"
)
def dump_config(
    format: str,
    include_defaults: bool,
    include_env_info: bool,
    config_file: Optional[str]
):
    """Dump resolved configuration in specified format.
    
    This is the primary quick win indicator for Stage 3.
    Shows hierarchical configuration resolution: CLI > env > file > defaults.
    
    Examples:
        sboxctl config dump
        sboxctl config dump --format json
        sboxctl config dump --include-env-info
        SBOXMGR__LOGGING__LEVEL=DEBUG sboxctl config dump
    """
    try:
        # Load configuration with optional config file
        if config_file:
            config = load_config(config_file_path=config_file)
        else:
            config = AppConfig()
        
        # Prepare output data
        if include_defaults:
            config_data = config.dict(exclude_unset=False, exclude_none=False)
        else:
            config_data = config.dict(exclude_unset=True, exclude_none=True)
        
        # Add environment information if requested
        if include_env_info:
            config_data["_environment_info"] = get_environment_info()
        
        # Add metadata
        config_data["_metadata"] = {
            "config_file": config.config_file,
            "service_mode": config.service.service_mode,
            "container_mode": config.container_mode,
            "format_version": "1.0"
        }
        
        # Output in requested format
        if format == "yaml":
            yaml_output = yaml.dump(
                config_data,
                default_flow_style=False,
                sort_keys=True,
                indent=2
            )
            click.echo(yaml_output)
        
        elif format == "json":
            json_output = json.dumps(
                config_data,
                indent=2,
                sort_keys=True,
                default=str
            )
            click.echo(json_output)
        
        elif format == "env":
            # Output as environment variables
            _output_env_format(config_data, prefix="SBOXMGR")
    
    except ValidationError as e:
        click.echo(f"❌ Configuration validation error:", err=True)
        for error in e.errors():
            field = " -> ".join(str(x) for x in error["loc"])
            click.echo(f"  {field}: {error['msg']}", err=True)
        sys.exit(1)
    
    except ConfigValidationError as e:
        click.echo(f"❌ Configuration file error: {e}", err=True)
        sys.exit(1)
    
    except Exception as e:
        click.echo(f"❌ Unexpected error: {e}", err=True)
        sys.exit(1)


@config_group.command(name="validate")
@click.argument("config_file", type=click.Path(exists=True, readable=True))
def validate_config(config_file: str):
    """Validate configuration file syntax and values.
    
    Checks configuration file for:
    - Valid TOML/YAML syntax
    - Schema compliance
    - Value validation
    - Environment variable resolution
    """
    try:
        config = load_config(config_file_path=config_file)
        click.echo(f"✅ Configuration file '{config_file}' is valid")
        
        # Show key configuration values
        click.echo("\nKey settings:")
        click.echo(f"  Service mode: {config.service.service_mode}")
        click.echo(f"  Log level: {config.logging.level}")
        click.echo(f"  Log format: {config.logging.format}")
        click.echo(f"  Log sinks: {', '.join(config.logging.sinks)}")
        
    except ValidationError as e:
        click.echo(f"❌ Configuration validation failed:", err=True)
        for error in e.errors():
            field = " -> ".join(str(x) for x in error["loc"])
            click.echo(f"  {field}: {error['msg']}", err=True)
        sys.exit(1)
    
    except Exception as e:
        click.echo(f"❌ Error validating configuration: {e}", err=True)
        sys.exit(1)


@config_group.command(name="schema")
@click.option(
    "--output",
    type=click.Path(),
    help="Output file for JSON schema (default: stdout)"
)
def generate_schema(output: Optional[str]):
    """Generate JSON schema for configuration validation.
    
    Useful for:
    - IDE autocompletion
    - Configuration file validation
    - Documentation generation
    """
    try:
        config = AppConfig()
        schema = config.generate_json_schema()
        
        schema_json = json.dumps(schema, indent=2, sort_keys=True)
        
        if output:
            with open(output, 'w') as f:
                f.write(schema_json)
            click.echo(f"✅ JSON schema written to {output}")
        else:
            click.echo(schema_json)
    
    except Exception as e:
        click.echo(f"❌ Error generating schema: {e}", err=True)
        sys.exit(1)


@config_group.command(name="env-info")
def environment_info():
    """Show environment detection information.
    
    Displays detailed information about:
    - Service mode detection
    - Container environment
    - Systemd availability
    - Development environment
    """
    try:
        env_info = get_environment_info()
        
        click.echo("🔍 Environment Detection Results:")
        click.echo()
        
        # Service mode detection
        service_mode = "✅ Enabled" if env_info["service_mode"] else "❌ Disabled"
        click.echo(f"Service Mode: {service_mode}")
        
        # Container detection
        container = "✅ Detected" if env_info["container_environment"] else "❌ Not detected"
        click.echo(f"Container Environment: {container}")
        
        # Systemd detection
        systemd = "✅ Available" if env_info["systemd_environment"] else "❌ Not available"
        click.echo(f"Systemd Environment: {systemd}")
        
        # Development detection
        dev = "✅ Detected" if env_info["development_environment"] else "❌ Not detected"
        click.echo(f"Development Environment: {dev}")
        
        click.echo()
        click.echo("📋 Environment Variables:")
        for key, value in env_info["environment_variables"].items():
            if value:
                click.echo(f"  {key}: {value}")
        
        click.echo()
        click.echo("🔧 Process Information:")
        for key, value in env_info["process_info"].items():
            click.echo(f"  {key}: {value}")
        
        click.echo()
        click.echo("📁 File Indicators:")
        for path, exists in env_info["file_indicators"].items():
            status = "✅ Exists" if exists else "❌ Missing"
            click.echo(f"  {path}: {status}")
    
    except Exception as e:
        click.echo(f"❌ Error getting environment info: {e}", err=True)
        sys.exit(1)


def _output_env_format(data: dict, prefix: str = "", parent_key: str = ""):
    """Output configuration in environment variable format.
    
    Converts nested configuration to SBOXMGR__SECTION__KEY format.
    """
    for key, value in data.items():
        if key.startswith("_"):  # Skip metadata
            continue
            
        env_key = f"{prefix}__{key.upper()}" if prefix else key.upper()
        
        if isinstance(value, dict):
            _output_env_format(value, env_key, key)
        elif isinstance(value, list):
            # Convert lists to comma-separated strings
            env_value = ",".join(str(v) for v in value)
            click.echo(f"{env_key}={env_value}")
        else:
            click.echo(f"{env_key}={value}")


# Add to main CLI
def register_config_commands(cli_app):
    """Register configuration commands with main CLI application."""
    cli_app.add_command(config_group) 