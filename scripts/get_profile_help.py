#!/usr/bin/env python3
"""Script to get profile CLI help."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# Initialize logging first
from sboxmgr.logging.core import initialize_logging

initialize_logging()

# Now import profile CLI
from sboxmgr.configs.cli import app

if __name__ == "__main__":
    app()
