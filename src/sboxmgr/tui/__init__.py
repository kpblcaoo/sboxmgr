"""TUI (Text User Interface) module for sboxmgr.

This module provides an interactive terminal user interface for sboxmgr,
designed with a focus on user experience and ease of use for newcomers.

Key features:
- Context-aware interface that shows only relevant options
- Step-by-step onboarding for new users
- Visual server management with checkboxes
- Integration with existing subscription management system
"""

__version__ = "0.1.0"
__all__ = ["SboxmgrTUI"]

try:
    from .app import SboxmgrTUI
except ImportError:
    # Graceful fallback if textual is not available
    SboxmgrTUI = None
