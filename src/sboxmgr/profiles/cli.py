"""CLI commands for profile management.

This module provides CLI commands for working with profiles:
- apply: Apply a profile
- validate: Validate a profile
- explain: Explain a profile
- diff: Compare profiles
- list: List available profiles
- switch: Switch active profile
"""

import json
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from .manager import ProfileManager
from .loader import ProfileLoader
from ..logging.core import get_logger

logger = get_logger(__name__)
console = Console()

app = typer.Typer()

@app.command()
def info(profile_path: str):
    """Show brief info about a profile file (structure, validity, errors)."""
    loader = ProfileLoader()
    try:
        info = loader.get_profile_info(profile_path)
        console.print("[bold blue]Profile Info:[/bold blue]")
        console.print(f"  [blue]Name:[/blue] {info['name']}")
        console.print(f"  [blue]Path:[/blue] {info['path']}")
        console.print(f"  [blue]Size:[/blue] {info['size']} bytes")
        console.print(f"  [blue]Modified:[/blue] {info['modified']}")
        console.print(f"  [blue]Format:[/blue] {info['format']}")
        console.print(f"  [blue]Sections:[/blue] {', '.join(info['sections'])}")
        status = "[green]✓ Valid[/green]" if info['valid'] else "[red]✗ Invalid[/red]"
        console.print(f"  [blue]Status:[/blue] {status}")
        if info['error']:
            console.print(f"  [red]Error:[/red] {info['error']}")
    except Exception as e:
        console.print(f"[red]Failed to get profile info: {e}[/red]")
        raise typer.Exit(1)

def apply_profile(profile_path: str, dry_run: bool = False) -> None:
    """Apply a profile.
    
    Args:
        profile_path: Path to the profile file
        dry_run: If True, don't actually apply the profile

    """
    try:
        manager = ProfileManager()
        loader = ProfileLoader()
        
        # Load and validate profile
        profile = loader.load_from_file(profile_path)
        validation_result = manager.validate_profile(profile)
        
        if not validation_result.valid:
            console.print("[red]Profile validation failed:[/red]")
            for error in validation_result.errors:
                console.print(f"  [red]• {error}[/red]")
            raise typer.Exit(1)
        
        if validation_result.warnings:
            console.print("[yellow]Profile warnings:[/yellow]")
            for warning in validation_result.warnings:
                console.print(f"  [yellow]• {warning}[/yellow]")
        
        if dry_run:
            console.print("[green]Profile would be applied (dry run):[/green]")
            console.print(f"  [blue]Name:[/blue] {profile.id}")
            console.print(f"  [blue]Path:[/blue] {profile_path}")
        else:
            # Set as active profile
            manager.set_active_profile(profile)
            console.print("[green]Profile applied successfully:[/green]")
            console.print(f"  [blue]Name:[/blue] {profile.id}")
            console.print(f"  [blue]Path:[/blue] {profile_path}")
        
    except FileNotFoundError:
        console.print(f"[red]Profile file not found: {profile_path}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Failed to apply profile: {e}[/red]")
        logger.error(f"Failed to apply profile {profile_path}: {e}")
        raise typer.Exit(1)


