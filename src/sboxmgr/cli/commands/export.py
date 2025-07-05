"""CLI command for configuration export (`sboxctl export`).

This module implements the unified export command that replaces the previous
run and dry-run commands. It generates configurations from subscriptions and
exports them to various formats while following ADR-0014 principles:
- sboxmgr only generates configurations
- sboxagent handles service management
- No direct service restart from sboxmgr
"""
import typer
import os
import json
import tempfile
from pathlib import Path
from typing import Optional, List, Any

from sboxmgr.subscription.manager import SubscriptionManager
from sboxmgr.subscription.models import SubscriptionSource, ClientProfile, InboundProfile
from sboxmgr.i18n.t import t
from sboxmgr.utils.env import get_backup_file
from sboxmgr.export.export_manager import ExportManager
from sboxmgr.agent import AgentBridge, AgentNotAvailableError, ClientType
from sboxmgr.config.validation import validate_config_file

# Import Phase 3 components
try:
    from sboxmgr.profiles.models import FullProfile
    from sboxmgr.subscription.postprocessors import (
        PostProcessorChain,
        GeoFilterPostProcessor,
        TagFilterPostProcessor,
        LatencySortPostProcessor
    )
    from sboxmgr.subscription.middleware import LoggingMiddleware, EnrichmentMiddleware
    PHASE3_AVAILABLE = True
except ImportError:
    PHASE3_AVAILABLE = False
    FullProfile = None

# Константы для валидации CLI-флагов
ALLOWED_POSTPROCESSORS = ['geo_filter', 'tag_filter', 'latency_sort']
ALLOWED_MIDDLEWARE = ['logging', 'enrichment']


def _validate_flag_combinations(
    dry_run: bool, 
    agent_check: bool, 
    validate_only: bool, 
    url: Optional[str]
) -> None:
    """Validate flag combinations for mutual exclusivity.
    
    Args:
        dry_run: Dry run mode flag
        agent_check: Agent check mode flag  
        validate_only: Validate only mode flag
        url: Subscription URL
        
    Raises:
        typer.Exit: If invalid flag combination detected

    """
    if dry_run and agent_check:
        typer.echo("❌ Error: --dry-run and --agent-check are mutually exclusive", err=True)
        raise typer.Exit(1)
    
    if validate_only and url:
        typer.echo("❌ Error: --validate-only cannot be used with subscription URL", err=True)
        raise typer.Exit(1)
        
    if validate_only and (dry_run or agent_check):
        typer.echo("❌ Error: --validate-only cannot be used with --dry-run or --agent-check", err=True)
        raise typer.Exit(1)


def _determine_output_format(output_file: str, format_flag: str) -> str:
    """Determine output format based on file extension and format flag.
    
    Args:
        output_file: Output file path
        format_flag: Format flag value (json, toml, auto)
        
    Returns:
        Determined format (json or toml)

    """
    if format_flag == "auto":
        ext = Path(output_file).suffix.lower()
        if ext == ".toml":
            return "toml"
        else:
            return "json"
    return format_flag


def _create_backup_if_needed(output_file: str, backup: bool) -> Optional[str]:
    """Create backup of existing config file if requested.
    
    Args:
        output_file: Path to output file
        backup: Whether to create backup
        
    Returns:
        Path to backup file if created, None otherwise

    """
    if not backup or not os.path.exists(output_file):
        return None
        
    backup_file = get_backup_file()
    if backup_file:
        import shutil
        shutil.copy2(output_file, backup_file)
        typer.echo(f"📦 Backup created: {backup_file}")
        return backup_file
    return None


def _run_agent_check(config_file: str, agent_check: bool) -> bool:
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
            typer.echo("ℹ️  sboxagent not available - skipping external validation", err=True)
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
        typer.echo("ℹ️  sboxagent not available - skipping external validation", err=True)
        return True
    except Exception as e:
        typer.echo(f"⚠️  Agent check failed: {e}", err=True)
        return False


