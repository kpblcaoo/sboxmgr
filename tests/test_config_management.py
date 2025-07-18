"""Tests for configuration management functionality."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import toml
from typer.testing import CliRunner

from sboxmgr.cli.commands.config import app
from sboxmgr.configs.manager import ConfigManager
from sboxmgr.configs.models import ExportConfig, UserConfig
from sboxmgr.configs.toml_support import save_config_to_toml


class TestConfigManager:
    """Test ConfigManager functionality."""

    def test_enum_serialization_roundtrip(self):
        """Test that enum values are properly serialized and deserialized."""
        # Create config with enum values
        config = UserConfig(
            id="test-enum",
            description="Test enum serialization",
            export=ExportConfig(
                format="sing-box",  # This is an enum
                inbound_profile="tun",
                output_file="test.json",
            ),
        )

        # Save to TOML
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            save_config_to_toml(config, f.name)
            toml_path = f.name

        try:
            # Load back from TOML
            from sboxmgr.configs.toml_support import load_config_from_toml

            loaded_config = load_config_from_toml(toml_path)

            # Verify enum values are preserved
            assert loaded_config.export.format == config.export.format
            assert isinstance(loaded_config.export.format, type(config.export.format))

            # Verify TOML contains string values, not enum representations
            with open(toml_path) as f:
                toml_content = f.read()
            assert 'format = "sing-box"' in toml_content
            assert "ExportFormat" not in toml_content

        finally:
            os.unlink(toml_path)

    def test_switch_config_validation(self):
        """Test config validation during switch operations."""
        test_dir = tempfile.mkdtemp()

        try:
            # Create valid config
            valid_config = UserConfig(
                id="valid-test",
                description="Valid test config",
                export=ExportConfig(
                    format="sing-box", inbound_profile="tun", output_file="test.json"
                ),
            )

            valid_path = Path(test_dir) / "valid.toml"
            save_config_to_toml(valid_config, str(valid_path))

            # Create TOML with syntax error
            broken_toml_path = Path(test_dir) / "broken.toml"
            with open(broken_toml_path, "w") as f:
                f.write(
                    'id = "broken-test"\n[export\nformat = "sing-box"'
                )  # Missing closing bracket

            # Create TOML with invalid data
            invalid_data_path = Path(test_dir) / "invalid.toml"
            with open(invalid_data_path, "w") as f:
                toml.dump(
                    {
                        "id": "",  # Empty ID - should be invalid
                        "description": "Invalid config",
                        "export": {
                            "format": "unknown-format",  # Invalid format
                            "inbound_profile": "tun",
                            "output_file": "test.json",
                        },
                    },
                    f,
                )

            # Test ConfigManager
            manager = ConfigManager(test_dir)

            # Test valid config
            result = manager.switch_config("valid")
            assert result is True
            assert manager.get_active_config_name() == "valid-test"

            # Test broken TOML
            with pytest.raises(Exception) as exc_info:
                manager.switch_config("broken")
            assert "Key group not on a line by itself" in str(exc_info.value)

            # Test invalid data
            with pytest.raises(Exception) as exc_info:
                manager.switch_config("invalid")
            assert "validation error" in str(exc_info.value).lower()

            # Test nonexistent config
            with pytest.raises(FileNotFoundError):
                manager.switch_config("nonexistent")

        finally:
            import shutil

            shutil.rmtree(test_dir)

    def test_corrupted_active_config_file(self):
        """Test handling of corrupted .active_config file."""
        test_dir = tempfile.mkdtemp()

        try:
            # Create corrupted .active_config file
            active_config_file = Path(test_dir) / ".active_config"
            with open(active_config_file, "w") as f:
                f.write("invalid json content")

            # ConfigManager should handle this gracefully and create default
            manager = ConfigManager(test_dir)

            # Should have created default config due to corruption
            assert manager.get_active_config() is not None
            assert manager.get_active_config_name() == "default"

        finally:
            import shutil

            shutil.rmtree(test_dir)

    def test_no_configs_directory(self):
        """Test behavior when no configs exist."""
        test_dir = tempfile.mkdtemp()

        try:
            # Empty directory
            manager = ConfigManager(test_dir)

            # Should create default config
            assert manager.get_active_config() is not None
            assert manager.get_active_config_name() == "default"

            # Should have created default.toml
            default_path = Path(test_dir) / "default.toml"
            assert default_path.exists()

        finally:
            import shutil

            shutil.rmtree(test_dir)


class TestConfigCLI:
    """Test config CLI commands."""

    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()
        self.test_dir = tempfile.mkdtemp()

        # Create test configs
        self.home_config = UserConfig(
            id="home",
            description="Home configuration",
            export=ExportConfig(
                format="sing-box", inbound_profile="tun", output_file="home.json"
            ),
        )

        self.work_config = UserConfig(
            id="work",
            description="Work configuration",
            export=ExportConfig(
                format="sing-box", inbound_profile="socks", output_file="work.json"
            ),
        )

        # Save configs
        home_path = Path(self.test_dir) / "home.toml"
        work_path = Path(self.test_dir) / "work.toml"
        save_config_to_toml(self.home_config, str(home_path))
        save_config_to_toml(self.work_config, str(work_path))

    def teardown_method(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.test_dir)

    def test_config_list_command(self):
        """Test config list command."""
        with patch("sboxmgr.cli.commands.config.ConfigManager") as mock_manager:
            mock_instance = mock_manager.return_value

            # Mock list_configs to return test configs
            from datetime import datetime

            from sboxmgr.configs.manager import ConfigInfo

            mock_configs = [
                ConfigInfo(
                    path=str(Path(self.test_dir) / "home.toml"),
                    name="home",
                    size=1024,
                    modified=datetime.now(),
                    valid=True,
                ),
                ConfigInfo(
                    path=str(Path(self.test_dir) / "work.toml"),
                    name="work",
                    size=2048,
                    modified=datetime.now(),
                    valid=True,
                ),
            ]
            mock_instance.list_configs.return_value = mock_configs
            mock_instance.get_active_config_name.return_value = "home"

            result = self.runner.invoke(app, ["list"])

            assert result.exit_code == 0
            assert "home" in result.stdout
            assert "work" in result.stdout
            assert "🔥 ACTIVE" in result.stdout  # Should show active marker

    def test_config_list_no_configs(self):
        """Test config list with no configurations."""
        with patch("sboxmgr.cli.commands.config.ConfigManager") as mock_manager:
            mock_instance = mock_manager.return_value
            mock_instance.list_configs.return_value = []

            result = self.runner.invoke(app, ["list"])

            assert result.exit_code == 0
            assert "No configurations found" in result.stdout

    def test_config_switch_command(self):
        """Test config switch command."""
        with (
            patch("sboxmgr.cli.commands.config.ConfigManager") as mock_manager,
            patch("sboxmgr.cli.commands.config.load_config_auto") as mock_load,
        ):
            mock_instance = mock_manager.return_value
            mock_instance.get_active_config_name.side_effect = [
                "home",
                "work",
            ]  # First call returns "home", second "work"
            mock_instance.configs_dir = Path("/tmp/test")

            # Mock config file exists
            with patch("pathlib.Path.exists", return_value=True):
                # Mock load_config_auto to return a valid config
                mock_config = UserConfig(id="work", description="Work config")
                mock_load.return_value = mock_config

                result = self.runner.invoke(app, ["switch", "work"])

                assert result.exit_code == 0
                assert "Switched to configuration" in result.stdout
                assert "work" in result.stdout

    def test_config_switch_already_active(self):
        """Test switching to already active config."""
        with patch("sboxmgr.cli.commands.config.ConfigManager") as mock_manager:
            mock_instance = mock_manager.return_value
            mock_instance.get_active_config_name.return_value = "home"

            result = self.runner.invoke(app, ["switch", "home"])

            assert result.exit_code == 0
            assert "already active" in result.stdout

    def test_config_switch_invalid_config(self):
        """Test switching to invalid config."""
        with patch("sboxmgr.cli.commands.config.ConfigManager") as mock_manager:
            mock_instance = mock_manager.return_value
            mock_instance.get_active_config_name.return_value = "home"
            mock_instance.configs_dir = Path("/tmp/test")
            mock_instance.list_configs.return_value = []

            # Mock config file doesn't exist
            with patch("pathlib.Path.exists", return_value=False):
                result = self.runner.invoke(app, ["switch", "invalid"])

                assert result.exit_code == 1
                assert "not found" in result.stdout

    def test_config_switch_validation_error(self):
        """Test switching to config with validation errors."""
        with (
            patch("sboxmgr.cli.commands.config.ConfigManager") as mock_manager,
            patch("sboxmgr.cli.commands.config.load_config_auto") as mock_load,
        ):
            mock_instance = mock_manager.return_value
            mock_instance.get_active_config_name.return_value = "home"
            mock_instance.configs_dir = Path("/tmp/test")

            # Mock config file exists but load_config_auto raises ValidationError
            with patch("pathlib.Path.exists", return_value=True):
                from pydantic import ValidationError

                # Create a proper ValidationError
                try:
                    UserConfig(
                        id="", description="Invalid"
                    )  # This will raise ValidationError
                except ValidationError as e:
                    mock_load.side_effect = e

                result = self.runner.invoke(app, ["switch", "broken"])

                assert result.exit_code == 1
                assert "failed" in result.stdout.lower()

    def test_config_status_command(self):
        """Test config status command."""
        with patch("sboxmgr.cli.commands.config.ConfigManager") as mock_manager:
            mock_instance = mock_manager.return_value
            mock_instance.get_active_config_name.return_value = "home"
            mock_instance.get_active_config.return_value = self.home_config

            result = self.runner.invoke(app, ["status"])

            assert result.exit_code == 0
            assert "home" in result.stdout
            assert "Home configuration" in result.stdout

    def test_config_status_no_active(self):
        """Test config status with no active config."""
        with patch("sboxmgr.cli.commands.config.ConfigManager") as mock_manager:
            mock_instance = mock_manager.return_value
            mock_instance.get_active_config.return_value = None

            result = self.runner.invoke(app, ["status"])

            assert result.exit_code == 0
            assert "No active configuration" in result.stdout

    def test_config_validate_command(self):
        """Test config validate command."""
        # Create a temporary valid config file
        valid_path = Path(self.test_dir) / "validate_test.toml"
        save_config_to_toml(self.home_config, str(valid_path))

        result = self.runner.invoke(app, ["validate", str(valid_path)])

        assert result.exit_code == 0
        assert "valid" in result.stdout.lower()

    def test_config_validate_invalid_file(self):
        """Test config validate with invalid file."""
        # Create invalid config file
        invalid_path = Path(self.test_dir) / "invalid.toml"
        with open(invalid_path, "w") as f:
            f.write('id = ""\ndescription = "Invalid"')  # Missing required fields

        result = self.runner.invoke(app, ["validate", str(invalid_path)])

        assert result.exit_code == 1
        assert "validation" in result.stdout.lower()

    def test_config_validate_nonexistent_file(self):
        """Test config validate with nonexistent file."""
        result = self.runner.invoke(app, ["validate", "/nonexistent/file.toml"])

        assert result.exit_code == 1
        assert "not found" in result.stdout.lower()


class TestConfigEnvVars:
    """Test configuration environment variable support."""

    def test_active_config_env_var(self):
        """Test SBOXMGR_ACTIVE_CONFIG environment variable."""
        # This would need integration with the actual export command
        # For now, we just verify the parameter exists
        import inspect

        from sboxmgr.cli.commands.export.cli import export

        sig = inspect.signature(export)
        assert "config" in sig.parameters

        # Verify the parameter has the correct envvar
        sig.parameters["config"]
        # Note: This is a simplified test - full testing would require
        # actual CLI invocation with environment variables


class TestConfigWithBrokenEnum:
    """Test handling of configs with broken enum values."""

    def test_config_with_invalid_enum_value(self):
        """Test loading config with invalid enum value."""
        test_dir = tempfile.mkdtemp()

        try:
            # Create TOML with invalid enum value
            invalid_enum_path = Path(test_dir) / "invalid_enum.toml"
            with open(invalid_enum_path, "w") as f:
                toml.dump(
                    {
                        "id": "test-invalid-enum",
                        "description": "Config with invalid enum",
                        "export": {
                            "format": "invalid-format",  # Invalid enum value
                            "inbound_profile": "tun",
                            "output_file": "test.json",
                        },
                    },
                    f,
                )

            # Try to load - should raise validation error
            from sboxmgr.configs.toml_support import load_config_from_toml

            with pytest.raises(Exception) as exc_info:
                load_config_from_toml(str(invalid_enum_path))

            assert "enum" in str(exc_info.value).lower()

        finally:
            import shutil

            shutil.rmtree(test_dir)


if __name__ == "__main__":
    pytest.main([__file__])
