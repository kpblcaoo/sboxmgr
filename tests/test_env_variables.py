import os
import pytest
from unittest.mock import patch
from sboxmgr.utils.env import (
    get_fetch_timeout, 
    get_fetch_size_limit,
    get_log_file,
    get_config_file,
    get_debug_level
)

class TestEnvironmentVariables:
    """Tests for environment variable utility functions."""

    def test_get_fetch_timeout_default(self):
        """Test that get_fetch_timeout returns default value."""
        with patch.dict(os.environ, {}, clear=True):
            assert get_fetch_timeout() == 30

    def test_get_fetch_timeout_from_env(self):
        """Test that get_fetch_timeout reads from environment variable."""
        with patch.dict(os.environ, {"SBOXMGR_FETCH_TIMEOUT": "60"}):
            assert get_fetch_timeout() == 60

    def test_get_fetch_timeout_invalid_env(self):
        """Test that invalid environment value falls back to default."""
        with patch.dict(os.environ, {"SBOXMGR_FETCH_TIMEOUT": "invalid"}):
            assert get_fetch_timeout() == 30

    def test_get_fetch_timeout_empty_env(self):
        """Test that empty environment value falls back to default."""
        with patch.dict(os.environ, {"SBOXMGR_FETCH_TIMEOUT": ""}):
            assert get_fetch_timeout() == 30

    def test_get_fetch_size_limit_default(self):
        """Test that get_fetch_size_limit returns default value (2MB)."""
        with patch.dict(os.environ, {}, clear=True):
            assert get_fetch_size_limit() == 2097152  # 2MB

    def test_get_fetch_size_limit_from_env(self):
        """Test that get_fetch_size_limit reads from environment variable."""
        with patch.dict(os.environ, {"SBOXMGR_FETCH_SIZE_LIMIT": "1048576"}):  # 1MB
            assert get_fetch_size_limit() == 1048576

    def test_get_fetch_size_limit_invalid_env(self):
        """Test that invalid environment value falls back to default."""
        with patch.dict(os.environ, {"SBOXMGR_FETCH_SIZE_LIMIT": "invalid"}):
            assert get_fetch_size_limit() == 2097152

    def test_get_fetch_size_limit_empty_env(self):
        """Test that empty environment value falls back to default."""
        with patch.dict(os.environ, {"SBOXMGR_FETCH_SIZE_LIMIT": ""}):
            assert get_fetch_size_limit() == 2097152

    def test_all_env_functions_exist(self):
        """Regression test: ensure all expected environment functions exist."""
        # Test that functions are callable
        assert callable(get_fetch_timeout)
        assert callable(get_fetch_size_limit)
        assert callable(get_log_file)
        assert callable(get_config_file)
        assert callable(get_debug_level)

    def test_fetch_functions_return_integers(self):
        """Test that fetch-related functions return integer values."""
        assert isinstance(get_fetch_timeout(), int)
        assert isinstance(get_fetch_size_limit(), int)
        assert get_fetch_timeout() > 0
        assert get_fetch_size_limit() > 0

    def test_environment_precedence(self):
        """Test that environment variables take precedence over defaults."""
        # Test timeout
        with patch.dict(os.environ, {"SBOXMGR_FETCH_TIMEOUT": "123"}):
            assert get_fetch_timeout() == 123
            
        # Test size limit  
        with patch.dict(os.environ, {"SBOXMGR_FETCH_SIZE_LIMIT": "456"}):
            assert get_fetch_size_limit() == 456
            
    def test_numeric_edge_cases(self):
        """Test handling of numeric edge cases."""
        # Zero values
        with patch.dict(os.environ, {"SBOXMGR_FETCH_TIMEOUT": "0"}):
            assert get_fetch_timeout() == 0
            
        with patch.dict(os.environ, {"SBOXMGR_FETCH_SIZE_LIMIT": "0"}):
            assert get_fetch_size_limit() == 0
            
        # Large values
        with patch.dict(os.environ, {"SBOXMGR_FETCH_TIMEOUT": "3600"}):  # 1 hour
            assert get_fetch_timeout() == 3600
            
        with patch.dict(os.environ, {"SBOXMGR_FETCH_SIZE_LIMIT": "104857600"}):  # 100MB
            assert get_fetch_size_limit() == 104857600 