def _create_client_profile_from_profile(profile: Optional['FullProfile']) -> Optional['ClientProfile']:
    """Create ClientProfile from FullProfile export settings.
    
    Args:
        profile: FullProfile with export settings
        
    Returns:
        ClientProfile with inbounds configured from profile, or None if no profile

    """
    if not profile or not hasattr(profile, 'export') or not profile.export:
        return None
    
    from sboxmgr.subscription.models import ClientProfile
    
    inbounds = []
    
    # Create inbound based on profile.inbound_profile
    if hasattr(profile.export, 'inbound_profile') and profile.export.inbound_profile:
        inbound_type = profile.export.inbound_profile
        
        # Map profile names to actual inbound types with correct sing-box configuration
        if inbound_type == "tun":
            inbounds.append(InboundProfile(
                type="tun",
                options={
                    "tag": "tun-in",
                    "interface_name": "tun0",
                    "address": ["198.18.0.1/16"],
                    "mtu": 1500,
                    "auto_route": True,
                    "endpoint_independent_nat": True,
                    "stack": "system",
                    "sniff": True,
                    "strict_route": True
                }
            ))
        elif inbound_type == "tproxy":
            inbounds.append(InboundProfile(
                type="tproxy",
                listen="0.0.0.0",
                port=12345,
                options={
                    "tag": "tproxy-in",
                    "network": ["tcp", "udp"],
                    "sniff": True
                }
            ))
        elif inbound_type == "socks5":
            inbounds.append(InboundProfile(
                type="socks",
                listen="0.0.0.0",
                port=1080,
                options={
                    "tag": "socks-in",
                    "sniff": True,
                    "users": [
                        {
                            "username": "test_user",
                            "password": "test_pass"
                        }
                    ]
                }
            ))
        elif inbound_type == "http":
            inbounds.append(InboundProfile(
                type="http",
                listen="0.0.0.0",
                port=8080,
                options={
                    "tag": "http-in",
                    "sniff": True
                }
            ))
        elif inbound_type == "all":
            # Create all inbound types
            inbounds.extend([
                InboundProfile(
                    type="tun",
                    options={
                        "tag": "tun-in",
                        "interface_name": "tun0",
                        "address": ["198.18.0.1/16"],
                        "mtu": 1500,
                        "auto_route": True,
                        "endpoint_independent_nat": True,
                        "stack": "system",
                        "sniff": True,
                        "strict_route": True
                    }
                ),
                InboundProfile(
                    type="tproxy",
                    listen="0.0.0.0",
                    port=12345,
                    options={
                        "tag": "tproxy-in",
                        "network": ["tcp", "udp"],
                        "sniff": True
                    }
                ),
                InboundProfile(
                    type="socks",
                    listen="0.0.0.0",
                    port=1080,
                    options={
                        "tag": "socks-in",
                        "sniff": True,
                        "users": [
                            {
                                "username": "test_user",
                                "password": "test_pass"
                            }
                        ]
                    }
                ),
                InboundProfile(
                    type="http",
                    listen="0.0.0.0",
                    port=8080,
                    options={
                        "tag": "http-in",
                        "sniff": True
                    }
                )
            ])
        else:
            # Default to tun if unknown
            inbounds.append(InboundProfile(
                type="tun",
                options={
                    "tag": "tun-in",
                    "interface_name": "tun0",
                    "address": ["198.18.0.1/16"],
                    "mtu": 1500,
                    "auto_route": True,
                    "endpoint_independent_nat": True,
                    "stack": "system",
                    "sniff": True
                }
            ))
    
    if inbounds:
        return ClientProfile(inbounds=inbounds)
    
    return None


