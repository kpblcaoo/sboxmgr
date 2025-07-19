#!/usr/bin/env python3
"""Test script for exclusions help."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from sboxmgr.cli.commands.subscription.exclusions import app

if __name__ == "__main__":
    app()
