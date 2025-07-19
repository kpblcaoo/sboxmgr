"""Base64 utility functions for subscription parsers.

This module provides common base64 operations used across different
subscription parsers to handle padding issues and decoding errors.
"""


def handle_base64_padding(b64_string: str) -> str:
    """Handle base64 padding issues by adding padding if needed.

    Args:
        b64_string: Base64 string that may need padding

    Returns:
        Properly padded base64 string

    """
    padding_needed = len(b64_string) % 4
    if padding_needed:
        return b64_string + "=" * (4 - padding_needed)
    return b64_string
