"""Mode handlers for export command."""

import json
import os
import tempfile
from pathlib import Path
from typing import Optional

import typer

from sboxmgr.agent import AgentBridge, AgentNotAvailableError, ClientType
from sboxmgr.config.validation import validate_config_file
from sboxmgr.i18n.t import t
from sboxmgr.subscription.models import ClientProfile

from .config_generators import (
    generate_config_from_subscription,
    generate_profile_from_cli,
)
from .file_handlers import (
    create_backup_if_needed,
    determine_output_format,
    write_config_to_file,
)

# Import Phase 3 components
try:
    from sboxmgr.configs.models import FullProfile

    PHASE3_AVAILABLE = True
except ImportError:
    PHASE3_AVAILABLE = False
    FullProfile = None


def run_agent_check(config_file: str, agent_check: bool) -> bool:
    """Run agent validation check if requested.

    Args:
        config_file: Path to configuration file
        agent_check: Whether to run agent checks

    Returns:
        True if check passed or skipped, False if failed
    """
    if not agent_check:
        return True

    try:
        bridge = AgentBridge()
        if not bridge.is_available():
            typer.echo(
                "ℹ️  sboxagent not available - skipping external validation", err=True
            )
            return True

        # Validate config with agent
        response = bridge.validate(Path(config_file), client_type=ClientType.SING_BOX)

        if response.success:
            typer.echo("✅ External validation passed")
            if response.client_detected:
                typer.echo(f"   Detected client: {response.client_detected}")
            if response.client_version:
                typer.echo(f"   Client version: {response.client_version}")
            return True
        else:
            typer.echo("❌ External validation failed:", err=True)
            for error in response.errors:
                typer.echo(f"   • {error}", err=True)
            return False

    except AgentNotAvailableError:
        typer.echo(
            "ℹ️  sboxagent not available - skipping external validation", err=True
        )
        return True
    except Exception as e:
        typer.echo(f"⚠️  Agent check failed: {e}", err=True)
        return False


def handle_profile_generation(
    generate_profile: str, postprocessors: Optional[str], middleware: Optional[str]
) -> None:
    """Handle profile generation mode.

    Args:
        generate_profile: Output path for generated profile
        postprocessors: Comma-separated list of postprocessors
        middleware: Comma-separated list of middleware

    Raises:
        typer.Exit: Always exits with code 0
    """
    postprocessors_list = (
        [p.strip() for p in postprocessors.split(",") if p.strip()]
        if postprocessors
        else None
    )
    middleware_list = (
        [m.strip() for m in middleware.split(",") if m.strip()] if middleware else None
    )
    generate_profile_from_cli(postprocessors_list, middleware_list, generate_profile)
    raise typer.Exit(0)


def handle_validate_only_mode(output: str) -> None:
    """Handle validate-only mode.

    Args:
        output: Configuration file path to validate

    Raises:
        typer.Exit: On validation failure or success
    """
    config_file = output
    if not os.path.exists(config_file):
        typer.echo(f"❌ Configuration file not found: {config_file}", err=True)
        raise typer.Exit(1)

    try:
        validate_config_file(config_file)
        typer.echo(f"✅ Configuration is valid: {config_file}")
        raise typer.Exit(0)
    except typer.Exit:
        raise  # Re-raise to preserve exit code
    except Exception as e:
        typer.echo(f"❌ Configuration is invalid: {config_file}", err=True)
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


