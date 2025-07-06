"""Test CLI routing and filtering flags."""

from typer.testing import CliRunner

from sboxmgr.cli.main import app


class TestCLIRoutingFlags:
    """Test CLI routing and filtering flags functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()

    def test_final_route_flag(self):
        """Test --final-route flag creates correct client profile."""
        # Mock the export function to capture the client profile
        from unittest.mock import patch

        with patch(
            "sboxmgr.cli.commands.export._generate_config_from_subscription"
        ) as mock_generate:
            mock_generate.return_value = {"test": "config"}

            result = self.runner.invoke(
                app,
                [
                    "export",
                    "--url",
                    "https://example.com/subscription",
                    "--final-route",
                    "direct",
                ],
            )

            # Check that the function was called with correct parameters
            assert mock_generate.called
            call_args = mock_generate.call_args
            # Function is called with positional arguments, client_profile is the 7th argument
            client_profile = call_args[0][6]  # 7th positional argument

            assert client_profile is not None
            assert client_profile.routing["final"] == "direct"

    def test_exclude_outbounds_flag(self):
        """Test --exclude-outbounds flag creates correct client profile."""
        from unittest.mock import patch

        with patch(
            "sboxmgr.cli.commands.export._generate_config_from_subscription"
        ) as mock_generate:
            mock_generate.return_value = {"test": "config"}

            result = self.runner.invoke(
                app,
                [
                    "export",
                    "--url",
                    "https://example.com/subscription",
                    "--exclude-outbounds",
                    "direct,block",
                ],
            )

            # Check that the function was called with correct parameters
            assert mock_generate.called
            call_args = mock_generate.call_args
            # Function is called with positional arguments, client_profile is the 7th argument
            client_profile = call_args[0][6]  # 7th positional argument

            assert client_profile is not None
            assert "direct" in client_profile.exclude_outbounds
            assert "block" in client_profile.exclude_outbounds

    def test_combined_routing_flags(self):
        """Test both --final-route and --exclude-outbounds flags together."""
        from unittest.mock import patch

        with patch(
            "sboxmgr.cli.commands.export._generate_config_from_subscription"
        ) as mock_generate:
            mock_generate.return_value = {"test": "config"}

            result = self.runner.invoke(
                app,
                [
                    "export",
                    "--url",
                    "https://example.com/subscription",
                    "--final-route",
                    "proxy",
                    "--exclude-outbounds",
                    "direct,block,dns",
                ],
            )

            # Check that the function was called with correct parameters
            assert mock_generate.called
            call_args = mock_generate.call_args
            # Function is called with positional arguments, client_profile is the 7th argument
            client_profile = call_args[0][6]  # 7th positional argument

            assert client_profile is not None
            assert client_profile.routing["final"] == "proxy"
            assert "direct" in client_profile.exclude_outbounds
            assert "block" in client_profile.exclude_outbounds
            assert "dns" in client_profile.exclude_outbounds

    def test_routing_flags_with_existing_client_profile(self):
        """Test that routing flags work with existing client profile."""
        import json
        import tempfile
        from unittest.mock import patch

        # Create a temporary client profile file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            client_profile_data = {
                "inbounds": [{"type": "socks", "listen": "127.0.0.1", "port": 1080}]
            }
            json.dump(client_profile_data, f)
            client_profile_path = f.name

        try:
            with patch(
                "sboxmgr.cli.commands.export._generate_config_from_subscription"
            ) as mock_generate:
                mock_generate.return_value = {"test": "config"}

                result = self.runner.invoke(
                    app,
                    [
                        "export",
                        "--url",
                        "https://example.com/subscription",
                        "--client-profile",
                        client_profile_path,
                        "--final-route",
                        "direct",
                    ],
                )

                # Check that the function was called with correct parameters
                assert mock_generate.called
                call_args = mock_generate.call_args
                # Function is called with positional arguments, client_profile is the 7th argument
                client_profile = call_args[0][6]  # 7th positional argument

                assert client_profile is not None
                assert client_profile.routing["final"] == "direct"
                # Should preserve existing inbounds
                assert len(client_profile.inbounds) == 1
                assert client_profile.inbounds[0].type == "socks"
        finally:
            import os

            os.unlink(client_profile_path)

    def test_invalid_final_route(self):
        """Test that invalid final route values are handled gracefully."""
        from unittest.mock import patch

        with patch(
            "sboxmgr.cli.commands.export._generate_config_from_subscription"
        ) as mock_generate:
            mock_generate.return_value = {"test": "config"}

            result = self.runner.invoke(
                app,
                [
                    "export",
                    "--url",
                    "https://example.com/subscription",
                    "--final-route",
                    "invalid_route",
                ],
            )

            # Should fail with validation error
            assert result.exit_code == 1
            assert (
                "Invalid final route" in result.stdout
                or "Invalid final route" in result.stderr
            )

    def test_empty_exclude_outbounds(self):
        """Test that empty exclude_outbounds is handled correctly."""
        from unittest.mock import patch

        with patch(
            "sboxmgr.cli.commands.export._generate_config_from_subscription"
        ) as mock_generate:
            mock_generate.return_value = {"test": "config"}

            result = self.runner.invoke(
                app,
                [
                    "export",
                    "--url",
                    "https://example.com/subscription",
                    "--exclude-outbounds",
                    "",
                ],
            )

            # Should not crash
            assert result.exit_code == 0