def _generate_config_from_subscription(
    url: str,
    user_agent: Optional[str],
    no_user_agent: bool,
    export_format: str,
    debug: int,
    profile: Optional['FullProfile'] = None,
    client_profile: Optional['ClientProfile'] = None
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
    source_type = "file" if url.startswith('file://') else "url"
    
    source = SubscriptionSource(
        url=url,
        source_type=source_type,
        user_agent=user_agent if not no_user_agent else None
    )
    
    # Create managers
    subscription_manager = SubscriptionManager(source)
    export_manager = ExportManager(
        export_format=export_format,
        client_profile=client_profile,
        profile=profile
    )
    
    # Create ClientProfile from profile if not provided directly
    if client_profile is None:
        client_profile = _create_client_profile_from_profile(profile)
    
    # Create pipeline context with debug level
    from sboxmgr.subscription.models import PipelineContext
    context = PipelineContext(debug_level=debug, source=url)
    
    # Process subscription
    try:
        result = subscription_manager.export_config(
            export_manager=export_manager,
            context=context
        )
        
        if not result.success:
            typer.echo(f"❌ {t('cli.error.subscription_processing_failed')}", err=True)
            for error in result.errors:
                typer.echo(f"  - {error.message}", err=True)
            raise typer.Exit(1)
        
        return result.config
        
    except Exception as e:
        typer.echo(f"❌ {t('cli.error.subscription_processing_failed')}: {e}", err=True)
        raise typer.Exit(1)


def _write_config_to_file(config_data: dict, output_file: str, output_format: str) -> None:
    """Write configuration to output file in specified format.
    
    Args:
        config_data: Configuration data to write
        output_file: Output file path  
        output_format: Output format (json or toml)
        
    Raises:
        typer.Exit: If writing fails

    """
    try:
        # Ensure output directory exists
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            
        if output_format == "toml":
            import toml
            config_content = toml.dumps(config_data)
        else:
            config_content = json.dumps(config_data, indent=2, ensure_ascii=False)
            
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(config_content)
            
        typer.echo(f"✅ Configuration written to: {output_file}")
        
    except Exception as e:
        typer.echo(f"❌ {t('cli.error_config_update')}: {e}", err=True)
        raise typer.Exit(1)


def _validate_postprocessors(processors: List[str]) -> None:
    """Validate postprocessor names.
    
    Args:
        processors: List of postprocessor names to validate
        
    Raises:
        typer.Exit: If invalid postprocessor names found

    """
    if invalid := [x for x in processors if x not in ALLOWED_POSTPROCESSORS]:
        typer.echo(f"❌ {t('cli.error.unknown_postprocessors').format(invalid=', '.join(invalid))}", err=True)
        typer.echo(f"💡 {t('cli.error.available_postprocessors').format(available=', '.join(ALLOWED_POSTPROCESSORS))}", err=True)
        raise typer.Exit(1)


def _validate_middleware(middleware: List[str]) -> None:
    """Validate middleware names.
    
    Args:
        middleware: List of middleware names to validate
        
    Raises:
        typer.Exit: If invalid middleware names found

    """
    if invalid := [x for x in middleware if x not in ALLOWED_MIDDLEWARE]:
        typer.echo(f"❌ {t('cli.error.unknown_middleware').format(invalid=', '.join(invalid))}", err=True)
        typer.echo(f"💡 {t('cli.error.available_middleware').format(available=', '.join(ALLOWED_MIDDLEWARE))}", err=True)
        raise typer.Exit(1)


def _load_profile_from_file(profile_path: str) -> Optional[FullProfile]:
    """Load FullProfile from JSON file.
    
    Args:
        profile_path: Path to profile JSON file
        
    Returns:
        Loaded FullProfile or None if failed
        
    Raises:
        typer.Exit: If profile loading fails

    """
    if not PHASE3_AVAILABLE:
        typer.echo("⚠️  Profile support requires Phase 3 components", err=True)
        return None
        
    if not os.path.exists(profile_path):
        typer.echo(f"❌ {t('cli.error.profile_not_found').format(path=profile_path)}", err=True)
        raise typer.Exit(1)
    
    try:
        with open(profile_path, 'r', encoding='utf-8') as f:
            profile_data = json.load(f)
        
        # Create FullProfile from loaded data with better error handling
        from pydantic import ValidationError
        profile = FullProfile(**profile_data)
        typer.echo(f"✅ {t('cli.success.profile_loaded').format(path=profile_path)}")
        return profile
        
    except ValidationError as ve:
        typer.echo(f"❌ {t('cli.error.profile_validation_failed')}:", err=True)
        for error in ve.errors():
            field_path = '.'.join(str(loc) for loc in error['loc'])
            typer.echo(f"   - {field_path}: {error['msg']}", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"❌ {t('cli.error.failed_to_load_profile').format(error=str(e))}", err=True)
        raise typer.Exit(1)


def _generate_profile_from_cli(
    postprocessors: Optional[List[str]] = None,
    middleware: Optional[List[str]] = None,
    output_path: str = "profile.json"
) -> None:
    """Generate FullProfile JSON from CLI parameters.
    
    Args:
        postprocessors: List of postprocessor names
        middleware: List of middleware names  
        output_path: Output path for generated profile
        
    Raises:
        typer.Exit: If profile generation fails

    """
    if not PHASE3_AVAILABLE:
        typer.echo("⚠️  Profile generation requires Phase 3 components", err=True)
        raise typer.Exit(1)
    
    try:
        # Create basic profile structure
        profile_data = {
            "id": "cli-generated-profile",
            "description": "Profile generated from CLI parameters",
            "filters": {
                "exclude_tags": [],
                "only_tags": [],
                "exclusions": [],
                "only_enabled": True
            },
            "export": {
                "format": "sing-box",
                "outbound_profile": "vless-real",
                "inbound_profile": "tun",
                "output_file": "config.json"
            },
            "metadata": {}
        }
        
        # Add postprocessor configuration
        if postprocessors:
            _validate_postprocessors(postprocessors)
            profile_data["metadata"]["postprocessors"] = {
                "chain": [{"type": proc, "config": {}} for proc in postprocessors],
                "execution_mode": "sequential",
                "error_strategy": "continue"
            }
        
        # Add middleware configuration
        if middleware:
            _validate_middleware(middleware)
            profile_data["metadata"]["middleware"] = {
                "chain": [{"type": mw, "config": {}} for mw in middleware]
            }
        
        # Write profile to file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(profile_data, f, indent=2, ensure_ascii=False)
        
        typer.echo(f"✅ {t('cli.success.profile_generated').format(path=output_path)}")
        
    except Exception as e:
        typer.echo(f"❌ Failed to generate profile: {e}", err=True)
        raise typer.Exit(1)


def _create_postprocessor_chain_from_list(processors: List[str]) -> Optional['PostProcessorChain']:
    """Create PostProcessorChain from list of processor names.
    
    Args:
        processors: List of processor names (geo_filter, tag_filter, latency_sort)
        
    Returns:
        Configured PostProcessorChain or None
        
    Raises:
        typer.Exit: If invalid processor names found

    """
    if not PHASE3_AVAILABLE:
        typer.echo("⚠️  PostProcessor chains require Phase 3 components", err=True)
        return None
    
    # Validate processor names
    _validate_postprocessors(processors)
    
    processor_instances = []
    processor_map = {
        'geo_filter': GeoFilterPostProcessor,
        'tag_filter': TagFilterPostProcessor,
        'latency_sort': LatencySortPostProcessor
    }
    
    for proc_name in processors:
        # Use default configuration for CLI-specified processors
        processor_instances.append(processor_map[proc_name]({}))
        typer.echo(f"✅ {t('cli.success.postprocessor_added').format(name=proc_name)}")
    
    if processor_instances:
        return PostProcessorChain(processor_instances, {
            'execution_mode': 'sequential',
            'error_strategy': 'continue'
        })
    
    return None


def _create_middleware_chain_from_list(middleware: List[str]) -> List[Any]:
    """Create middleware chain from list of middleware names.
    
    Args:
        middleware: List of middleware names (logging, enrichment)
        
    Returns:
        List of configured middleware instances
        
    Raises:
        typer.Exit: If invalid middleware names found

    """
    if not PHASE3_AVAILABLE:
        typer.echo("⚠️  Middleware chains require Phase 3 components", err=True)
        return []
    
    # Validate middleware names
    _validate_middleware(middleware)
    
    middleware_instances = []
    middleware_map = {
        'logging': LoggingMiddleware,
        'enrichment': EnrichmentMiddleware
    }
    
    for mw_name in middleware:
        # Use default configuration for CLI-specified middleware
        middleware_instances.append(middleware_map[mw_name]({}))
        typer.echo(f"✅ {t('cli.success.middleware_added').format(name=mw_name)}")
    
    return middleware_instances


def _load_client_profile_from_file(client_profile_path: str) -> Optional['ClientProfile']:
    """Load ClientProfile from JSON file.
    
    Args:
        client_profile_path: Path to client profile JSON file
        
    Returns:
        Loaded ClientProfile or None if failed
        
    Raises:
        typer.Exit: If client profile loading fails

    """
    if not os.path.exists(client_profile_path):
        typer.echo(f"❌ Client profile not found: {client_profile_path}", err=True)
        raise typer.Exit(1)
    
    try:
        with open(client_profile_path, 'r', encoding='utf-8') as f:
            client_profile_data = json.load(f)
        
        # Create ClientProfile from loaded data with better error handling
        from pydantic import ValidationError
        from sboxmgr.subscription.models import ClientProfile
        client_profile = ClientProfile(**client_profile_data)
        typer.echo(f"✅ Client profile loaded: {client_profile_path}")
        return client_profile
        
    except ValidationError as ve:
        typer.echo("❌ Client profile validation failed:", err=True)
        for error in ve.errors():
            field_path = '.'.join(str(loc) for loc in error['loc'])
            typer.echo(f"   - {field_path}: {error['msg']}", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"❌ Failed to load client profile: {e}", err=True)
        raise typer.Exit(1)


def _validate_final_route(final_route: str) -> None:
    """Validate final route value.
    
    Args:
        final_route: Final route value to validate
        
    Raises:
        typer.Exit: If final route is invalid

    """
    valid_routes = ["auto", "direct", "block", "proxy", "dns"]
    
    # Check if it's a valid predefined route
    if final_route in valid_routes:
        return
    
    # Check if it's a valid outbound tag (alphanumeric + hyphen/underscore)
    import re
    if re.match(r'^[a-zA-Z0-9_-]+$', final_route):
        return
    
    typer.echo(f"❌ Invalid final route: {final_route}", err=True)
    typer.echo(f"💡 Valid values: {', '.join(valid_routes)} or a valid outbound tag", err=True)
    raise typer.Exit(1)


def _validate_exclude_outbounds(exclude_outbounds: str) -> None:
    """Validate exclude outbounds list.
    
    Args:
        exclude_outbounds: Comma-separated list of outbound types to validate
        
    Raises:
        typer.Exit: If exclude outbounds contains invalid values

    """
    # Extended list of valid outbound types including all supported protocols
    valid_types = [
        # Basic outbound types
        "direct", "block", "dns", "proxy", "urltest", "selector",
        # Supported protocol types
        "vmess", "vless", "trojan", "shadowsocks", "ss", "hysteria2",
        "wireguard", "tuic", "shadowtls", "anytls", "tor", "ssh",
        "http", "socks"
    ]
    
    exclude_list = [o.strip() for o in exclude_outbounds.split(',') if o.strip()]
    
    invalid_types = []
    for outbound_type in exclude_list:
        if outbound_type not in valid_types:
            invalid_types.append(outbound_type)
    
    if invalid_types:
        typer.echo(f"❌ Invalid outbound types: {', '.join(invalid_types)}", err=True)
        typer.echo(f"💡 Valid types: {', '.join(valid_types)}", err=True)
        raise typer.Exit(1)


def export(
    url: str = typer.Option(
        None, "-u", "--url", help=t("cli.url.help"),
        envvar=["SBOXMGR_URL", "SINGBOX_URL", "TEST_URL"]
    ),
    debug: int = typer.Option(0, "-d", "--debug", help=t("cli.debug.help")),
    dry_run: bool = typer.Option(False, "--dry-run", help="Validate configuration without saving"),
    output: str = typer.Option("config.json", "--output", help="Output file path (ignored in dry-run and agent-check modes)"),
    format: str = typer.Option("json", "--format", help="Output format: json, toml, auto"),
    export_format: str = typer.Option("singbox", "--export-format", help="Export format: singbox, clash"),
    validate_only: bool = typer.Option(False, "--validate-only", help="Only validate existing configuration file"),
    agent_check: bool = typer.Option(False, "--agent-check", help="Check configuration via sboxagent without saving"),
    backup: bool = typer.Option(False, "--backup", help="Create backup before overwriting existing file"),
    user_agent: str = typer.Option(None, "--user-agent", help="Override User-Agent for subscription fetcher"),
    no_user_agent: bool = typer.Option(False, "--no-user-agent", help="Do not send User-Agent header"),
    # Phase 4 enhancements
    profile: str = typer.Option(None, "--profile", help="Profile JSON file for Phase 3 processing configuration"),
    client_profile: str = typer.Option(None, "--client-profile", help="Client profile JSON file for inbound configuration"),
    postprocessors: str = typer.Option(None, "--postprocessors", help="Comma-separated list of postprocessors (geo_filter,tag_filter,latency_sort)"),
    middleware: str = typer.Option(None, "--middleware", help="Comma-separated list of middleware (logging,enrichment)"),
    generate_profile: str = typer.Option(None, "--generate-profile", help="Generate profile JSON file from CLI parameters and exit"),
    # Inbound CLI parameters
    inbound_types: str = typer.Option(None, "--inbound-types", help="Comma-separated inbound types (tun,socks,http,tproxy)"),
    # TUN parameters
    tun_address: str = typer.Option(None, "--tun-address", help="TUN interface address (default: 198.18.0.1/16)"),
    tun_mtu: int = typer.Option(None, "--tun-mtu", help="TUN MTU value (default: 1500)"),
    tun_stack: str = typer.Option(None, "--tun-stack", help="TUN network stack (system,gvisor,mixed, default: mixed)"),
    # SOCKS parameters
    socks_port: int = typer.Option(None, "--socks-port", help="SOCKS proxy port (default: 1080)"),
    socks_listen: str = typer.Option(None, "--socks-listen", help="SOCKS bind address (default: 127.0.0.1)"),
    socks_auth: str = typer.Option(None, "--socks-auth", help="SOCKS authentication (user:pass)"),
    # HTTP parameters
    http_port: int = typer.Option(None, "--http-port", help="HTTP proxy port (default: 8080)"),
    http_listen: str = typer.Option(None, "--http-listen", help="HTTP bind address (default: 127.0.0.1)"),
    http_auth: str = typer.Option(None, "--http-auth", help="HTTP authentication (user:pass)"),
    # TPROXY parameters
    tproxy_port: int = typer.Option(None, "--tproxy-port", help="TPROXY port (default: 7895)"),
    tproxy_listen: str = typer.Option(None, "--tproxy-listen", help="TPROXY bind address (default: 0.0.0.0)"),
    # DNS mode
    dns_mode: str = typer.Option(None, "--dns-mode", help="DNS resolution mode (system,tunnel,off, default: system)"),
    # Routing and filtering flags
    final_route: str = typer.Option(None, "--final-route", help="Set final routing destination (e.g., proxy, direct, block)"),
    exclude_outbounds: str = typer.Option(None, "--exclude-outbounds", help="Comma-separated list of outbound types to exclude (e.g., direct,block,dns)")
):
    """Export configuration with various modes.
    
    This unified command replaces the previous run and dry-run commands while
    following ADR-0014 principles. It generates configurations from subscriptions
    and exports them to various formats without managing services directly.
    
    Modes:
    - Default: Generate and save config to output file
    - --dry-run: Validate without saving (uses temporary file)  
    - --agent-check: Check via sboxagent without saving
    - --validate-only: Validate existing config file only
    
    Args:
        url: Subscription URL to fetch from
        debug: Debug verbosity level (0-2)
        dry_run: Validate configuration without saving
        output: Output file path (default: config.json)
        format: Output format (json, toml, auto)
        export_format: Export format (singbox, clash)
        validate_only: Only validate existing configuration
        agent_check: Check via sboxagent without applying
        backup: Create backup before overwriting
        user_agent: Custom User-Agent header
        no_user_agent: Disable User-Agent header
        profile: Profile JSON file for Phase 3 processing configuration
        client_profile: Client profile JSON file for inbound configuration
        postprocessors: Comma-separated list of postprocessors (geo_filter,tag_filter,latency_sort)
        middleware: Comma-separated list of middleware (logging,enrichment)
        generate_profile: Generate profile JSON file from CLI parameters and exit
        inbound_types: Comma-separated inbound types (tun,socks,http,tproxy)
        tun_address: TUN interface address (default: 198.18.0.1/16)
        tun_mtu: TUN MTU value (default: 1500)
        tun_stack: TUN network stack (system,gvisor,mixed, default: mixed)
        socks_port: SOCKS proxy port (default: 1080)
        socks_listen: SOCKS bind address (default: 127.0.0.1)
        socks_auth: SOCKS authentication (user:pass)
        http_port: HTTP proxy port (default: 8080)
        http_listen: HTTP bind address (default: 127.0.0.1)
        http_auth: HTTP authentication (user:pass)
        tproxy_port: TPROXY port (default: 7895)
        tproxy_listen: TPROXY bind address (default: 0.0.0.0)
        dns_mode: DNS resolution mode (system,tunnel,off, default: system)
        final_route: Set final routing destination (e.g., proxy, direct, block)
        exclude_outbounds: Comma-separated list of outbound types to exclude (e.g., direct,block,dns)
        
    Raises:
        typer.Exit: On validation failure or processing errors

    """
    from logsetup.setup import setup_logging
    setup_logging(debug_level=debug)
    
    # Handle profile generation mode (early exit)
    if generate_profile:
        postprocessors_list = [p.strip() for p in postprocessors.split(',') if p.strip()] if postprocessors else None
        middleware_list = [m.strip() for m in middleware.split(',') if m.strip()] if middleware else None
        _generate_profile_from_cli(postprocessors_list, middleware_list, generate_profile)
        raise typer.Exit(0)
    
    # Validate flag combinations
    _validate_flag_combinations(dry_run, agent_check, validate_only, url)
    
    # Handle validate-only mode
    if validate_only:
        config_file = output
        if not os.path.exists(config_file):
            typer.echo(f"❌ Configuration file not found: {config_file}", err=True)
            raise typer.Exit(1)
            
        try:
            validate_config_file(config_file)
            typer.echo(f"✅ Configuration is valid: {config_file}")
            raise typer.Exit(0)
        except typer.Exit:
            # Re-raise typer.Exit to preserve exit code
            raise  
        except Exception as e:
            typer.echo(f"❌ Configuration is invalid: {config_file}", err=True)
            typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(1)
    
    # URL is required for other modes
    if not url:
        typer.echo(f"❌ {t('cli.error.subscription_url_required')}", err=True)
        raise typer.Exit(1)
    
    # Validate postprocessors and middleware if provided
    postprocessors_list = None
    middleware_list = None
    
    if postprocessors:
        postprocessors_list = [p.strip() for p in postprocessors.split(',') if p.strip()]
        if postprocessors_list:
            try:
                _validate_postprocessors(postprocessors_list)
            except typer.Exit:
                raise  # Re-raise to preserve exit code
    
    if middleware:
        middleware_list = [m.strip() for m in middleware.split(',') if m.strip()]
        if middleware_list:
            try:
                _validate_middleware(middleware_list)
            except typer.Exit:
                raise  # Re-raise to preserve exit code
    
    # Validate routing and filtering parameters if provided
    if final_route:
        try:
            _validate_final_route(final_route)
        except typer.Exit:
            raise  # Re-raise to preserve exit code
    
    if exclude_outbounds:
        try:
            _validate_exclude_outbounds(exclude_outbounds)
        except typer.Exit:
            raise  # Re-raise to preserve exit code
    
    # Load profile if provided
    loaded_profile = None
    if profile:
        try:
            loaded_profile = _load_profile_from_file(profile)
        except typer.Exit:
            raise  # Re-raise to preserve exit code
    
    # Load client profile if provided
    loaded_client_profile = None
    if client_profile:
        try:
            loaded_client_profile = _load_client_profile_from_file(client_profile)
        except typer.Exit:
            raise  # Re-raise to preserve exit code
    
    # Build client profile from CLI parameters if provided
    if inbound_types and not loaded_client_profile:
        try:
            from sboxmgr.cli.inbound_builder import build_client_profile_from_cli
            loaded_client_profile = build_client_profile_from_cli(
                inbound_types=inbound_types,
                tun_address=tun_address,
                tun_mtu=tun_mtu,
                tun_stack=tun_stack,
                socks_port=socks_port,
                socks_listen=socks_listen,
                socks_auth=socks_auth,
                http_port=http_port,
                http_listen=http_listen,
                http_auth=http_auth,
                tproxy_port=tproxy_port,
                tproxy_listen=tproxy_listen,
                dns_mode=dns_mode
            )
            typer.echo("✅ Built client profile from CLI parameters")
        except ValueError as e:
            typer.echo(f"❌ Invalid parameters: {e}", err=True)
            raise typer.Exit(1)
        except Exception as e:
            typer.echo(f"❌ Failed to build client profile: {e}", err=True)
            raise typer.Exit(1)
    
    # Apply routing and filtering parameters if provided
    if final_route or exclude_outbounds:
        # Use existing client profile or create new one
        if not loaded_client_profile:
            loaded_client_profile = ClientProfile()
        
        # Set final route if provided
        if final_route:
            if not loaded_client_profile.routing:
                loaded_client_profile.routing = {}
            loaded_client_profile.routing["final"] = final_route
        
        # Set exclude outbounds if provided
        if exclude_outbounds:
            exclude_list = [o.strip() for o in exclude_outbounds.split(',') if o.strip()]
            loaded_client_profile.exclude_outbounds = exclude_list
        
        typer.echo("✅ Applied routing and filtering parameters")
    
    # Create postprocessor and middleware chains if provided
    postprocessor_chain = None
    middleware_chain = []
    
    if postprocessors_list:
        try:
            postprocessor_chain = _create_postprocessor_chain_from_list(postprocessors_list)
        except typer.Exit:
            raise  # Re-raise to preserve exit code
    
    if middleware_list:
        try:
            middleware_chain = _create_middleware_chain_from_list(middleware_list)
        except typer.Exit:
            raise  # Re-raise to preserve exit code
    
    # Determine output format
    output_format = _determine_output_format(output, format)
    
    # Generate configuration from subscription
    config_data = _generate_config_from_subscription(
        url, user_agent, no_user_agent, export_format, debug, loaded_profile, loaded_client_profile
    )
    
    # Handle dry-run mode
    if dry_run:
        typer.echo("🔍 " + t("cli.dry_run_mode"))
        with tempfile.NamedTemporaryFile("w+", suffix=f".{output_format}", delete=False) as tmp:
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
            success = _run_agent_check(temp_path, True)
            exit_code = 0 if success else 1
        finally:
            os.unlink(temp_path)
            typer.echo("🗑️  Temporary file deleted")
            
        raise typer.Exit(exit_code)
    
    # Default mode: Generate and save configuration
    # Create backup if requested
    _create_backup_if_needed(output, backup)
    
    # Write configuration to file
    _write_config_to_file(config_data, output, output_format)
    
    # Note: Following ADR-0014, we do NOT restart services here
    # That's sboxagent's responsibility
    typer.echo("✅ " + t("cli.update_completed"))
    typer.echo("ℹ️  Note: Use sboxagent to apply configuration to services")


# Create Typer app for export commands
app = typer.Typer(help="Export configurations in standardized formats")
app.command()(export)