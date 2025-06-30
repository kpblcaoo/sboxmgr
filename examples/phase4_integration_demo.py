"""CLI command for configuration export (sboxctl export) with Phase 4 enhancements.

This module implements the unified export command that replaces the previous
run and dry-run commands. It generates configurations from subscriptions and
exports them to various formats while following ADR-0014 principles:
- sboxmgr only generates configurations
- sboxagent handles service management  
- No direct service restart from sboxmgr

Phase 4 enhancements:
- Profile-based configuration with --profile flag
- PostProcessor chain configuration with --postprocessors flag
- Middleware chain configuration with --middleware flag
- Backward compatibility with existing export workflows
"""
import typer
import os
import json
import tempfile
from pathlib import Path
from typing import Optional, List, Dict, Any

from sboxmgr.subscription.manager import SubscriptionManager
from sboxmgr.subscription.models import SubscriptionSource, PipelineContext
from sboxmgr.server.exclusions import load_exclusions
from sboxmgr.i18n.t import t
from sboxmgr.utils.env import get_template_file, get_config_file, get_backup_file
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


def _determine_output_format(output_file: str, format_arg: str) -> str:
    """Determine output format from file extension or format argument.
    
    Args:
        output_file: Output file path
        format_arg: Format argument from CLI
        
    Returns:
        Determined output format (json or toml)
    """
    if format_arg == "auto":
        # Auto-detect from file extension
        if output_file.endswith(('.toml', '.tml')):
            return "toml"
        else:
            return "json"
    elif format_arg in ("json", "toml"):
        return format_arg
    else:
        typer.echo(f"❌ Error: Unsupported format '{format_arg}'. Use: json, toml, auto", err=True)
        raise typer.Exit(1)


def _create_backup_if_needed(output_file: str, backup: bool) -> Optional[str]:
    """Create backup of existing output file if requested.
    
    Args:
        output_file: Output file path
        backup: Whether to create backup
        
    Returns:
        Backup file path or None
    """
    if backup and os.path.exists(output_file):
        backup_file = f"{output_file}.backup"
        import shutil
        shutil.copy2(output_file, backup_file)
        typer.echo(f"📁 Backup created: {backup_file}")
        return backup_file
    return None


def _run_agent_check(config_file: str, delete_after: bool = False) -> bool:
    """Run configuration check via sboxagent.
    
    Args:
        config_file: Configuration file to check
        delete_after: Whether to delete file after check
        
    Returns:
        True if check passed, False otherwise
    """
    try:
        bridge = AgentBridge()
        result = bridge.check_config(config_file, ClientType.SING_BOX)
        
        if result.success:
            typer.echo("✅ Configuration check passed via sboxagent")
            return True
        else:
            typer.echo("❌ Configuration check failed via sboxagent", err=True)
            typer.echo(f"Error: {result.error}", err=True)
            return False
            
    except AgentNotAvailableError:
        typer.echo("⚠️  sboxagent not available, falling back to file validation", err=True)
        try:
            validate_config_file(config_file)
            typer.echo("✅ File validation passed")
            return True
        except Exception as e:
            typer.echo(f"❌ File validation failed: {e}", err=True)
            return False
    except Exception as e:
        typer.echo(f"❌ Agent check failed: {e}", err=True)
        return False


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
        typer.echo(f"❌ Profile file not found: {profile_path}", err=True)
        raise typer.Exit(1)
    
    try:
        with open(profile_path, 'r', encoding='utf-8') as f:
            profile_data = json.load(f)
        
        # Create FullProfile from loaded data
        profile = FullProfile(**profile_data)
        typer.echo(f"✅ Profile loaded: {profile_path}")
        return profile
        
    except Exception as e:
        typer.echo(f"❌ Failed to load profile: {e}", err=True)
        raise typer.Exit(1)


