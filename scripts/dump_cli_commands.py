#!/usr/bin/env python3
"""Script to dump all CLI commands and their help outputs.

This script automatically discovers and documents all available CLI commands
by recursively traversing the command tree and capturing help output.
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional


def run_command(cmd: List[str]) -> str:
    """Run a command and return its output.

    Args:
        cmd: Command to run as list of arguments

    Returns:
        Command output as string

    Raises:
        subprocess.CalledProcessError: If command fails
    """
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            cwd=Path(__file__).parent.parent
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error running command: {e}\n{e.stderr}"


def get_main_help() -> str:
    """Get main CLI help output."""
    return run_command([sys.executable, "-m", "src.sboxmgr.cli.main", "--help"])


def get_command_help(command: str, show_details: bool = False) -> str:
    """Get help output for a specific command.

    Args:
        command: Command to get help for (e.g., "profile", "export")
        show_details: Whether to try --show-details flag

    Returns:
        Help output as string
    """
    cmd = [sys.executable, "-m", "src.sboxmgr.cli.main", command, "--help"]
    if show_details:
        cmd.append("--show-details")
    return run_command(cmd)


def get_subcommand_help(command: str, subcommand: str, show_details: bool = False) -> str:
    """Get help output for a specific subcommand.

    Args:
        command: Main command (e.g., "profile")
        subcommand: Subcommand (e.g., "list", "show")
        show_details: Whether to try --show-details flag

    Returns:
        Help output as string
    """
    cmd = [sys.executable, "-m", "src.sboxmgr.cli.main", command, subcommand, "--help"]
    if show_details:
        cmd.append("--show-details")
    return run_command(cmd)


def extract_subcommands(help_output: str) -> List[str]:
    """Extract subcommand names from help output.

    Args:
        help_output: Help output to parse

    Returns:
        List of subcommand names
    """
    subcommands = []
    in_commands_section = False

    for line in help_output.split('\n'):
        line = line.strip()

        # Look for Commands section
        if 'Commands' in line and '─' in line:
            in_commands_section = True
            continue

        # End of commands section
        if in_commands_section and (line.startswith('╰') or line.startswith('─')):
            in_commands_section = False
            continue

        # Extract subcommand names - improved parsing
        if in_commands_section and line and line.startswith('│'):
            # Remove the │ prefix and extract command name
            content = line[1:].strip()
            if content and not content.startswith('─'):
                # Split by spaces and take first word
                parts = content.split()
                if parts:
                    cmd_name = parts[0]
                    # More robust validation
                    if (cmd_name and
                        not cmd_name.startswith('─') and
                        not cmd_name.startswith('(') and
                        not cmd_name.endswith(')') and
                        len(cmd_name) > 0 and
                        cmd_name.isidentifier()):  # Ensure it's a valid identifier
                        subcommands.append(cmd_name)

    return subcommands


def dump_command_tree(show_details: bool = False) -> str:
    """Dump the complete CLI command tree with help outputs.

    Args:
        show_details: Whether to try --show-details flag for detailed help

    Returns:
        Formatted markdown documentation
    """
    output = []

    # Main help
    output.append("# SboxMgr CLI Commands Reference\n")
    output.append("This document contains all available CLI commands and their help outputs.\n")

    # Cache main help to avoid calling twice
    main_help = get_main_help()

    output.append("## 🔹 Main CLI Help\n")
    output.append("```")
    output.append(main_help)
    output.append("```\n")

    # Get main commands from help
    main_commands = extract_subcommands(main_help)

    # Process each main command
    total_subcommands = 0
    command_stats = []

    for cmd in main_commands:
        output.append(f"## 🔹 Command: `sboxctl {cmd}`\n")

        # Get command help
        cmd_help = get_command_help(cmd, show_details)
        output.append("```")
        output.append(cmd_help)
        output.append("```\n")

        # Get subcommands
        subcommands = extract_subcommands(cmd_help)
        total_subcommands += len(subcommands)
        command_stats.append((cmd, len(subcommands)))

        # Process each subcommand
        for subcmd in subcommands:
            output.append(f"### 🔸 Subcommand: `sboxctl {cmd} {subcmd}`\n")
            subcmd_help = get_subcommand_help(cmd, subcmd, show_details)
            output.append("```")
            output.append(subcmd_help)
            output.append("```\n")
            output.append("---\n")

    # Add summary
    output.append("\n# 📊 CLI Commands Statistics\n")
    output.append(f"- **Total main commands**: {len(main_commands)}\n")
    output.append(f"- **Total subcommands**: {total_subcommands}\n")
    output.append(f"- **Total commands**: {len(main_commands) + total_subcommands}\n")
    output.append(f"- **Show details**: {show_details}\n")
    output.append(f"- **Generated**: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    output.append("\n## Command Groups Overview\n")
    for cmd, subcmd_count in command_stats:
        output.append(f"- **`sboxctl {cmd}`**: {subcmd_count} subcommands\n")

    return '\n'.join(output)


def main():
    """Main function to generate CLI documentation."""
    parser = argparse.ArgumentParser(
        description="Generate CLI command documentation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                           # Generate to tmp/cli_dump.md
  %(prog)s --output docs/cli.md      # Generate to specific file
  %(prog)s --output -                # Output to stdout
        """
    )
    parser.add_argument(
        '--output',
        default="tmp/cli_dump.md",
        help="Output markdown file (default: tmp/cli_dump.md, use '-' for stdout)"
    )
    parser.add_argument(
        '--show-details',
        action='store_true',
        help="Try to get detailed help with --show-details flag (if supported)"
    )

    args = parser.parse_args()

    # Handle stdout output
    if args.output == '-':
        output_file = None
        print("Generating CLI command documentation to stdout...")
    else:
        output_file = Path(args.output)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        print(f"Generating CLI command documentation to {output_file}...")

    try:
        content = dump_command_tree(args.show_details)

        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)

            print(f"✅ CLI documentation generated: {output_file}")
            print(f"📄 File size: {output_file.stat().st_size} bytes")
        else:
            print(content)

    except Exception as e:
        print(f"❌ Error generating documentation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
