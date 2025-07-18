import json
import os
from unittest.mock import patch

import pytest

from sboxmgr.subscription.parsers.json_parser import JSONParser, TolerantJSONParser


def test_json_parser():
    example_path = os.path.join(
        os.path.dirname(__file__), "../src/sboxmgr/examples/example_json.json"
    )
    with open(example_path, "rb") as f:
        raw = f.read()
    parser = JSONParser()
    servers = parser.parse(raw)
    assert isinstance(servers, list)


def test_json_parser_debug_levels():
    """Test JSON parser with different debug levels."""
    parser = JSONParser()
    invalid_json = b'{"invalid": json}'

    # Test debug_level = 0 (no debug output)
    with patch(
        "sboxmgr.subscription.parsers.json_parser.get_debug_level", return_value=0
    ):
        with pytest.raises((json.JSONDecodeError, ValueError)):
            parser.parse(invalid_json)

    # Test debug_level = 1 (no output for > 1 check)
    with patch(
        "sboxmgr.subscription.parsers.json_parser.get_debug_level", return_value=1
    ):
        with pytest.raises((json.JSONDecodeError, ValueError)):
            parser.parse(invalid_json)

    # Test debug_level = 2 (should trigger debug output)
    with patch(
        "sboxmgr.subscription.parsers.json_parser.get_debug_level", return_value=2
    ):
        with patch("builtins.print") as mock_print:
            with pytest.raises((json.JSONDecodeError, ValueError)):
                parser.parse(invalid_json)
            mock_print.assert_called_once()
            assert "[WARN] JSON parse error:" in mock_print.call_args[0][0]


def test_tolerant_json_parser_debug_levels():
    """Test TolerantJSONParser with different debug levels."""
    parser = TolerantJSONParser()

    # JSON with comments
    json_with_comments = b"""
    // This is a comment
    {
        "valid": "json",
        "_comment": "should be removed"
    }
    """

    # Test debug_level = 0 (no debug output)
    with patch(
        "sboxmgr.subscription.parsers.json_parser.get_debug_level", return_value=0
    ):
        with patch("builtins.print") as mock_print:
            servers = parser.parse(json_with_comments)
            assert isinstance(servers, list)
            mock_print.assert_not_called()

    # Test debug_level = 1 (should trigger debug output for removed comments)
    with patch(
        "sboxmgr.subscription.parsers.json_parser.get_debug_level", return_value=1
    ):
        with patch("builtins.print") as mock_print:
            servers = parser.parse(json_with_comments)
            assert isinstance(servers, list)
            mock_print.assert_called()
            assert "Removed comments/fields:" in mock_print.call_args_list[0][0][0]


def test_tolerant_json_parser_error_debug():
    """Test TolerantJSONParser error handling with debug."""
    parser = TolerantJSONParser()
    invalid_json = b'{"still": invalid after cleaning}'

    # Test debug_level = 0 (no debug output)
    with patch(
        "sboxmgr.subscription.parsers.json_parser.get_debug_level", return_value=0
    ):
        with pytest.raises((json.JSONDecodeError, ValueError)):
            parser.parse(invalid_json)

    # Test debug_level = 1 (should trigger debug output for errors)
    with patch(
        "sboxmgr.subscription.parsers.json_parser.get_debug_level", return_value=1
    ):
        with patch("builtins.print") as mock_print:
            with pytest.raises((json.JSONDecodeError, ValueError)):
                parser.parse(invalid_json)
            mock_print.assert_called()
            assert "JSON parse error after cleaning:" in mock_print.call_args[0][0]


def test_tolerant_json_parser_comment_stripping():
    """Test comment stripping functionality."""
    parser = TolerantJSONParser()

    json_with_various_comments = b"""
    // Leading comment
    # Another leading comment
    {
        "key1": "value1", // inline comment
        "_comment": "this should be removed",
        "key2": "value2", # another inline comment
        "key3": "value3",
    }
    """

    # Should not raise exception
    with patch(
        "sboxmgr.subscription.parsers.json_parser.get_debug_level", return_value=0
    ):
        servers = parser.parse(json_with_various_comments)
        assert isinstance(servers, list)


def test_tolerant_json_parser_no_comments():
    """Test TolerantJSONParser with clean JSON (no comments to remove)."""
    parser = TolerantJSONParser()
    clean_json = b'{"clean": "json", "no": "comments"}'

    with patch(
        "sboxmgr.subscription.parsers.json_parser.get_debug_level", return_value=1
    ):
        with patch("builtins.print") as mock_print:
            servers = parser.parse(clean_json)
            assert isinstance(servers, list)
            # Should not print anything since no comments were removed
            mock_print.assert_not_called()
