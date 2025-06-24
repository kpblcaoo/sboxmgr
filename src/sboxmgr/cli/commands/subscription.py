import typer
import os
from sboxmgr.subscription.manager import SubscriptionManager
from sboxmgr.subscription.models import SubscriptionSource, PipelineContext
from sboxmgr.server.exclusions import load_exclusions
from sboxmgr.i18n.loader import LanguageLoader
from sboxmgr.i18n.t import t
from sboxmgr.utils.env import get_template_file, get_config_file, get_backup_file
from sboxmgr.export.export_manager import ExportManager

lang = LanguageLoader(os.getenv('SBOXMGR_LANG', 'en'))


def run(
    url: str = typer.Option(
        ..., "-u", "--url", help=t("cli.url.help"),
        envvar=["SBOXMGR_URL", "SINGBOX_URL", "TEST_URL"]
    ),
    debug: int = typer.Option(0, "-d", "--debug", help=t("cli.debug.help")),
    dry_run: bool = typer.Option(False, "--dry-run", help=t("cli.dry_run.help")),
    config_file: str = typer.Option(None, "--config-file", help=t("cli.config_file.help")),
    backup_file: str = typer.Option(None, "--backup-file", help=t("cli.backup_file.help")),
    template_file: str = typer.Option(None, "--template-file", help=t("cli.template_file.help")),
    user_agent: str = typer.Option(None, "--user-agent", help="Override User-Agent for subscription fetcher (default: ClashMeta/1.0)"),
    no_user_agent: bool = typer.Option(False, "--no-user-agent", help="Do not send User-Agent header at all"),
    format: str = typer.Option("singbox", "--format", help="Export format: singbox, clash, v2ray"),
    skip_version_check: bool = typer.Option(False, "--skip-version-check", help="Skip sing-box version compatibility check")
):
    """Update sing-box configuration from subscription with comprehensive pipeline.
    
    Fetches subscription data, processes it through the complete pipeline
    including parsing, filtering, and format conversion, then updates the
    local configuration file with automatic service restart.
    
    The process includes:
    1. Fetch subscription data with optional User-Agent customization
    2. Parse and validate server configurations
    3. Apply exclusions and filtering rules  
    4. Export to target format (sing-box, clash, v2ray)
    5. Validate generated configuration
    6. Update configuration file with backup
    7. Restart proxy service if applicable
    
    Args:
        url: Subscription URL to fetch from.
        debug: Debug verbosity level (0-2).
        dry_run: Validate configuration without applying changes.
        config_file: Override path to main configuration file.
        backup_file: Override path to backup configuration file.
        template_file: Override path to configuration template.
        user_agent: Custom User-Agent header for subscription requests.
        no_user_agent: Disable User-Agent header completely.
        format: Target export format (singbox, clash, v2ray).
                 skip_version_check: Skip version compatibility validation.
         
     Raises:
         typer.Exit: On subscription fetch failure, parse errors, or config write errors.
     """
    from logsetup.setup import setup_logging
    setup_logging(debug_level=debug)
    
    try:
        if no_user_agent:
            ua = ""
        else:
            ua = user_agent
        source = SubscriptionSource(url=url, source_type="url_base64", user_agent=ua)
        mgr = SubscriptionManager(source)
        exclusions = load_exclusions(dry_run=dry_run)
        context = PipelineContext(mode="default", debug_level=debug)
        user_routes = []
        
        # Создаём ExportManager с выбранным форматом
        export_mgr = ExportManager(export_format=format)
        config = mgr.export_config(exclusions=exclusions, user_routes=user_routes, context=context, export_manager=export_mgr, skip_version_check=skip_version_check)
        if not config.success or not config.config or not config.config.get("outbounds"):
            typer.echo("ERROR: No servers parsed from subscription, config not updated.", err=True)
            raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"{lang.get('error.subscription_failed')}: {e}", err=True)
        raise typer.Exit(1)

    template_file = template_file or get_template_file()
    config_file = config_file or get_config_file()
    backup_file = backup_file or get_backup_file()

    import json
    config_json = json.dumps(config.config, indent=2, ensure_ascii=False)

    if dry_run:
        from sboxmgr.config.generate import validate_config_file
        import tempfile
        typer.echo(lang.get("cli.dry_run_mode"))
        with tempfile.NamedTemporaryFile("w+", suffix=".json", delete=False) as tmp:
            temp_path = tmp.name
            tmp.write(config_json)
        valid, output = validate_config_file(temp_path)
        if valid:
            typer.echo(lang.get("cli.dry_run_valid"))
        else:
            typer.echo(f"{lang.get('cli.config_invalid')}\n{output}", err=True)
        os.unlink(temp_path)
        typer.echo(lang.get("cli.temp_file_deleted"))
        raise typer.Exit(0 if valid else 1)

    try:
        with open(config_file, "w", encoding="utf-8") as f:
            f.write(config_json)
        if backup_file:
            import shutil
            shutil.copy2(config_file, backup_file)
        try:
            from sboxmgr.service.manage import manage_service
            manage_service()
            if debug >= 1:
                typer.echo(lang.get("cli.service_restart_completed"))
        except Exception as e:
            typer.echo(f"[WARN] Failed to restart sing-box.service: {e}", err=True)
    except Exception as e:
        typer.echo(f"{lang.get('cli.error_config_update')}: {e}", err=True)
        raise typer.Exit(1)

    typer.echo(lang.get("cli.update_completed"))


