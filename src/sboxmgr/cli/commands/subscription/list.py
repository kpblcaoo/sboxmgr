"""Subscription list command module.

This module provides the 'subscription list' command for listing servers
from a subscription with various output formats and policy details.
"""

from typing import Optional

import typer

from sboxmgr.constants import DEFAULT_USER_AGENT
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
        DEFAULT_USER_AGENT,
        "--user-agent",
        help="Override User-Agent for subscription fetcher. If not provided, the default 'ClashMeta/1.0' will be used.",
    ),
    no_user_agent: bool = typer.Option(
        False, "--no-user-agent", help="Do not send User-Agent header at all"
    ),
    format: Optional[str] = typer.Option(
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
    output_format: str = typer.Option(
        "table",
        "--output-format",
        help="Output format: table, json",
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
        output_format: Output format (table/json).
        ctx: Typer context containing global flags.

    Raises:
        typer.Exit: On subscription fetch failure or parsing errors.

    """
    # Get global flags from context
    verbose = ctx.obj.get("verbose", False) if ctx is not None and ctx.obj else False

    if verbose:
        typer.echo("🔍 Loading subscription...")
        typer.echo(f"   URL: {url}")
        typer.echo(f"   Format: {format or 'auto'}")
        typer.echo(f"   Debug level: {debug}")
        typer.echo(f"   Output format: {output_format}")

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
                    typer.echo(f"   Validation fixes applied: {len(validation_fixes)}")

        if not config.success:
            typer.echo("❌ Failed to export subscription.")
            if config.errors:
                for error in config.errors:
                    typer.echo(f"   Error: {error}")
            raise typer.Exit(1)

        if not config.config or "outbounds" not in config.config:
            typer.echo("❌ No valid config generated from subscription.")
            raise typer.Exit(1)

        outbounds = config.config["outbounds"]
        if not outbounds:
            typer.echo("📡 No servers found in subscription.")
            return

        # Фильтруем служебные outbounds
        servers = [
            outbound for outbound in outbounds if not _is_service_outbound(outbound)
        ]

        if not servers:
            typer.echo("📡 No user servers found (only service outbounds).")
            return

        if output_format == "json":
            # JSON output
            server_data = []
            for i, server in enumerate(servers):
                server_info = {
                    "index": i,
                    "tag": server.get("tag", "N/A"),
                    "type": server.get("type", "N/A"),
                }

                # Add protocol-specific details
                if server.get("type") == "shadowsocks":
                    server_info.update(
                        {
                            "server": server.get("server", "N/A"),
                            "server_port": server.get("server_port", "N/A"),
                            "method": server.get("method", "N/A"),
                        }
                    )
                elif server.get("type") == "vmess":
                    server_info.update(
                        {
                            "server": server.get("server", "N/A"),
                            "server_port": server.get("server_port", "N/A"),
                            "uuid": server.get("uuid", "N/A"),
                            "security": server.get("security", "N/A"),
                        }
                    )
                elif server.get("type") == "vless":
                    server_info.update(
                        {
                            "server": server.get("server", "N/A"),
                            "server_port": server.get("server_port", "N/A"),
                            "uuid": server.get("uuid", "N/A"),
                            "encryption": server.get("encryption", "N/A"),
                        }
                    )
                elif server.get("type") == "trojan":
                    server_info.update(
                        {
                            "server": server.get("server", "N/A"),
                            "server_port": server.get("server_port", "N/A"),
                            "password": server.get("password", "N/A"),
                        }
                    )
                else:
                    # Generic fallback
                    server_info.update(
                        {
                            "server": server.get("server", "N/A"),
                            "server_port": server.get("server_port", "N/A"),
                        }
                    )

                # Add policy details if requested
                if policy_details:
                    server_info["policy_status"] = _format_policy_details(
                        context, server.get("tag", "")
                    )

                server_data.append(server_info)

            import json

            print(
                json.dumps(
                    {"servers": server_data, "total": len(server_data)}, indent=2
                )
            )
        else:
            # Table output
            from rich.console import Console
            from rich.table import Table

            console = Console()

            table = Table(title=f"📡 Available Servers ({len(servers)})")
            table.add_column("Index", style="cyan", justify="right")
            table.add_column("Tag", style="white")
            table.add_column("Type", style="blue")
            table.add_column("Server:Port", style="green")

            if policy_details:
                table.add_column("Policy Status", style="yellow")

            for i, server in enumerate(servers):
                server_tag = server.get("tag", "N/A")
                server_type = server.get("type", "N/A")
                server_addr = (
                    f"{server.get('server', 'N/A')}:{server.get('server_port', 'N/A')}"
                )

                if policy_details:
                    policy_status = _format_policy_details(context, server_tag)
                    table.add_row(
                        str(i), server_tag, server_type, server_addr, policy_status
                    )
                else:
                    table.add_row(str(i), server_tag, server_type, server_addr)

            console.print(table)

    except Exception as e:
        if verbose:
            typer.echo(f"❌ Error: {e}")
        else:
            typer.echo("❌ Failed to list servers from subscription.")
        raise typer.Exit(1)


__all__ = ["list_servers"]
