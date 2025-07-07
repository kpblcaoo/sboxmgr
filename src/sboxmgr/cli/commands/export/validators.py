"""Validators for export command parameters."""

import re
from typing import List, Optional

import typer

from sboxmgr.i18n.t import t

from .constants import (
    ALLOWED_MIDDLEWARE,
    ALLOWED_POSTPROCESSORS,
    VALID_FINAL_ROUTES,
    VALID_OUTBOUND_TYPES,
)

# Valid format values
VALID_OUTPUT_FORMATS = {"json", "toml", "auto"}
VALID_EXPORT_FORMATS = {"singbox", "clash", "v2ray"}


def validate_flag_combinations(
    dry_run: bool,
    agent_check: bool,
    validate_only: bool,
    url: Optional[str],
    user_agent: Optional[str],
    no_user_agent: bool,
    output: Optional[str],
) -> None:
    """Validate flag combinations for mutual exclusivity.

    Args:
        dry_run: Dry run mode flag
        agent_check: Agent check mode flag
        validate_only: Validate only mode flag
        url: Subscription URL
        user_agent: Custom User-Agent header
        no_user_agent: Disable User-Agent header
        output: Output file path

    Raises:
        typer.Exit: If invalid flag combination detected
    """
    # Existing validations
    if dry_run and agent_check:
        typer.echo(
            "❌ Error: --dry-run and --agent-check are mutually exclusive", err=True
        )
        raise typer.Exit(1)

    if validate_only and url:
        typer.echo(
            "❌ Error: --validate-only cannot be used with subscription URL", err=True
        )
        raise typer.Exit(1)

    if validate_only and (dry_run or agent_check):
        typer.echo(
            "❌ Error: --validate-only cannot be used with --dry-run or --agent-check",
            err=True,
        )
        raise typer.Exit(1)

    # NEW: user-agent + no-user-agent conflict
    if user_agent and no_user_agent:
        typer.echo(
            "❌ Error: --user-agent and --no-user-agent are mutually exclusive",
            err=True,
        )
        raise typer.Exit(1)

    # NEW: warnings for ignored output
    if output and (dry_run or agent_check):
        mode = "dry-run" if dry_run else "agent-check"
        typer.echo(f"⚠️  Warning: --output is ignored in --{mode} mode", err=True)


def validate_postprocessors(processors: List[str]) -> None:
    """Validate postprocessor names.

    Args:
        processors: List of postprocessor names to validate

    Raises:
        typer.Exit: If invalid postprocessor names found
    """
    if invalid := [x for x in processors if x not in ALLOWED_POSTPROCESSORS]:
        typer.echo(
            f"❌ {t('cli.error.unknown_postprocessors').format(invalid=', '.join(invalid))}",
            err=True,
        )
        typer.echo(
            f"💡 {t('cli.error.available_postprocessors').format(available=', '.join(ALLOWED_POSTPROCESSORS))}",
            err=True,
        )
        raise typer.Exit(1)


def validate_middleware(middleware: List[str]) -> None:
    """Validate middleware names.

    Args:
        middleware: List of middleware names to validate

    Raises:
        typer.Exit: If invalid middleware names found
    """
    if invalid := [x for x in middleware if x not in ALLOWED_MIDDLEWARE]:
        typer.echo(
            f"❌ {t('cli.error.unknown_middleware').format(invalid=', '.join(invalid))}",
            err=True,
        )
        typer.echo(
            f"💡 {t('cli.error.available_middleware').format(available=', '.join(ALLOWED_MIDDLEWARE))}",
            err=True,
        )
        raise typer.Exit(1)


def validate_final_route(final_route: str) -> None:
    """Validate final route value.

    Args:
        final_route: Final route value to validate

    Raises:
        typer.Exit: If final route is invalid
    """
    # Check if it's a valid predefined route
    if final_route in VALID_FINAL_ROUTES:
        return

    # Check if it's a valid outbound tag (alphanumeric + hyphen/underscore)
    if re.match(r"^[a-zA-Z0-9_-]+$", final_route):
        return

    typer.echo(f"❌ Invalid final route: {final_route}", err=True)
    typer.echo(
        f"💡 Valid values: {', '.join(VALID_FINAL_ROUTES)} or a valid outbound tag",
        err=True,
    )
    raise typer.Exit(1)


def validate_exclude_outbounds(exclude_outbounds: str) -> None:
    """Validate exclude outbounds list.

    Args:
        exclude_outbounds: Comma-separated list of outbound types to validate

    Raises:
        typer.Exit: If exclude outbounds contains invalid values
    """
    exclude_list = [o.strip() for o in exclude_outbounds.split(",") if o.strip()]

    invalid_types = []
    for outbound_type in exclude_list:
        if outbound_type not in VALID_OUTBOUND_TYPES:
            invalid_types.append(outbound_type)

    if invalid_types:
        typer.echo(f"❌ Invalid outbound types: {', '.join(invalid_types)}", err=True)
        typer.echo(f"💡 Valid types: {', '.join(VALID_OUTBOUND_TYPES)}", err=True)
        raise typer.Exit(1)


def validate_and_parse_cli_parameters(
    postprocessors: Optional[str],
    middleware: Optional[str],
    final_route: Optional[str],
    exclude_outbounds: Optional[str],
) -> tuple[Optional[list[str]], Optional[list[str]]]:
    """Validate and parse CLI parameters.

    Args:
        postprocessors: Comma-separated list of postprocessors
        middleware: Comma-separated list of middleware
        final_route: Final routing destination
        exclude_outbounds: Comma-separated list of outbound types to exclude

    Returns:
        Tuple of (postprocessors_list, middleware_list)

    Raises:
        typer.Exit: On validation failure
    """
    postprocessors_list = None
    middleware_list = None

    if postprocessors:
        postprocessors_list = [
            p.strip() for p in postprocessors.split(",") if p.strip()
        ]
        if postprocessors_list:
            validate_postprocessors(postprocessors_list)

    if middleware:
        middleware_list = [m.strip() for m in middleware.split(",") if m.strip()]
        if middleware_list:
            validate_middleware(middleware_list)

    if final_route:
        validate_final_route(final_route)

    if exclude_outbounds:
        validate_exclude_outbounds(exclude_outbounds)

    return postprocessors_list, middleware_list


def validate_output_format(format_value: str) -> None:
    """Validate output format value.

    Args:
        format_value: Output format to validate

    Raises:
        typer.Exit: If format is invalid
    """
    if format_value not in VALID_OUTPUT_FORMATS:
        typer.echo(f"❌ Invalid output format: {format_value}", err=True)
        typer.echo(
            f"💡 Valid formats: {', '.join(sorted(VALID_OUTPUT_FORMATS))}", err=True
        )
        raise typer.Exit(1)


def validate_export_format(export_format: str) -> None:
    """Validate export format value.

    Args:
        export_format: Export format to validate

    Raises:
        typer.Exit: If export format is invalid
    """
    if export_format not in VALID_EXPORT_FORMATS:
        typer.echo(f"❌ Invalid export format: {export_format}", err=True)
        typer.echo(
            f"💡 Valid formats: {', '.join(sorted(VALID_EXPORT_FORMATS))}", err=True
        )
        raise typer.Exit(1)