def process_export_mode(
    url: str,
    dry_run: bool,
    agent_check: bool,
    output: str,
    format: str,
    export_format: str,
    user_agent: Optional[str],
    no_user_agent: bool,
    debug: int,
    loaded_profile: Optional["FullProfile"],
    loaded_client_profile: Optional["ClientProfile"],
    postprocessors_list: Optional[list[str]],
    middleware_list: Optional[list[str]],
    backup: bool,
) -> None:
    """Process export mode (default, dry-run, or agent-check).

    Args:
        url: Subscription URL
        dry_run: Whether to run in dry-run mode
        agent_check: Whether to run agent check
        output: Output file path
        format: Output format
        export_format: Export format
        user_agent: Custom User-Agent
        no_user_agent: Whether to disable User-Agent
        debug: Debug level
        loaded_profile: Loaded profile
        loaded_client_profile: Loaded client profile
        postprocessors_list: List of postprocessors
        middleware_list: List of middleware
        backup: Whether to create backup

    Raises:
        typer.Exit: On processing failure
    """
    # Create backup if needed
    backup_file = None
    if not dry_run and not agent_check:
        backup_file = create_backup_if_needed(output, backup)

    # Determine output format
    output_format = determine_output_format(output, format)

    # Generate configuration
    config_data = generate_config_from_subscription(
        url=url,
        user_agent=user_agent,
        no_user_agent=no_user_agent,
        export_format=export_format,
        debug=debug,
        profile=loaded_profile,
        client_profile=loaded_client_profile,
    )

    # Handle different modes
    if dry_run:
        # Validate configuration without saving
        temp_file = f"{output}.tmp"
        try:
            write_config_to_file(config_data, temp_file, output_format)
            validate_config_file(temp_file)
            typer.echo("✅ Configuration is valid (dry-run)")
            os.remove(temp_file)
            raise typer.Exit(0)
        except Exception as e:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            typer.echo(f"❌ Configuration validation failed: {e}", err=True)
            raise typer.Exit(1)

    elif agent_check:
        # Check via sboxagent
        temp_file = f"{output}.tmp"
        try:
            write_config_to_file(config_data, temp_file, output_format)
            if run_agent_check(temp_file, agent_check):
                typer.echo("✅ Configuration passed agent check")
                raise typer.Exit(0)
            else:
                typer.echo("❌ Configuration failed agent check", err=True)
                raise typer.Exit(1)
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)

    else:
        # Default mode: save configuration
        try:
            write_config_to_file(config_data, output, output_format)
            typer.echo(f"✅ Configuration exported to: {output}")
            if backup_file:
                typer.echo(f"📦 Backup created: {backup_file}")
            raise typer.Exit(0)
        except Exception as e:
            typer.echo(f"❌ Failed to write configuration: {e}", err=True)
            raise typer.Exit(1)


def handle_legacy_modes(
    dry_run: bool,
    agent_check: bool,
    url: str,
    user_agent: Optional[str],
    no_user_agent: bool,
    export_format: str,
    debug: int,
    loaded_profile: Optional["FullProfile"],
    loaded_client_profile: Optional["ClientProfile"],
    output: str,
    format: str,
) -> None:
    """Handle legacy dry-run and agent-check modes from original implementation.

    Args:
        dry_run: Whether to run in dry-run mode
        agent_check: Whether to run agent check
        url: Subscription URL
        user_agent: Custom User-Agent
        no_user_agent: Whether to disable User-Agent
        export_format: Export format
        debug: Debug level
        loaded_profile: Loaded profile
        loaded_client_profile: Loaded client profile
        output: Output file path
        format: Output format

    Raises:
        typer.Exit: On processing failure or success
    """
    # Generate configuration from subscription
    config_data = generate_config_from_subscription(
        url,
        user_agent,
        no_user_agent,
        export_format,
        debug,
        loaded_profile,
        loaded_client_profile,
    )

    # Determine output format
    output_format = determine_output_format(output, format)

    # Handle dry-run mode
    if dry_run:
        typer.echo("🔍 " + t("cli.dry_run_mode"))
        with tempfile.NamedTemporaryFile(
            "w+", suffix=f".{output_format}", delete=False
        ) as tmp:
            temp_path = tmp.name
            if output_format == "toml":
                import toml

                tmp.write(toml.dumps(config_data))
            else:
                tmp.write(json.dumps(config_data, indent=2, ensure_ascii=False))

        try:
            validate_config_file(temp_path)
            typer.echo("✅ " + t("cli.dry_run_valid"))
            exit_code = 0
        except Exception as e:
            typer.echo(f"❌ {t('cli.config_invalid')}", err=True)
            typer.echo(f"Error: {e}", err=True)
            exit_code = 1
        finally:
            os.unlink(temp_path)
            typer.echo("🗑️  " + t("cli.temp_file_deleted"))

        raise typer.Exit(exit_code)

    # Handle agent-check mode
    if agent_check:
        typer.echo("🔍 Checking configuration via sboxagent...")
        with tempfile.NamedTemporaryFile("w+", suffix=".json", delete=False) as tmp:
            temp_path = tmp.name
            tmp.write(json.dumps(config_data, indent=2, ensure_ascii=False))

        try:
            success = run_agent_check(temp_path, True)
            exit_code = 0 if success else 1
        finally:
            os.unlink(temp_path)
            typer.echo("🗑️  Temporary file deleted")

        raise typer.Exit(exit_code)
