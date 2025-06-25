#!/usr/bin/env python3
"""CLI entry point for sboxmgr.

Allows running sboxmgr CLI via:
- python -m sboxmgr.cli
- sboxctl (if installed as package)
"""

from .main import app

if __name__ == "__main__":
    app() 