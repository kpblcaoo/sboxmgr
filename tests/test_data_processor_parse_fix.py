"""Test for data processor parse errors fix.

This test verifies that the parse_servers method correctly handles
empty server lists and invalid servers without raising parse errors,
and that debug logging is properly controlled.
"""

from unittest.mock import Mock, patch

from sboxmgr.subscription.manager.data_processor import DataProcessor
from sboxmgr.subscription.manager.pipeline_coordinator import PipelineContext


class MockParser:
    """Mock parser for testing."""

    def __init__(self, servers_to_return):
        self.servers_to_return = servers_to_return

    def parse(self, raw_data):
        return self.servers_to_return


class MockServer:
    """Mock server object for testing."""

    def __init__(self, address="valid.example.com"):
        self.address = address


def test_parse_servers_empty_list_success():
    """Test that empty server list is handled gracefully."""

    # Setup
    mock_fetcher = Mock()
    mock_fetcher.source.source_type = "test"
    mock_error_handler = Mock()

    processor = DataProcessor(mock_fetcher, mock_error_handler)
    context = PipelineContext(debug_level=0)

    # Mock parser that returns empty list
    mock_parser = MockParser([])

    with patch('sboxmgr.subscription.manager.data_processor.detect_parser', return_value=mock_parser):
        # Execute
        servers, success = processor.parse_servers(b"test_data", context)

        # Verify
        assert success is True
        assert servers == []
        # Should not create any parse errors
        mock_error_handler.create_parse_error.assert_not_called()


def test_parse_servers_all_invalid_success():
    """Test that all invalid servers are handled gracefully."""

    # Setup
    mock_fetcher = Mock()
    mock_fetcher.source.source_type = "test"
    mock_error_handler = Mock()

    processor = DataProcessor(mock_fetcher, mock_error_handler)
    context = PipelineContext(debug_level=0)

    # Mock parser that returns servers with invalid addresses
    invalid_servers = [MockServer("invalid"), MockServer("invalid")]
    mock_parser = MockParser(invalid_servers)

    with patch('sboxmgr.subscription.manager.data_processor.detect_parser', return_value=mock_parser):
        # Execute
        servers, success = processor.parse_servers(b"test_data", context)

        # Verify
        assert success is True
        assert len(servers) == 2
        assert all(s.address == "invalid" for s in servers)
        # Should not create any parse errors
        mock_error_handler.create_parse_error.assert_not_called()


def test_parse_servers_mixed_valid_invalid_success():
    """Test that mixed valid/invalid servers are handled correctly."""

    # Setup
    mock_fetcher = Mock()
    mock_fetcher.source.source_type = "test"
    mock_error_handler = Mock()

    processor = DataProcessor(mock_fetcher, mock_error_handler)
    context = PipelineContext(debug_level=0)

    # Mock parser that returns mixed servers
    mixed_servers = [
        MockServer("valid1.example.com"),
        MockServer("invalid"),
        MockServer("valid2.example.com")
    ]
    mock_parser = MockParser(mixed_servers)

    with patch('sboxmgr.subscription.manager.data_processor.detect_parser', return_value=mock_parser):
        # Execute
        servers, success = processor.parse_servers(b"test_data", context)

        # Verify
        assert success is True
        assert len(servers) == 3
        # Should not create any parse errors
        mock_error_handler.create_parse_error.assert_not_called()


def test_parse_servers_debug_logging_controlled():
    """Test that debug logging is properly controlled by debug_level."""

    # Setup
    mock_fetcher = Mock()
    mock_fetcher.source.source_type = "test"
    mock_error_handler = Mock()

    processor = DataProcessor(mock_fetcher, mock_error_handler)

    # Test with debug_level=0 (no debug output)
    context_low = PipelineContext(debug_level=0)
    mock_parser = MockParser([MockServer("test.example.com")])

    with patch('sboxmgr.subscription.manager.data_processor.detect_parser', return_value=mock_parser):
        with patch('builtins.print') as mock_print:
            # Execute
            servers, success = processor.parse_servers(b"test_data", context_low)

            # Verify no debug output
            assert success is True
            mock_print.assert_not_called()

    # Test with debug_level=2 (debug output enabled)
    context_high = PipelineContext(debug_level=2)

    with patch('sboxmgr.subscription.manager.data_processor.detect_parser', return_value=mock_parser):
        with patch('builtins.print') as mock_print:
            # Execute
            servers, success = processor.parse_servers(b"test_data", context_high)

            # Verify debug output is present
            assert success is True
            mock_print.assert_called()


def test_parse_servers_no_parser_error():
    """Test that missing parser still creates proper error."""

    # Setup
    mock_fetcher = Mock()
    mock_fetcher.source.source_type = "test"
    mock_error_handler = Mock()

    processor = DataProcessor(mock_fetcher, mock_error_handler)
    context = PipelineContext(debug_level=0)

    with patch('sboxmgr.subscription.manager.data_processor.detect_parser', return_value=None):
        # Execute
        servers, success = processor.parse_servers(b"test_data", context)

        # Verify
        assert success is False
        assert servers == []
        # Should create parse error for missing parser
        mock_error_handler.create_parse_error.assert_called_once()
        mock_error_handler.add_error_to_context.assert_called_once()


def test_parse_servers_parser_exception_error():
    """Test that parser exceptions are properly handled."""

    # Setup
    mock_fetcher = Mock()
    mock_fetcher.source.source_type = "test"
    mock_error_handler = Mock()

    processor = DataProcessor(mock_fetcher, mock_error_handler)
    context = PipelineContext(debug_level=0)

    # Mock parser that raises exception
    mock_parser = Mock()
    mock_parser.parse.side_effect = Exception("Parser failed")

    with patch('sboxmgr.subscription.manager.data_processor.detect_parser', return_value=mock_parser):
        # Execute
        servers, success = processor.parse_servers(b"test_data", context)

        # Verify
        assert success is False
        assert servers == []
        # Should create parse error for exception
        mock_error_handler.create_parse_error.assert_called_once()
        mock_error_handler.add_error_to_context.assert_called_once()
