"""CLI commands for subscription processing (`sboxctl list-servers`).

This module contains the list-servers command that fetches subscription data
and displays available server configurations. This is the only remaining
command in this module after the CLI reorganization.
"""
import typer
from typing import List
from sboxmgr.subscription.manager import SubscriptionManager
from sboxmgr.subscription.models import SubscriptionSource, PipelineContext
from sboxmgr.server.exclusions import load_exclusions
from sboxmgr.i18n.t import t


def _is_service_outbound(outbound: dict) -> bool:
    """Проверяет, является ли outbound служебным (direct, block, dns-out).
    
    Args:
        outbound: Outbound конфигурация
        
    Returns:
        bool: True если это служебный outbound
    """
    if not outbound or not isinstance(outbound, dict):
        return False
        
    outbound_type = outbound.get("type", "")
    tag = outbound.get("tag", "")
    
    # Служебные outbounds
    service_types = {"direct", "block", "dns"}
    service_tags = {"direct", "block", "dns-out"}
    
    return outbound_type in service_types or tag in service_tags


def list_servers(
    url: str = typer.Option(
        ..., "-u", "--url", help=t("cli.url.help"),
        envvar=["SBOXMGR_URL", "SINGBOX_URL", "TEST_URL"]
    ),
    debug: int = typer.Option(0, "-d", "--debug", help=t("cli.debug.help")),
    user_agent: str = typer.Option(None, "--user-agent", help="Override User-Agent for subscription fetcher (default: ClashMeta/1.0)"),
    no_user_agent: bool = typer.Option(False, "--no-user-agent", help="Do not send User-Agent header at all"),
    format: str = typer.Option(None, "--format", help="Force specific format: auto, base64, json, uri_list, clash")
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
        format: Force specific format detection (auto, base64, json, uri_list, clash).
        
    Raises:
        typer.Exit: On subscription fetch failure or parsing errors.
    """
    try:
        if no_user_agent:
            ua = ""
        else:
            ua = user_agent
            
        # Определяем source_type на основе формата
        if format == "base64":
            source_type = "url_base64"
        elif format == "json":
            source_type = "url_json"
        elif format == "uri_list":
            source_type = "uri_list"
        elif format == "clash":
            source_type = "url"  # Используем универсальный fetcher для clash
        else:
            # Автоопределение - используем универсальный fetcher
            source_type = "url"
            
        source = SubscriptionSource(url=url, source_type=source_type, user_agent=ua)
        mgr = SubscriptionManager(source)
        exclusions = load_exclusions(dry_run=True)
        context = PipelineContext(mode="default", debug_level=debug)
        user_routes: List[str] = []
        config = mgr.export_config(exclusions=exclusions, user_routes=user_routes, context=context)
        if not config.config or not isinstance(config.config, dict):
            typer.echo("[Error] No valid config generated from subscription.", err=True)
            raise typer.Exit(1)
        
        # Получаем все outbounds и фильтруем служебные
        all_outbounds = config.config.get("outbounds", [])
        servers = [s for s in all_outbounds if not _is_service_outbound(s)]
        
        for i, s in enumerate(servers):
            typer.echo(f"[{i}] {s.get('tag', s.get('server', ''))} ({s.get('type', '')}:{s.get('server_port', '')})")
    except Exception as e:
        typer.echo(f"{t('error.subscription_failed')}: {e}", err=True)
        raise typer.Exit(1) 