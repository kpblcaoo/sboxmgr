"""CLI commands for subscription processing (`sboxctl list-servers`).

This module contains the list-servers command that fetches subscription data
and displays available server configurations. This is the only remaining
command in this module after the CLI reorganization.
"""

import typer

from sboxmgr.i18n.t import t
from sboxmgr.server.exclusions import load_exclusions
from sboxmgr.subscription.manager import SubscriptionManager
from sboxmgr.subscription.models import PipelineContext, SubscriptionSource


def _is_service_outbound(outbound: dict) -> bool:
    """Проверяет, является ли outbound служебным (direct, block, dns-out, urltest).

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
    service_types = {"direct", "block", "dns", "urltest"}
    service_tags = {"direct", "block", "dns-out", "auto"}

    return outbound_type in service_types or tag in service_tags


def _format_policy_details(context: PipelineContext, server_tag: str) -> str:
    """Форматирует детали политик для сервера.

    Args:
        context: Pipeline context с результатами политик
        server_tag: Тег сервера

    Returns:
        Строка с деталями политик

    """
    details = []

    # Проверяем нарушения политик
    violations = context.metadata.get("policy_violations", [])
    server_violations = [v for v in violations if v.get("server") == server_tag]
    if server_violations:
        violation_reasons = [f"{v['policy']}: {v['reason']}" for v in server_violations]
        details.append(f"❌ DENIED: {'; '.join(violation_reasons)}")

    # Проверяем предупреждения
    warnings = context.metadata.get("policy_warnings", [])
    server_warnings = [w for w in warnings if w.get("server") == server_tag]
    if server_warnings:
        warning_reasons = [f"{w['policy']}: {w['reason']}" for w in server_warnings]
        details.append(f"⚠️ WARNINGS: {'; '.join(warning_reasons)}")

    # Проверяем информационные сообщения
    info_results = context.metadata.get("policy_info", [])
    server_info = [i for i in info_results if i.get("server") == server_tag]
    if server_info:
        info_reasons = [f"{i['policy']}: {i['reason']}" for i in server_info]
        details.append(f"ℹ️ INFO: {'; '.join(info_reasons)}")

    return " | ".join(details) if details else "✅ ALLOWED"


def list_servers(
    url: str = typer.Option(
        ...,
        "-u",
        "--url",
        help=t("cli.url.help"),
        envvar=["SBOXMGR_URL", "SINGBOX_URL", "TEST_URL"],
    ),
    debug: int = typer.Option(0, "-d", "--debug", help=t("cli.debug.help")),
    user_agent: str = typer.Option(
        None,
        "--user-agent",
        help="Override User-Agent for subscription fetcher (default: ClashMeta/1.0)",
    ),
    no_user_agent: bool = typer.Option(
        False, "--no-user-agent", help="Do not send User-Agent header at all"
    ),
    format: str = typer.Option(
        None,
        "--format",
        help="Force specific format: auto, base64, json, uri_list, clash",
    ),
    policy_details: bool = typer.Option(
        False,
        "-P",
        "--policy-details",
        help="Show policy evaluation details for each server",
    ),
    ctx: typer.Context = None,
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
        policy_details: Show policy evaluation details for each server.
        ctx: Typer context containing global flags.

    Raises:
        typer.Exit: On subscription fetch failure or parsing errors.

    """
    # Get global flags from context
    verbose = ctx.obj.get("verbose", False) if ctx.obj else False

    if verbose:
        typer.echo("🔍 Loading subscription...")
        typer.echo(f"   URL: {url}")
        typer.echo(f"   Format: {format or 'auto'}")
        typer.echo(f"   Debug level: {debug}")

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
        user_routes: list[str] = []
        config = mgr.export_config(
            exclusions=exclusions, user_routes=user_routes, context=context
        )

        # Проверяем политики ДО проверки config.config
        if policy_details:
            violations = context.metadata.get("policy_violations", [])
            warnings = context.metadata.get("policy_warnings", [])
            info_results = context.metadata.get("policy_info", [])

            # Если есть нарушения политик, показываем их независимо от результата конфигурации
            if violations or warnings or info_results:
                typer.echo("\n📊 Policy Evaluation Summary:")
                typer.echo(
                    f"   Servers denied: {len({v['server'] for v in violations})}"
                )
                typer.echo(
                    f"   Servers with warnings: {len({w['server'] for w in warnings})}"
                )
                typer.echo(f"   Total policy violations: {len(violations)}")
                typer.echo(f"   Total policy warnings: {len(warnings)}")

                # Показываем исправления валидации
                validation_fixes = context.metadata.get("validation_fixes", [])
                if validation_fixes:
                    typer.echo("\n🔧 Validation Fixes Applied:")
                    for fix in validation_fixes:
                        severity_icon = "ℹ️" if fix["severity"] == "info" else "⚠️"
                        typer.echo(
                            f"   {severity_icon} Server {fix['server_identifier']}: {fix['description']}"
                        )

                # Выводим причины блокировки по каждому серверу
                typer.echo(
                    "\n❌ Сервера заблокированы политиками. Причины по каждому серверу:"
                )
                # Собираем уникальные server_id
                all_servers = set(
                    [v["server"] for v in violations]
                    + [w["server"] for w in warnings]
                    + [i["server"] for i in info_results]
                )
                for server_id in all_servers:
                    typer.echo(f"\nServer: {server_id}")
                    vlist = [v for v in violations if v["server"] == server_id]
                    wlist = [w for w in warnings if w["server"] == server_id]
                    ilist = [i for i in info_results if i["server"] == server_id]
                    if vlist:
                        for v in vlist:
                            typer.echo(f"  ❌ DENIED by {v['policy']}: {v['reason']}")
                    if wlist:
                        for w in wlist:
                            typer.echo(f"  ⚠️ WARNING by {w['policy']}: {w['reason']}")
                    if ilist:
                        for i in ilist:
                            typer.echo(f"  ℹ️ INFO by {i['policy']}: {i['reason']}")

                # Если нет валидной конфигурации из-за политик, завершаем с кодом 2
                if not config.config or not isinstance(config.config, dict):
                    raise typer.Exit(2)

        if not config.config or not isinstance(config.config, dict):
            typer.echo("[Error] No valid config generated from subscription.", err=True)
            raise typer.Exit(1)

        # Получаем все outbounds и фильтруем служебные
        all_outbounds = config.config.get("outbounds", [])
        servers = [s for s in all_outbounds if not _is_service_outbound(s)]

        # Выводим статистику политик если включены детали и есть сервера
        if policy_details and servers:
            violations = context.metadata.get("policy_violations", [])
            warnings = context.metadata.get("policy_warnings", [])
            info_results = context.metadata.get("policy_info", [])

            typer.echo("\n📊 Policy Evaluation Summary:")
            typer.echo(f"   Total servers processed: {len(servers)}")
            typer.echo(f"   Servers denied: {len({v['server'] for v in violations})}")
            typer.echo(
                f"   Servers with warnings: {len({w['server'] for w in warnings})}"
            )
            typer.echo(f"   Total policy violations: {len(violations)}")
            typer.echo(f"   Total policy warnings: {len(warnings)}")

            # Показываем исправления валидации
            validation_fixes = context.metadata.get("validation_fixes", [])
            if validation_fixes:
                typer.echo("\n🔧 Validation Fixes Applied:")
                for fix in validation_fixes:
                    severity_icon = "ℹ️" if fix["severity"] == "info" else "⚠️"
                    typer.echo(
                        f"   {severity_icon} Server {fix['server_identifier']}: {fix['description']}"
                    )
            typer.echo()

        for i, s in enumerate(servers):
            server_tag = s.get("tag", s.get("server", ""))
            server_info = (
                f"[{i}] {server_tag} ({s.get('type', '')}:{s.get('server_port', '')})"
            )

            if policy_details:
                policy_info = _format_policy_details(context, server_tag)
                typer.echo(f"{server_info}")
                if policy_info != "✅ ALLOWED":
                    typer.echo(f"    {policy_info}")
            else:
                typer.echo(server_info)

    except Exception as e:
        typer.echo(f"❌ {t('cli.error.subscription_export_failed')}: {e}", err=True)
        raise typer.Exit(1) from e
