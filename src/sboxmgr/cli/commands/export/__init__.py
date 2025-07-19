"""Export command module for sboxmgr CLI (ADR-0020).

This module provides a refactored, modular implementation of the export command
that generates configurations from subscriptions and exports them to various formats.

The module is organized into the following components:

- cli.py: Main CLI command interface (legacy)
- validators.py: Parameter validation functions
- profile_loaders.py: Profile loading utilities
- config_generators.py: Configuration generation functions
- file_handlers.py: File operations (read, write, backup)
- mode_handlers.py: Different operation mode handlers
- chain_builders.py: Postprocessor and middleware chain builders
- constants.py: Validation constants and defaults

New subcommand structure (ADR-0020):
- generate.py: Generate ClientConfig from FullProfile
- validate.py: Validate configurations
- dry_run.py: Test mode without saving
- profile.py: Export optimized FullProfile
"""

from .cli import app, export

__all__ = ["export", "app"]