def _create_postprocessor_chain_from_list(processors: List[str]) -> Optional['PostProcessorChain']:
    """Create PostProcessorChain from list of processor names.
    
    Args:
        processors: List of processor names (geo_filter, tag_filter, latency_sort)
        
    Returns:
        Configured PostProcessorChain or None
    """
    if not PHASE3_AVAILABLE:
        typer.echo("⚠️  PostProcessor chains require Phase 3 components", err=True)
        return None
    
    processor_instances = []
    processor_map = {
        'geo_filter': GeoFilterPostProcessor,
        'tag_filter': TagFilterPostProcessor,
        'latency_sort': LatencySortPostProcessor
    }
    
    for proc_name in processors:
        if proc_name in processor_map:
            # Use default configuration for CLI-specified processors
            processor_instances.append(processor_map[proc_name]({}))
            typer.echo(f"✅ Added postprocessor: {proc_name}")
        else:
            typer.echo(f"⚠️  Unknown postprocessor: {proc_name}", err=True)
    
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
    """
    if not PHASE3_AVAILABLE:
        typer.echo("⚠️  Middleware chains require Phase 3 components", err=True)
        return []
    
    middleware_instances = []
    middleware_map = {
        'logging': LoggingMiddleware,
        'enrichment': EnrichmentMiddleware
    }
    
    for mw_name in middleware:
        if mw_name in middleware_map:
            # Use default configuration for CLI-specified middleware
            middleware_instances.append(middleware_map[mw_name]({}))
            typer.echo(f"✅ Added middleware: {mw_name}")
        else:
            typer.echo(f"⚠️  Unknown middleware: {mw_name}", err=True)
    
    return middleware_instances


def _generate_config_from_subscription(
    url: str,
    user_agent: Optional[str],
    no_user_agent: bool,
    format: str,
    debug: int,
    skip_version_check: bool,
    profile: Optional[FullProfile] = None,
    postprocessors: Optional[List[str]] = None,
    middleware: Optional[List[str]] = None
) -> dict:
    """Generate configuration from subscription URL with Phase 3 processing.
    
    Args:
        url: Subscription URL
        user_agent: Custom User-Agent header
        no_user_agent: Disable User-Agent header
        format: Export format
        debug: Debug level
        skip_version_check: Skip version compatibility check
        profile: Optional FullProfile for processing
        postprocessors: Optional list of postprocessor names
        middleware: Optional list of middleware names
        
    Returns:
        Generated configuration dictionary
        
    Raises:
        typer.Exit: If subscription processing fails
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
        user_routes: List[str] = []
        
        # Create ExportManager with Phase 3 components
        export_mgr = ExportManager(export_format=format)
        
        # Configure Phase 3 components if available
        if PHASE3_AVAILABLE:
            # Configure from profile if provided
            if profile:
                export_mgr = export_mgr.configure_from_profile(profile)
                typer.echo("🔧 Configured export manager from profile")
            
            # Override with CLI-specified components
            if postprocessors:
                postprocessor_chain = _create_postprocessor_chain_from_list(postprocessors)
                if postprocessor_chain:
                    export_mgr.postprocessor_chain = postprocessor_chain
            
            if middleware:
                middleware_chain = _create_middleware_chain_from_list(middleware)
                if middleware_chain:
                    export_mgr.middleware_chain = middleware_chain
            
            # Show Phase 3 configuration
            if export_mgr.has_phase3_components:
                metadata = export_mgr.get_processing_metadata()
                typer.echo(f"🔧 Phase 3 processing enabled:")
                if metadata['has_postprocessor_chain']:
                    typer.echo(f"   - PostProcessor chain: ✅")
                if metadata['middleware_count'] > 0:
                    typer.echo(f"   - Middleware: {', '.join(metadata['middleware_types'])}")
        
        config = mgr.export_config(
            exclusions=exclusions, 
            user_routes=user_routes, 
            context=context, 
            export_manager=export_mgr, 
            skip_version_check=skip_version_check
        )
        
        if not config.success or not config.config or not config.config.get("outbounds"):
            typer.echo("❌ ERROR: No servers parsed from subscription", err=True)
            raise typer.Exit(1)
            
        return config.config
        
    except Exception as e:
        typer.echo(f"❌ {t('error.subscription_failed')}: {e}", err=True)
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


