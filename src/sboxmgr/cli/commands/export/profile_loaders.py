"""Profile loaders for export command."""

import json
import os
from typing import Optional

import typer

from sboxmgr.i18n.t import t
from sboxmgr.subscription.models import ClientProfile, InboundProfile

# Import Phase 3 components
try:
    from sboxmgr.profiles.models import FullProfile
    PHASE3_AVAILABLE = True
except ImportError:
    PHASE3_AVAILABLE = False
    FullProfile = None


def load_profile_from_file(profile_path: str) -> Optional['FullProfile']:
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


def load_client_profile_from_file(client_profile_path: str) -> Optional['ClientProfile']:
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


def create_client_profile_from_profile(profile: Optional['FullProfile']) -> Optional['ClientProfile']:
    """Create ClientProfile from FullProfile export settings.
    
    Args:
        profile: FullProfile with export settings
        
    Returns:
        ClientProfile with inbounds configured from profile, or None if no profile
    """
    if not profile or not hasattr(profile, 'export') or not profile.export:
        return None
    
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
                listen="127.0.0.1",
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
                listen="127.0.0.1",
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
                listen="127.0.0.1",
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
                    listen="127.0.0.1",
                    port=12345,
                    options={
                        "tag": "tproxy-in",
                        "network": ["tcp", "udp"],
                        "sniff": True
                    }
                ),
                InboundProfile(
                    type="socks",
                    listen="127.0.0.1",
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
                    listen="127.0.0.1",
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


def load_profiles(
    profile: Optional[str],
    client_profile: Optional[str],
    inbound_types: Optional[str],
    **inbound_params
) -> tuple[Optional['FullProfile'], Optional['ClientProfile']]:
    """Load profiles from files or CLI parameters.
    
    Args:
        profile: Profile file path
        client_profile: Client profile file path
        inbound_types: Comma-separated inbound types
        **inbound_params: Additional inbound parameters
        
    Returns:
        Tuple of (loaded_profile, loaded_client_profile)
        
    Raises:
        typer.Exit: On loading failure
    """
    loaded_profile = None
    if profile:
        loaded_profile = load_profile_from_file(profile)
    
    loaded_client_profile = None
    if client_profile:
        loaded_client_profile = load_client_profile_from_file(client_profile)
    
    # Build client profile from CLI parameters if provided
    if inbound_types and not loaded_client_profile:
        from sboxmgr.cli.inbound_builder import build_client_profile_from_cli
        loaded_client_profile = build_client_profile_from_cli(
            inbound_types=inbound_types,
            **inbound_params
        )
    
    return loaded_profile, loaded_client_profile 