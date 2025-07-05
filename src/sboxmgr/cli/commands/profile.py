"""CLI commands for profile management (ADR-0017, ADR-0019).

This module provides commands for applying, validating, and managing profiles.
"""

import json
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from sboxmgr.profiles.models import FullProfile, LegacyProfile, SubscriptionProfile, FilterProfile, ExportProfile
from sboxmgr.logging.core import get_logger

# Don't initialize logger at module level - it will be done in functions
console = Console()
app = typer.Typer(name="profile", help="Profile management commands")


@app.command()
def apply(
    profile_path: str = typer.Argument(..., help="Path to profile JSON file"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be applied without making changes"),
    override_subscription: Optional[str] = typer.Option(None, "--override-subscription", help="Override subscription URL"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Override output file path"),
) -> None:
    """Apply a profile configuration (ADR-0017)."""
    logger = get_logger(__name__)  # Initialize logger inside function
    
    try:
        # Load and validate profile
        profile = _load_profile(profile_path)
        
        if dry_run:
            _show_profile_preview(profile)
            return
        
        # Apply profile
        _apply_profile(profile, override_subscription, output)
        
        console.print(f"✅ Profile '{profile.id}' applied successfully", style="green")
        
    except Exception as e:
        logger.error(f"Failed to apply profile: {e}")
        console.print(f"❌ Error applying profile: {e}", style="red")
        sys.exit(1)


@app.command()
def validate(
    profile_path: str = typer.Argument(..., help="Path to profile JSON file"),
) -> None:
    """Validate a profile configuration."""
    logger = get_logger(__name__)
    
    try:
        profile = _load_profile(profile_path)
        console.print(f"✅ Profile '{profile.id}' is valid", style="green")
        
        # Show profile summary
        _show_profile_summary(profile)
        
    except Exception as e:
        logger.error(f"Profile validation failed: {e}")
        console.print(f"❌ Profile validation failed: {e}", style="red")
        sys.exit(1)


@app.command()
def explain(
    profile_path: str = typer.Argument(..., help="Path to profile JSON file"),
) -> None:
    """Explain what a profile does."""
    logger = get_logger(__name__)
    
    try:
        profile = _load_profile(profile_path)
        _show_profile_explanation(profile)
        
    except Exception as e:
        logger.error(f"Failed to explain profile: {e}")
        console.print(f"❌ Error explaining profile: {e}", style="red")
        sys.exit(1)


@app.command()
def diff(
    profile1: str = typer.Argument(..., help="First profile path or ID"),
    profile2: str = typer.Argument(..., help="Second profile path or ID"),
) -> None:
    """Show differences between two profiles."""
    logger = get_logger(__name__)
    
    try:
        # Load profiles
        prof1 = _load_profile(profile1)
        prof2 = _load_profile(profile2)
        
        _show_profile_diff(prof1, prof2)
        
    except Exception as e:
        logger.error(f"Failed to compare profiles: {e}")
        console.print(f"❌ Error comparing profiles: {e}", style="red")
        sys.exit(1)


@app.command()
def switch(
    profile_id: str = typer.Argument(..., help="Profile ID to switch to"),
) -> None:
    """Switch to a different profile (ADR-0019)."""
    logger = get_logger(__name__)
    
    try:
        # TODO: Implement ProfileStateManager
        console.print(f"🔄 Switching to profile '{profile_id}'...", style="yellow")
        
        # For now, just show what would happen
        console.print("⚠️  Profile switching not yet implemented", style="yellow")
        console.print("This will be implemented in Phase 8 (ADR-0019)", style="dim")
        
    except Exception as e:
        logger.error(f"Failed to switch profile: {e}")
        console.print(f"❌ Error switching profile: {e}", style="red")
        sys.exit(1)


@app.command()
def list() -> None:
    """List available profiles."""
    logger = get_logger(__name__)
    
    try:
        # TODO: Implement ProfileHistoryManager
        console.print("📋 Available profiles:", style="bold")
        
        # For now, show placeholder
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("ID", style="cyan")
        table.add_column("Description", style="green")
        table.add_column("Status", style="yellow")
        table.add_column("Last Used", style="dim")
        
        table.add_row("home", "Home profile with Pi-hole", "Active", "2025-06-29")
        table.add_row("work", "Work profile with VPN", "Inactive", "2025-06-28")
        table.add_row("china", "China-specific servers", "Inactive", "Never")
        
        console.print(table)
        console.print("\n⚠️  Profile listing not yet fully implemented", style="yellow")
        
    except Exception as e:
        logger.error(f"Failed to list profiles: {e}")
        console.print(f"❌ Error listing profiles: {e}", style="red")
        sys.exit(1)


def _load_profile(profile_path: str) -> FullProfile:
    """Load and validate a profile from file."""
    path = Path(profile_path)
    if not path.exists():
        raise FileNotFoundError(f"Profile file not found: {profile_path}")
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Try to parse as FullProfile first
        try:
            return FullProfile(**data)
        except Exception:
            # Try as LegacyProfile and convert
            legacy = LegacyProfile(**data)
            return _convert_legacy_profile(legacy)
            
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in profile file: {e}")
    except Exception as e:
        raise ValueError(f"Failed to load profile: {e}")


def _convert_legacy_profile(legacy: LegacyProfile) -> FullProfile:
    """Convert legacy profile to FullProfile format."""
    # Create subscription profiles from URLs
    subscriptions = []
    for i, url in enumerate(legacy.subscriptions):
        subscriptions.append(
            SubscriptionProfile(
                id=f"legacy_{i}",
                enabled=True,
                priority=i + 1
            )
        )
    
    # Create filter profile from exclusions
    filters = FilterProfile(
        exclusions=legacy.exclusions
    )
    
    # Create export profile
    export = ExportProfile(
        format=legacy.export_format
    )
    
    return FullProfile(
        id="converted_legacy",
        description="Converted from legacy format",
        subscriptions=subscriptions,
        filters=filters,
        export=export
    )


def _apply_profile(profile: FullProfile, override_subscription: Optional[str], output: Optional[str]) -> None:
    """Apply a profile configuration."""
    # TODO: Implement full profile application
    # For now, just show what would be applied
    
    console.print(f"📋 Applying profile '{profile.id}':", style="bold")
    console.print(f"  • Subscriptions: {len(profile.subscriptions)}")
    console.print(f"  • Export format: {profile.export.format}")
    console.print(f"  • Output file: {profile.export.output_file}")
    
    if override_subscription:
        console.print(f"  • Override subscription: {override_subscription}")
    
    if output:
        console.print(f"  • Override output: {output}")
    
    # TODO: Actually apply the profile
    console.print("⚠️  Profile application not yet fully implemented", style="yellow")


def _show_profile_preview(profile: FullProfile) -> None:
    """Show a preview of what the profile would do."""
    console.print(Panel(
        f"[bold]Profile Preview: {profile.id}[/bold]\n"
        f"Description: {profile.description or 'No description'}\n"
        f"Subscriptions: {len(profile.subscriptions)}\n"
        f"Export format: {profile.export.format}\n"
        f"Output file: {profile.export.output_file}",
        title="Profile Preview",
        border_style="blue"
    ))


def _show_profile_summary(profile: FullProfile) -> None:
    """Show a summary of the profile."""
    table = Table(title=f"Profile Summary: {profile.id}")
    table.add_column("Component", style="cyan")
    table.add_column("Details", style="green")
    
    table.add_row("ID", profile.id)
    table.add_row("Description", profile.description or "No description")
    table.add_row("Version", profile.version)
    table.add_row("Subscriptions", str(len(profile.subscriptions)))
    table.add_row("Export Format", profile.export.format.value)
    table.add_row("Output File", profile.export.output_file)
    
    console.print(table)


def _show_profile_explanation(profile: FullProfile) -> None:
    """Explain what the profile does."""
    console.print(Panel(
        f"[bold]What this profile does:[/bold]\n\n"
        f"• [cyan]Subscriptions:[/cyan] {len(profile.subscriptions)} subscription(s) will be processed\n"
        f"• [cyan]Filtering:[/cyan] {len(profile.filters.exclude_tags)} tags excluded, "
        f"{len(profile.filters.only_tags)} tags required\n"
        f"• [cyan]Routing:[/cyan] Default route: {profile.routing.default_route}\n"
        f"• [cyan]Export:[/cyan] Will generate {profile.export.format.value} config\n"
        f"• [cyan]Output:[/cyan] Will save to {profile.export.output_file}",
        title=f"Profile Explanation: {profile.id}",
        border_style="green"
    ))


def _show_profile_diff(profile1: FullProfile, profile2: FullProfile) -> None:
    """Show differences between two profiles."""
    console.print(Panel(
        f"[bold]Profile Comparison[/bold]\n\n"
        f"[cyan]{profile1.id}[/cyan] vs [cyan]{profile2.id}[/cyan]\n\n"
        f"• Subscriptions: {len(profile1.subscriptions)} vs {len(profile2.subscriptions)}\n"
        f"• Export format: {profile1.export.format.value} vs {profile2.export.format.value}\n"
        f"• Output file: {profile1.export.output_file} vs {profile2.export.output_file}",
        title="Profile Diff",
        border_style="yellow"
    )) 