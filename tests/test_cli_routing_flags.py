"""Test CLI routing and filtering flags."""

import pytest
from typer.testing import CliRunner

from sboxmgr.cli.commands.export.cli import app as export_app


@pytest.fixture(autouse=True)
def mock_all_fetchers_and_parser():
    import base64
    from unittest.mock import Mock, patch
    valid_data = b"ss://YWVzLTI1Ni1nY206cGFzc0BleGFtcGxlLmNvbTo4Mzg4#test"
    encoded = base64.b64encode(valid_data)
    # Mock fetchers
    with patch('sboxmgr.subscription.fetchers.apifetcher.ApiFetcher.fetch') as mock_api, \
         patch('sboxmgr.subscription.fetchers.file_fetcher.FileFetcher.fetch') as mock_file, \
         patch('sboxmgr.subscription.manager.parser_detector.detect_parser') as mock_parser:
        mock_api.return_value = encoded
        mock_file.return_value = encoded
        # Mock parser to always return a valid server list
        mock_server = Mock()
        mock_server.type = "ss"
        parser_instance = Mock()
        parser_instance.parse.return_value = [mock_server]
        mock_parser.return_value = parser_instance
        yield

class TestCLIRoutingFlags:
    """Test CLI routing and filtering flags functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()

    @pytest.mark.skip(reason="TODO: CLI tests require deeper analysis of architecture and mocking strategy. Will be addressed in separate branch.")
    def test_final_route_flag(self):
        """Test --final-route flag functionality."""
        result = self.runner.invoke(export_app, ["--url", "https://example.com", "--final-route", "direct"])
        assert result.exit_code == 0
        assert "Applied routing" in result.stdout or "✅" in result.stdout

    @pytest.mark.skip(reason="TODO: CLI tests require deeper analysis of architecture and mocking strategy. Will be addressed in separate branch.")
    def test_exclude_outbounds_flag(self):
        """Test --exclude-outbounds flag functionality."""
        result = self.runner.invoke(export_app, ["--url", "https://example.com", "--exclude-outbounds", "vmess,ss"])
        assert result.exit_code == 0
        assert "Applied routing" in result.stdout or "✅" in result.stdout

    @pytest.mark.skip(reason="TODO: CLI tests require deeper analysis of architecture and mocking strategy. Will be addressed in separate branch.")
    def test_combined_routing_flags(self):
        """Test combination of routing flags."""
        result = self.runner.invoke(
            export_app,
            ["--url", "https://example.com", "--final-route", "direct", "--exclude-outbounds", "vmess"]
        )
        assert result.exit_code == 0
        assert "Applied routing" in result.stdout or "✅" in result.stdout

    @pytest.mark.skip(reason="TODO: CLI tests require deeper analysis of architecture and mocking strategy. Will be addressed in separate branch.")
    def test_routing_flags_with_existing_client_profile(self):
        """Test routing flags with existing client profile."""
        result = self.runner.invoke(
            export_app,
            ["--url", "https://example.com", "--client-profile", "test", "--final-route", "auto"]
        )
        assert result.exit_code == 0
        assert "Applied routing" in result.stdout or "✅" in result.stdout

    def test_invalid_final_route(self):
        """Test invalid final route handling."""
        result = self.runner.invoke(export_app, ["--url", "https://example.com", "--final-route", "invalid"])
        assert result.exit_code != 0

    @pytest.mark.skip(reason="TODO: CLI tests require deeper analysis of architecture and mocking strategy. Will be addressed in separate branch.")
    def test_empty_exclude_outbounds(self):
        """Test empty exclude outbounds handling."""
        result = self.runner.invoke(export_app, ["--url", "https://example.com", "--exclude-outbounds", ""])
        assert result.exit_code == 0
        assert "Applied routing" in result.stdout or "✅" in result.stdout
