"""Export dry-run subcommand for sboxmgr (ADR-0020).

This module provides the `export dry-run` command for testing configurations
without saving them to disk.
"""

import os
import tempfile
from pathlib import Path

import typer

from sboxmgr.config.validation import validate_config_file

from ....configs.profile_manager import ProfileManager
from ....utils.cli_common import get_verbose_flag
from ..export.config_generators import generate_config_from_subscription
from ..export.file_handlers import determine_output_format, write_config_to_file
from ..export.validators import (
    validate_and_parse_cli_parameters,
    validate_export_format,
    validate_output_format,
)


def dry_run_config(
    profile_name: str = typer.Argument(..., help="Profile name to test"),
    url: str = typer.Option(
        None, "-u", "--url", help="Subscription URL (overrides profile URL)"
    ),
    out_format: str = typer.Option(
        "json", "--out-format", help="Output format: json, toml, auto"
    ),
    target: str = typer.Option(
        "singbox", "--target", help="Target format: singbox, clash"
    ),
    user_agent: str = typer.Option(
        None, "--user-agent", help="Override User-Agent for subscription fetcher"
    ),
    no_user_agent: bool = typer.Option(
        False, "--no-user-agent", help="Do not send User-Agent header"
    ),
    postprocessors: str = typer.Option(
        None,
        "--postprocessors",
        help="Comma-separated list of postprocessors (geo_filter,tag_filter,latency_sort)",
    ),
    middleware: str = typer.Option(
        None,
        "--middleware",
        help="Comma-separated list of middleware (logging,enrichment)",
    ),
    agent_check: bool = typer.Option(
        False, "--agent-check", help="Check configuration via sboxagent"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    ctx: typer.Context = None,
) -> None:
    """Test configuration generation without saving.

    Generates a configuration from a profile and validates it without
    saving to disk. Useful for testing and validation.
    This command adapts the existing dry-run functionality to work with
    the new two-layer architecture.

    Examples:
        sboxctl export dry-run home
        sboxctl export dry-run work --out-format toml --target clash
        sboxctl export dry-run home --agent-check

    """
    # Get global flags from context
    global_verbose = ctx.obj.get("verbose", False) if ctx and ctx.obj else False

    verbose_flag = get_verbose_flag(verbose or global_verbose)
    manager = ProfileManager()

    try:
        # Get profile
        profile = manager.get_profile(profile_name)
        if not profile:
            typer.echo(f"Profile '{profile_name}' not found.", err=True)
            typer.echo("Use 'sboxctl profile list' to see available profiles.")
            raise typer.Exit(1)

        if verbose_flag:
            typer.echo(f"Testing configuration generation for profile: {profile_name}")
            typer.echo(f"Output format: {out_format}")
            typer.echo(f"Target format: {target}")

        # Validate format values
        validate_output_format(out_format)
        validate_export_format(target)

        # Get subscription URL from profile or use provided URL
        subscription_url = url
        if not subscription_url:
            # Extract URL from profile subscriptions
            if not profile.subscriptions:
                typer.echo("No subscription URL found in profile.", err=True)
                typer.echo("Use --url to specify a subscription URL.")
                raise typer.Exit(1)

            # Use the first subscription URL
            subscription_url = profile.subscriptions[0].url
            if verbose_flag:
                typer.echo(f"Using subscription URL from profile: {subscription_url}")

        # Validate and parse CLI parameters
        postprocessors_list, middleware_list = validate_and_parse_cli_parameters(
            postprocessors, middleware, None, None
        )

        # Generate configuration using existing logic
        config_data = generate_config_from_subscription(
            url=subscription_url,
            user_agent=user_agent,
            no_user_agent=no_user_agent,
            export_format=target,
            debug=1 if verbose_flag else 0,
            profile=profile,
            client_profile=None,  # Will be extracted from profile if needed
        )

        # Create temporary file for validation
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as tmp_file:
            temp_file_path = tmp_file.name

        try:
            # Determine output format and write to temp file
            output_format = determine_output_format("temp.json", out_format)
            write_config_to_file(config_data, temp_file_path, output_format)

            # Validate the generated configuration
            validate_config_file(temp_file_path)
            typer.echo("✅ Configuration is valid (dry-run)")

            # Run agent check if requested
            if agent_check:
                from ..export.mode_handlers import run_agent_check

                if not run_agent_check(temp_file_path, agent_check):
                    raise typer.Exit(1)

            if verbose_flag:
                file_size = Path(temp_file_path).stat().st_size
                typer.echo("Dry-run details:")
                typer.echo(f"  - Profile: {profile.id}")
                typer.echo(f"  - Subscription URL: {subscription_url}")
                typer.echo(f"  - Target format: {target}")
                typer.echo(f"  - Output format: {output_format}")
                typer.echo(f"  - Generated size: {file_size} bytes")
                typer.echo("  - Validation: passed")
                if agent_check:
                    typer.echo("  - Agent check: passed")

        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except OSError:
                pass

    except Exception as e:
        if verbose_flag:
            typer.echo(f"Error in dry-run: {e}", err=True)
        else:
            typer.echo("Error in dry-run. Use --verbose for details.", err=True)
        raise typer.Exit(1)