def export(
    url: str = typer.Option(
        None, "-u", "--url", help=t("cli.url.help"),
        envvar=["SBOXMGR_URL", "SINGBOX_URL", "TEST_URL"]
    ),
    debug: int = typer.Option(0, "-d", "--debug", help=t("cli.debug.help")),
    dry_run: bool = typer.Option(False, "--dry-run", help="Validate configuration without saving"),
    output: str = typer.Option("config.json", "--output", help="Output file path (ignored in dry-run and agent-check modes)"),
    format: str = typer.Option("json", "--format", help="Output format: json, toml, auto"),
    validate_only: bool = typer.Option(False, "--validate-only", help="Only validate existing configuration file"),
    agent_check: bool = typer.Option(False, "--agent-check", help="Check configuration via sboxagent without saving"),
    backup: bool = typer.Option(False, "--backup", help="Create backup before overwriting existing file"),
    user_agent: str = typer.Option(None, "--user-agent", help="Override User-Agent for subscription fetcher"),
    no_user_agent: bool = typer.Option(False, "--no-user-agent", help="Do not send User-Agent header"),
    skip_version_check: bool = typer.Option(True, "--skip-version-check", help="Skip sing-box version compatibility check"),
    # Phase 4 enhancements
    profile: str = typer.Option(None, "--profile", help="Profile JSON file for Phase 3 processing configuration"),
    postprocessors: str = typer.Option(None, "--postprocessors", help="Comma-separated list of postprocessors (geo_filter,tag_filter,latency_sort)"),
    middleware: str = typer.Option(None, "--middleware", help="Comma-separated list of middleware (logging,enrichment)")
):
    """Export configuration with various modes and Phase 4 enhancements.
    
    This unified command replaces the previous run and dry-run commands while
    following ADR-0014 principles. It generates configurations from subscriptions
    and exports them to various formats without managing services directly.
    
    Phase 4 enhancements:
    - Profile-based configuration with --profile flag
    - PostProcessor chain configuration with --postprocessors flag  
    - Middleware chain configuration with --middleware flag
    - Backward compatibility with existing export workflows
    
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
        validate_only: Only validate existing configuration
        agent_check: Check via sboxagent without applying
        backup: Create backup before overwriting
        user_agent: Custom User-Agent header
        no_user_agent: Disable User-Agent header
        skip_version_check: Skip version compatibility check
        profile: Profile JSON file for Phase 3 processing
        postprocessors: Comma-separated postprocessor list
        middleware: Comma-separated middleware list
        
    Raises:
        typer.Exit: On validation failure or processing errors
    """
    from logsetup.setup import setup_logging
    setup_logging(debug_level=debug)
    
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
        typer.echo("❌ Error: Subscription URL is required (use -u/--url)", err=True)
        raise typer.Exit(1)
    
    # Determine output format
    output_format = _determine_output_format(output, format)
    
    # Load profile if specified
    profile_obj = None
    if profile:
        profile_obj = _load_profile_from_file(profile)
    
    # Parse postprocessors and middleware lists
    postprocessors_list = None
    if postprocessors:
        postprocessors_list = [p.strip() for p in postprocessors.split(',') if p.strip()]
        if postprocessors_list:
            typer.echo(f"🔧 Postprocessors: {', '.join(postprocessors_list)}")
    
    middleware_list = None
    if middleware:
        middleware_list = [m.strip() for m in middleware.split(',') if m.strip()]
        if middleware_list:
            typer.echo(f"🔧 Middleware: {', '.join(middleware_list)}")
    
    # Generate configuration from subscription with Phase 3 processing
    config_data = _generate_config_from_subscription(
        url, user_agent, no_user_agent, "singbox", debug, skip_version_check,
        profile_obj, postprocessors_list, middleware_list
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
    backup_file = _create_backup_if_needed(output, backup)
    
    # Write configuration to file
    _write_config_to_file(config_data, output, output_format)
    
    # Note: Following ADR-0014, we do NOT restart services here
    # That's sboxagent's responsibility
    typer.echo("✅ " + t("cli.update_completed"))
    
    # Show Phase 3 processing summary if used
    if PHASE3_AVAILABLE and (profile_obj or postprocessors_list or middleware_list):
        typer.echo("\n🔧 Phase 3 Processing Summary:")
        if profile_obj:
            typer.echo(f"   - Profile: {profile}")
        if postprocessors_list:
            typer.echo(f"   - PostProcessors: {', '.join(postprocessors_list)}")
        if middleware_list:
            typer.echo(f"   - Middleware: {', '.join(middleware_list)}")



# Create Typer app for export commands
app = typer.Typer(help="Export configurations in standardized formats with Phase 4 enhancements")
app.command()(export)