def dry_run(
    url: str = typer.Option(
        ..., "-u", "--url", help=t("cli.url.help"),
        envvar=["SBOXMGR_URL", "SINGBOX_URL", "TEST_URL"]
    ),
    debug: int = typer.Option(0, "-d", "--debug", help=t("cli.debug.help")),
    config_file: str = typer.Option(None, "--config-file", help=t("cli.config_file.help")),
    template_file: str = typer.Option(None, "--template-file", help=t("cli.template_file.help")),
    user_agent: str = typer.Option(None, "--user-agent", help="Override User-Agent for subscription fetcher (default: ClashMeta/1.0)"),
    no_user_agent: bool = typer.Option(False, "--no-user-agent", help="Do not send User-Agent header at all"),
    format: str = typer.Option("singbox", "--format", help="Export format: singbox, clash, v2ray"),
    skip_version_check: bool = typer.Option(False, "--skip-version-check", help="Skip sing-box version compatibility check")
):
    """Validate subscription configuration without making changes.
    
    Performs the complete subscription processing pipeline including fetch,
    parse, and export operations, then validates the generated configuration
    but does not write any files or restart services. This is useful for
    testing subscriptions and troubleshooting configuration issues.
    
    Args:
        url: Subscription URL to validate.
        debug: Debug verbosity level (0-2).
        config_file: Override path to configuration file (for reference only).
        template_file: Override path to configuration template.
        user_agent: Custom User-Agent header for subscription requests.
        no_user_agent: Disable User-Agent header completely.
        format: Target export format for validation.
        skip_version_check: Skip version compatibility validation.
        
    Raises:
        typer.Exit: Exit code 0 if validation passes, 1 if validation fails.
    """
    from logsetup.setup import setup_logging
    setup_logging(debug_level=debug)
    
    try:
        if no_user_agent:
            ua = ""
        else:
            ua = user_agent
        source = SubscriptionSource(url=url, source_type="url_base64", user_agent=ua)
        mgr = SubscriptionManager(source)
        exclusions = load_exclusions(dry_run=True)
        context = PipelineContext(mode="default", debug_level=debug)
        user_routes = []
        
        # Создаём ExportManager с выбранным форматом
        export_mgr = ExportManager(export_format=format)
        config = mgr.export_config(exclusions=exclusions, user_routes=user_routes, context=context, export_manager=export_mgr, skip_version_check=skip_version_check)
        if not config.success or not config.config or not config.config.get("outbounds"):
            typer.echo("ERROR: No servers parsed from subscription, nothing to validate.", err=True)
            raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"{lang.get('error.subscription_failed')}: {e}", err=True)
        raise typer.Exit(1)

    import json
    config_json = json.dumps(config.config, indent=2, ensure_ascii=False)
    from sboxmgr.config.generate import validate_config_file
    import tempfile
    typer.echo(lang.get("cli.dry_run_mode"))
    with tempfile.NamedTemporaryFile("w+", suffix=".json", delete=False) as tmp:
        temp_path = tmp.name
        tmp.write(config_json)
    valid, output = validate_config_file(temp_path)
    if valid:
        typer.echo(lang.get("cli.dry_run_valid"))
    else:
        typer.echo(f"{lang.get('cli.config_invalid')}\n{output}", err=True)
    os.unlink(temp_path)
    typer.echo(lang.get("cli.temp_file_deleted"))
    raise typer.Exit(0 if valid else 1)


def list_servers(
    url: str = typer.Option(
        ..., "-u", "--url", help=t("cli.url.help"),
        envvar=["SBOXMGR_URL", "SINGBOX_URL", "TEST_URL"]
    ),
    debug: int = typer.Option(0, "-d", "--debug", help=t("cli.debug.help")),
    user_agent: str = typer.Option(None, "--user-agent", help="Override User-Agent for subscription fetcher (default: ClashMeta/1.0)"),
    no_user_agent: bool = typer.Option(False, "--no-user-agent", help="Do not send User-Agent header at all")
):
    """List all available servers from subscription.
    
    Fetches and parses the subscription to display all available server
    configurations with their basic information including index, name,
    protocol type, and connection details. Useful for inspecting
    subscription content and planning exclusions.
    
    Args:
        url: Subscription URL to list servers from.
        debug: Debug verbosity level (0-2).
        user_agent: Custom User-Agent header for subscription requests.
        no_user_agent: Disable User-Agent header completely.
        
    Raises:
        typer.Exit: On subscription fetch failure or parsing errors.
    """
    try:
        if no_user_agent:
            ua = ""
        else:
            ua = user_agent
        source = SubscriptionSource(url=url, source_type="url_base64", user_agent=ua)
        mgr = SubscriptionManager(source)
        exclusions = load_exclusions(dry_run=True)
        context = PipelineContext(mode="default", debug_level=debug)
        user_routes = []
        config = mgr.export_config(exclusions=exclusions, user_routes=user_routes, context=context)
        if not config.config or not isinstance(config.config, dict):
            typer.echo("[Error] No valid config generated from subscription.", err=True)
            raise typer.Exit(1)
        servers = config.config.get("outbounds", [])
        for i, s in enumerate(servers):
            typer.echo(f"[{i}] {s.get('tag', s.get('server', ''))} ({s.get('type', '')}:{s.get('server_port', '')})")
    except Exception as e:
        typer.echo(f"{lang.get('error.subscription_failed')}: {e}", err=True)
        raise typer.Exit(1) 