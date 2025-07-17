"""Test file to verify ruff catches unresolved imports."""

# This import should cause F404 error if package is not in dependencies


def test_function():
    """Test function."""
    return "test"
