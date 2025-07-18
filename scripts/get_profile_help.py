#!/usr/bin/env python3
"""Get help for profile CLI commands."""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import profile CLI
from sboxmgr.configs.cli import app

if __name__ == "__main__":
    app()
