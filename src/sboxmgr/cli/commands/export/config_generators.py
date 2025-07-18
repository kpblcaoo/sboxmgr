"""Configuration generators for export command."""

import json
from typing import Any, Optional

import typer

from sboxmgr.export.export_manager import ExportManager
from sboxmgr.i18n.t import t
from sboxmgr.subscription.manager import SubscriptionManager
from sboxmgr.subscription.models import (
    ClientProfile,
    PipelineContext,
    SubscriptionSource,
)

from .validators import validate_middleware, validate_postprocessors

# Import Phase 3 components
try:
    from sboxmgr.configs.models import FullProfile

except ImportError:
    FullProfile = None


def generate_config_from_subscription(
    url: str,
    user_agent: Optional[str],
    no_user_agent: bool,
    export_format: str,
    debug: int,
    profile: Optional["FullProfile"] = None,
    client_profile: Optional["ClientProfile"] = None,
) -> dict:
    """Generate configuration from subscription data.

    Args:
        url: Subscription URL
        user_agent: Custom User-Agent header
        no_user_agent: Disable User-Agent header
        export_format: Export format
        debug: Debug level
        profile: Optional FullProfile for configuration
        client_profile: Optional ClientProfile for inbound configuration

    Returns:
        Generated configuration data

    Raises:
        typer.Exit: On processing errors
    """
    # Create subscription source
    # Используем автоопределение как в list-servers, а не жесткое кодирование форматов
    # source_type должен определяться по содержимому, а не по формату вывода
    source_type = "file" if url.startswith("file://") else "url"

    source = SubscriptionSource(
        url=url,
        source_type=source_type,
        user_agent=user_agent if not no_user_agent else None,
    )

    # Create managers
    subscription_manager = SubscriptionManager(source)
    export_manager = ExportManager(
        export_format=export_format, client_profile=client_profile, profile=profile
    )

    # Create pipeline context with debug level
    context = PipelineContext(debug_level=debug, source=url)

    # Process subscription
    try:
        result = subscription_manager.export_config(
            export_manager=export_manager, context=context
        )

        if not result.success:
            typer.echo(f"❌ {t('cli.error.subscription_processing_failed')}", err=True)
            for error in result.errors:
                typer.echo(f"  - {error.message}", err=True)
            raise typer.Exit(1)

        return result.config

    except Exception as e:
        typer.echo(f"❌ {t('cli.error.subscription_processing_failed')}: {e}", err=True)
        raise typer.Exit(1) from e


def generate_profile_from_cli(
    postprocessors: Optional[list[str]] = None,
    middleware: Optional[list[str]] = None,
    output_path: str = "profile.json",
) -> None:
    """Generate FullProfile JSON from CLI parameters.

    Args:
        postprocessors: List of postprocessor names
        middleware: List of middleware names
        output_path: Output path for generated profile

    Raises:
        typer.Exit: If profile generation fails
    """

    try:
        # Create basic profile structure
        profile_data: dict[str, Any] = {
            "id": "cli-generated-profile",
            "description": "Profile generated from CLI parameters",
            "filters": {
                "exclude_tags": [],
                "only_tags": [],
                "exclusions": [],
                "only_enabled": True,
            },
            "export": {
                "format": "sing-box",
                "outbound_profile": "vless-real",
                "inbound_profile": "tun",
                "output_file": "config.json",
            },
            "metadata": {},
        }

        # Add postprocessor configuration
        if postprocessors:
            validate_postprocessors(postprocessors)
            metadata = profile_data["metadata"]
            if isinstance(metadata, dict):
                metadata["postprocessors"] = {
                    "chain": [{"type": proc, "config": {}} for proc in postprocessors],
                    "execution_mode": "sequential",
                    "error_strategy": "continue",
                }

        # Add middleware configuration
        if middleware:
            validate_middleware(middleware)
            metadata = profile_data["metadata"]
            if isinstance(metadata, dict):
                metadata["middleware"] = {
                    "chain": [{"type": mw, "config": {}} for mw in middleware]
                }

        # Write profile to file
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(profile_data, f, indent=2, ensure_ascii=False)

        typer.echo(f"✅ {t('cli.success.profile_generated').format(path=output_path)}")

    except Exception as e:
        typer.echo(f"❌ Failed to generate profile: {e}", err=True)
        raise typer.Exit(1) from e
