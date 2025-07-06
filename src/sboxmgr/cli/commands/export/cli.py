"""Main CLI command for export functionality."""

import typer

from sboxmgr.i18n.t import t
from sboxmgr.subscription.models import ClientProfile
from logsetup.setup import setup_logging

from .validators import validate_flag_combinations, validate_and_parse_cli_parameters
from .profile_loaders import load_profiles
from .mode_handlers import (
    handle_profile_generation,
    handle_validate_only_mode,
    handle_legacy_modes
)
from .file_handlers import create_backup_if_needed, write_config_to_file
from .config_generators import generate_config_from_subscription
from .chain_builders import create_postprocessor_chain_from_list, create_middleware_chain_from_list

# Import Phase 3 components
try:
    from sboxmgr.profiles.models import FullProfile
    PHASE3_AVAILABLE = True
except ImportError:
    PHASE3_AVAILABLE = False
    FullProfile = None


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
    # Setup logging
    setup_logging(debug_level=debug)
    
    # Handle profile generation mode (early exit)
    if generate_profile:
        handle_profile_generation(generate_profile, postprocessors, middleware)
    
    # Validate flag combinations
    validate_flag_combinations(dry_run, agent_check, validate_only, url)
    
    # Handle validate-only mode
    if validate_only:
        handle_validate_only_mode(output)
    
    # URL is required for other modes
    if not url:
        typer.echo(f"❌ {t('cli.error.subscription_url_required')}", err=True)
        raise typer.Exit(1)
    
    # Validate and parse CLI parameters
    postprocessors_list, middleware_list = validate_and_parse_cli_parameters(
        postprocessors, middleware, final_route, exclude_outbounds
    )
    
    # Load profiles
    loaded_profile, loaded_client_profile = load_profiles(
        profile, client_profile, inbound_types,
        tun_address=tun_address, tun_mtu=tun_mtu, tun_stack=tun_stack,
        socks_port=socks_port, socks_listen=socks_listen, socks_auth=socks_auth,
        http_port=http_port, http_listen=http_listen, http_auth=http_auth,
        tproxy_port=tproxy_port, tproxy_listen=tproxy_listen,
        dns_mode=dns_mode
    )
    
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
    if postprocessors_list:
        create_postprocessor_chain_from_list(postprocessors_list)
    
    if middleware_list:
        create_middleware_chain_from_list(middleware_list)
    
    # Handle different execution modes
    if dry_run or agent_check:
        # Use legacy mode handlers for compatibility
        handle_legacy_modes(
            dry_run, agent_check, url, user_agent, no_user_agent,
            export_format, debug, loaded_profile, loaded_client_profile,
            output, format
        )
    else:
        # Default mode: Generate and save configuration
        from .file_handlers import determine_output_format
        
        # Create backup if requested
        create_backup_if_needed(output, backup)
        
        # Generate configuration
        config_data = generate_config_from_subscription(
            url, user_agent, no_user_agent, export_format, debug,
            loaded_profile, loaded_client_profile
        )
        
        # Determine output format and write
        output_format = determine_output_format(output, format)
        write_config_to_file(config_data, output, output_format)
        
        # Note: Following ADR-0014, we do NOT restart services here
        # That's sboxagent's responsibility
        typer.echo("✅ " + t("cli.update_completed"))
        typer.echo("ℹ️  Note: Use sboxagent to apply configuration to services")


# Create Typer app for export commands
app = typer.Typer(help="Export configurations in standardized formats")
app.command()(export)
