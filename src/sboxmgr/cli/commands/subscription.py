import typer
import os
from sboxmgr.subscription.manager import SubscriptionManager
from sboxmgr.subscription.models import SubscriptionSource, PipelineContext
from sboxmgr.server.exclusions import load_exclusions
from sboxmgr.i18n.loader import LanguageLoader
from sboxmgr.i18n.t import t
from sboxmgr.utils.env import get_template_file, get_config_file, get_backup_file

lang = LanguageLoader(os.getenv('SBOXMGR_LANG', 'en'))


def run(
    url: str = typer.Option(
        ..., "-u", "--url", help=t("cli.url.help"),
        envvar=["SBOXMGR_URL", "SINGBOX_URL", "TEST_URL"]
    ),
    remarks: str = typer.Option(None, "-r", "--remarks", help=t("cli.remarks.help")),
    index: str = typer.Option(None, "-i", "--index", help=t("cli.index.help")),
    debug: int = typer.Option(0, "-d", "--debug", help=t("cli.debug.help")),
    dry_run: bool = typer.Option(False, "--dry-run", help=t("cli.dry_run.help")),
    config_file: str = typer.Option(None, "--config-file", help=t("cli.config_file.help")),
    backup_file: str = typer.Option(None, "--backup-file", help=t("cli.backup_file.help")),
    template_file: str = typer.Option(None, "--template-file", help=t("cli.template_file.help")),
    use_selected: bool = typer.Option(False, "--use-selected", help=t("cli.use_selected.help")),
    user_agent: str = typer.Option(None, "--user-agent", help="Override User-Agent for subscription fetcher (default: ClashMeta/1.0)"),
    no_user_agent: bool = typer.Option(False, "--no-user-agent", help="Do not send User-Agent header at all")
):
    """Generate and apply sing-box config (default scenario)."""
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
        config = mgr.export_config(exclusions=exclusions, user_routes=user_routes, context=context)
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
    remarks: str = typer.Option(None, "-r", "--remarks", help=t("cli.remarks.help")),
    index: str = typer.Option(None, "-i", "--index", help=t("cli.index.help")),
    debug: int = typer.Option(0, "-d", "--debug", help=t("cli.debug.help")),
    config_file: str = typer.Option(None, "--config-file", help=t("cli.config_file.help")),
    template_file: str = typer.Option(None, "--template-file", help=t("cli.template_file.help")),
    user_agent: str = typer.Option(None, "--user-agent", help="Override User-Agent for subscription fetcher (default: ClashMeta/1.0)"),
    no_user_agent: bool = typer.Option(False, "--no-user-agent", help="Do not send User-Agent header at all")
):
    """Validate config and print result (no changes)."""
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
    """List all available servers from config."""
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