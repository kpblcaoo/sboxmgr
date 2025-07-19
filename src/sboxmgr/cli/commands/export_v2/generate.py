"""Export generate subcommand for sboxmgr (ADR-0020).

This module provides the `export generate` command for generating ClientConfig
from FullProfile configurations.
"""

from pathlib import Path

import typer

from ....configs.profile_manager import ProfileManager
from ....utils.cli_common import get_verbose_flag
from ..export.config_generators import generate_config_from_subscription
from ..export.file_handlers import (
    create_backup_if_needed,
    determine_output_format,
    write_config_to_file,
)
from ..export.validators import (
    validate_and_parse_cli_parameters,
    validate_export_format,
    validate_output_format,
)


def generate_config(
    profile_name: str = typer.Argument(
        ..., help="Profile name to generate config from"
    ),
    url: str = typer.Option(
        None, "-u", "--url", help="Subscription URL (overrides profile URL)"
    ),
    output: str = typer.Option("config.json", "--output", help="Output file path"),
    out_format: str = typer.Option(
        "json", "--out-format", help="Output format: json, toml, auto"
    ),
    target: str = typer.Option(
        "singbox", "--target", help="Target format: singbox, clash"
    ),
    backup: bool = typer.Option(
        False,
        "--backup",
        help="Create backup before overwriting existing file (creates <output>.bak)",
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
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    ctx: typer.Context = None,
) -> None:
    """Generate ClientConfig from FullProfile.

    Generates a machine-readable ClientConfig from a user-friendly FullProfile.
    This command adapts the existing export functionality to work with the new
    two-layer architecture.

    Examples:
        sboxctl export generate home
        sboxctl export generate work --output work-config.json --out-format json
        sboxctl export generate home --url https://example.com/subscription

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
            typer.echo(f"Generating config from profile: {profile_name}")
            typer.echo(f"Output: {output}")
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

        # Create backup if requested
        create_backup_if_needed(output, backup)

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

        # Determine output format and write
        output_format = determine_output_format(output, out_format)
        write_config_to_file(config_data, output, output_format)

        typer.echo(f"✅ Configuration generated successfully: {output}")

        if verbose_flag:
            typer.echo("Configuration details:")
            typer.echo(f"  - Profile: {profile.id}")
            typer.echo(f"  - Subscription URL: {subscription_url}")
            typer.echo(f"  - Target format: {target}")
            typer.echo(f"  - Output format: {output_format}")
            typer.echo(f"  - File size: {Path(output).stat().st_size} bytes")

    except Exception as e:
        if verbose_flag:
            typer.echo(f"Error generating config: {e}", err=True)
        else:
            typer.echo("Error generating config. Use --verbose for details.", err=True)
        raise typer.Exit(1)