@app.command()
def validate(
    profile_path: str,
    verbose: bool = typer.Option(False, "--verbose", help="Show detailed validation info"),
    normalize: bool = typer.Option(False, "--normalize", help="Auto-fix profile before validation")
):
    """Validate a profile (optionally auto-fix with --normalize)."""
    try:
        manager = ProfileManager()
        loader = ProfileLoader()
        
        # Get profile info first
        info = loader.get_profile_info(profile_path)
        
        if not info['valid'] and not normalize:
            console.print("[red]Profile validation failed:[/red]")
            console.print(f"  [red]Error: {info['error']}[/red]")
            raise typer.Exit(1)
        
        # Load and (optionally) normalize profile
        with open(profile_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
        if normalize:
            raw_data = loader.normalize_profile(raw_data)
            console.print("[yellow]Profile normalized before validation[/yellow]")
        
        profile = loader.load_from_dict(raw_data)
        validation_result = manager.validate_profile(profile)
        
        if not validation_result.valid:
            console.print("[red]Profile validation failed:[/red]")
            for error in validation_result.errors:
                console.print(f"  [red]• {error}[/red]")
            raise typer.Exit(1)
        
        console.print("[green]Profile is valid![/green]")
        
        if verbose:
            console.print("\n[blue]Profile Information:[/blue]")
            console.print(f"  [blue]Name:[/blue] {info['name']}")
            console.print(f"  [blue]Path:[/blue] {info['path']}")
            console.print(f"  [blue]Size:[/blue] {info['size']} bytes")
            console.print(f"  [blue]Modified:[/blue] {info['modified']}")
            console.print(f"  [blue]Format:[/blue] {info['format']}")
            console.print(f"  [blue]Sections:[/blue] {', '.join(info['sections'])}")
        
        if validation_result.warnings:
            console.print("\n[yellow]Warnings:[/yellow]")
            for warning in validation_result.warnings:
                console.print(f"  [yellow]• {warning}[/yellow]")
                
    except FileNotFoundError:
        console.print(f"[red]Profile file not found: {profile_path}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Failed to validate profile: {e}[/red]")
        raise typer.Exit(1)


def explain_profile(profile_path: str) -> None:
    """Explain a profile structure and contents.
    
    Args:
        profile_path: Path to the profile file

    """
    try:
        loader = ProfileLoader()
        profile = loader.load_from_file(profile_path)
        
        # Create explanation panel
        explanation = []
        explanation.append(f"[bold blue]Profile: {profile.id}[/bold blue]")
        if profile.description:
            explanation.append(f"[blue]Description:[/blue] {profile.description}")
        explanation.append(f"[blue]Path:[/blue] {profile_path}")
        explanation.append("")
        
        # Explain each section
        if hasattr(profile, 'subscriptions') and profile.subscriptions:
            explanation.append("[bold green]Subscriptions:[/bold green]")
            explanation.append(f"  Count: {len(profile.subscriptions)}")
            for sub in profile.subscriptions:
                status = "✓ Enabled" if sub.enabled else "✗ Disabled"
                explanation.append(f"    • {sub.id} (priority: {sub.priority}) - {status}")
            explanation.append("")
        
        if hasattr(profile, 'export') and profile.export:
            explanation.append("[bold green]Export:[/bold green]")
            explanation.append(f"  Format: {profile.export.format}")
            explanation.append(f"  Output: {profile.export.output_file}")
            explanation.append(f"  Outbound: {profile.export.outbound_profile}")
            explanation.append(f"  Inbound: {profile.export.inbound_profile}")
            explanation.append("")
        
        if hasattr(profile, 'filters') and profile.filters:
            explanation.append("[bold green]Filters:[/bold green]")
            if profile.filters.exclude_tags:
                explanation.append(f"  Exclude tags: {', '.join(profile.filters.exclude_tags)}")
            if profile.filters.only_tags:
                explanation.append(f"  Only tags: {', '.join(profile.filters.only_tags)}")
            if profile.filters.exclusions:
                explanation.append(f"  Exclusions: {', '.join(profile.filters.exclusions)}")
            explanation.append(f"  Only enabled: {profile.filters.only_enabled}")
            explanation.append("")
        
        if hasattr(profile, 'routing') and profile.routing:
            explanation.append("[bold green]Routing:[/bold green]")
            explanation.append(f"  Default route: {profile.routing.default_route}")
            if profile.routing.by_source:
                explanation.append(f"  Source routes: {len(profile.routing.by_source)}")
            if profile.routing.custom_routes:
                explanation.append(f"  Custom routes: {len(profile.routing.custom_routes)}")
            explanation.append("")
        
        if hasattr(profile, 'agent') and profile.agent:
            explanation.append("[bold green]Agent:[/bold green]")
            explanation.append(f"  Auto restart: {profile.agent.auto_restart}")
            explanation.append(f"  Monitor latency: {profile.agent.monitor_latency}")
            explanation.append(f"  Health check: {profile.agent.health_check_interval}")
            explanation.append(f"  Log level: {profile.agent.log_level}")
            explanation.append("")
        
        if hasattr(profile, 'ui') and profile.ui:
            explanation.append("[bold green]UI:[/bold green]")
            explanation.append(f"  Language: {profile.ui.default_language}")
            explanation.append(f"  Mode: {profile.ui.mode}")
            if profile.ui.theme:
                explanation.append(f"  Theme: {profile.ui.theme}")
            explanation.append(f"  Debug info: {profile.ui.show_debug_info}")
            explanation.append("")
        
        # Display explanation
        panel = Panel("\n".join(explanation), title="Profile Explanation", border_style="blue")
        console.print(panel)
        
    except FileNotFoundError:
        console.print(f"[red]Profile file not found: {profile_path}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Failed to explain profile: {e}[/red]")
        raise typer.Exit(1)


def diff_profiles(profile1_path: str, profile2_path: str) -> None:
    """Compare two profiles.
    
    Args:
        profile1_path: Path to the first profile file
        profile2_path: Path to the second profile file

    """
    try:
        loader = ProfileLoader()
        profile1 = loader.load_from_file(profile1_path)
        profile2 = loader.load_from_file(profile2_path)
        
        # Convert to dictionaries for comparison
        dict1 = profile1.model_dump(mode='json')
        dict2 = profile2.model_dump(mode='json')
        
        # Simple comparison - in a real implementation, you'd want a more sophisticated diff
        console.print("[bold blue]Comparing profiles:[/bold blue]")
        console.print(f"  [blue]Profile 1:[/blue] {profile1.id} ({profile1_path})")
        console.print(f"  [blue]Profile 2:[/blue] {profile2.id} ({profile2_path})")
        console.print("")
        
        # Compare sections
        sections1 = set(dict1.keys())
        sections2 = set(dict2.keys())
        
        # Sections only in profile1
        only_in_1 = sections1 - sections2
        if only_in_1:
            console.print(f"[yellow]Sections only in profile 1:[/yellow] {', '.join(only_in_1)}")
        
        # Sections only in profile2
        only_in_2 = sections2 - sections1
        if only_in_2:
            console.print(f"[yellow]Sections only in profile 2:[/yellow] {', '.join(only_in_2)}")
        
        # Common sections
        common_sections = sections1 & sections2
        if common_sections:
            console.print(f"[green]Common sections:[/green] {', '.join(common_sections)}")
            
            # Compare common sections
            for section in common_sections:
                if dict1[section] != dict2[section]:
                    console.print(f"  [red]Section '{section}' differs[/red]")
                else:
                    console.print(f"  [green]Section '{section}' identical[/green]")
        
        if not only_in_1 and not only_in_2 and all(dict1[section] == dict2[section] for section in common_sections):
            console.print("\n[green]Profiles are identical![/green]")
        
    except FileNotFoundError as e:
        console.print(f"[red]Profile file not found: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Failed to compare profiles: {e}[/red]")
        logger.error(f"Failed to compare profiles: {e}")
        raise typer.Exit(1)


def list_profiles(profiles_dir: Optional[str] = None) -> None:
    """List available profiles.
    
    Args:
        profiles_dir: Directory to search for profiles

    """
    try:
        manager = ProfileManager(profiles_dir)
        profiles = manager.list_profiles()
        
        if not profiles:
            console.print(f"[yellow]No profiles found in {manager.profiles_dir}[/yellow]")
            return
        
        # Create table
        table = Table(title="Available Profiles")
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Path", style="blue")
        table.add_column("Size", style="green")
        table.add_column("Modified", style="yellow")
        table.add_column("Status", style="red")
        
        for profile in profiles:
            status = "[green]✓ Valid[/green]" if profile.valid else "[red]✗ Invalid[/red]"
            table.add_row(
                profile.name,
                str(profile.path),
                f"{profile.size} bytes",
                profile.modified.strftime("%Y-%m-%d %H:%M"),
                status
            )
        
        console.print(table)
        
        # Show invalid profiles details
        invalid_profiles = [p for p in profiles if not p.valid]
        if invalid_profiles:
            console.print("\n[yellow]Invalid profiles:[/yellow]")
            for profile in invalid_profiles:
                console.print(f"  [red]• {profile.name}: {profile.error}[/red]")
        
    except Exception as e:
        console.print(f"[red]Failed to list profiles: {e}[/red]")
        logger.error(f"Failed to list profiles: {e}")
        raise typer.Exit(1)


def switch_profile(profile_id: str, profiles_dir: Optional[str] = None) -> None:
    """Switch to a different active profile.
    
    Args:
        profile_id: Profile ID (name or path)
        profiles_dir: Directory to search for profiles

    """
    try:
        manager = ProfileManager(profiles_dir)
        
        # Try to find profile by name first
        profiles = manager.list_profiles()
        target_profile = None
        
        # Look for exact name match
        for profile in profiles:
            if profile.name == profile_id and profile.valid:
                target_profile = profile
                break
        
        # If not found by name, try as path
        if not target_profile:
            try:
                loader = ProfileLoader()
                profile = loader.load_from_file(profile_id)
                target_profile = type('ProfileInfo', (), {
                    'path': profile_id,
                    'name': Path(profile_id).stem,
                    'valid': True
                })()
            except:
                pass
        
        if not target_profile:
            console.print(f"[red]Profile not found: {profile_id}[/red]")
            console.print("[yellow]Available profiles:[/yellow]")
            for profile in profiles:
                if profile.valid:
                    console.print(f"  [blue]• {profile.name}[/blue]")
            raise typer.Exit(1)
        
        # Load and set active profile
        loader = ProfileLoader()
        profile = loader.load_from_file(target_profile.path)
        manager.set_active_profile(profile)
        
        console.print(f"[green]Switched to profile: {target_profile.name}[/green]")
        console.print(f"  [blue]Path:[/blue] {target_profile.path}")
        
    except Exception as e:
        console.print(f"[red]Failed to switch profile: {e}[/red]")
        logger.error(f"Failed to switch profile: {e}")
        raise typer.Exit(1)

@app.command()
def apply(
    profile_path: str,
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be applied without actually applying")
):
    """Apply a profile."""
    apply_profile(profile_path, dry_run)

@app.command()
def explain(profile_path: str):
    """Explain a profile structure and contents."""
    explain_profile(profile_path)

@app.command()
def diff(profile1_path: str, profile2_path: str):
    """Compare two profiles."""
    diff_profiles(profile1_path, profile2_path)

@app.command()
def list(profiles_dir: Optional[str] = typer.Option(None, "--dir", help="Profiles directory")):
    """List available profiles."""
    list_profiles(profiles_dir)

@app.command()
def switch(profile_id: str, profiles_dir: Optional[str] = typer.Option(None, "--dir", help="Profiles directory")):
    """Switch to a different profile."""
    switch_profile(profile_id, profiles_dir)
