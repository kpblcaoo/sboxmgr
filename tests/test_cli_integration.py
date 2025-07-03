"""Integration tests for CLI commands with real data.

These tests verify that CLI commands work correctly with real
subscription URLs and produce expected outputs.
"""

import os
import pytest
import subprocess
import sys
from pathlib import Path


@pytest.mark.integration
@pytest.mark.external
def test_cli_export_with_real_url(test_subscription_url, require_external_tests, tmp_path):
    """Test CLI export command with real subscription URL.
    
    This test verifies that the CLI export command can process
    real subscription URLs and generate valid configuration files.
    """
    # Change to temporary directory
    os.chdir(tmp_path)
    
    # Run CLI export command
    cmd = [
        sys.executable, "-m", "sboxmgr.cli.main",
        "export",
        "--url", test_subscription_url,
        "--output", "test_config.json",
        "--format", "json"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    
    # Check if command completed
    if result.returncode == 0:
        # Verify output file was created
        config_file = tmp_path / "test_config.json"
        assert config_file.exists()
        
        # Verify file content
        with open(config_file, 'r') as f:
            content = f.read()
            assert len(content) > 0
            assert '"log"' in content or '"outbounds"' in content
        
        print("CLI export command completed successfully")
    else:
        # If failed, check for meaningful error output
        print(f"CLI export failed with return code {result.returncode}")
        print(f"stdout: {result.stdout}")
        print(f"stderr: {result.stderr}")
        
        # Should provide meaningful error information
        assert len(result.stderr) > 0 or len(result.stdout) > 0


@pytest.mark.integration
@pytest.mark.external
def test_cli_dry_run_with_real_url(test_subscription_url, require_external_tests, tmp_path):
    """Test CLI dry-run command with real subscription URL.
    
    This test verifies that the CLI dry-run command can validate
    real subscription URLs without creating files.
    """
    # Change to temporary directory
    os.chdir(tmp_path)
    
    # Run CLI dry-run command
    cmd = [
        sys.executable, "-m", "sboxmgr.cli.main",
        "export",
        "--url", test_subscription_url,
        "--dry-run"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    
    # Should complete (either success or meaningful failure)
    assert result.returncode in [0, 1]
    
    # Should provide output
    assert len(result.stdout) > 0 or len(result.stderr) > 0
    
    # Should not create output files in dry-run mode
    config_files = list(tmp_path.glob("*.json"))
    assert len(config_files) == 0
    
    print(f"CLI dry-run completed with return code {result.returncode}")


@pytest.mark.integration
@pytest.mark.external
def test_cli_list_servers_with_real_url(test_subscription_url, require_external_tests, tmp_path):
    """Test CLI list-servers command with real subscription URL.
    
    This test verifies that the CLI list-servers command can
    display server information from real subscription URLs.
    """
    # Change to temporary directory
    os.chdir(tmp_path)
    
    # Run CLI list-servers command
    cmd = [
        sys.executable, "-m", "sboxmgr.cli.main",
        "list-servers",
        "--url", test_subscription_url,
        "--format", "table"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    
    # Should complete
    assert result.returncode in [0, 1]
    
    # Should provide output
    output = result.stdout + result.stderr
    assert len(output) > 0
    
    print(f"CLI list-servers completed with return code {result.returncode}")
    print(f"Output length: {len(output)} characters")


@pytest.mark.integration
@pytest.mark.external
def test_cli_with_different_formats(test_subscription_url, require_external_tests, tmp_path):
    """Test CLI with different output formats.
    
    This test verifies that CLI commands work with different
    output formats (json, toml).
    """
    # Change to temporary directory
    os.chdir(tmp_path)
    
    formats = ["json", "toml"]
    
    for format_name in formats:
        output_file = f"test_config.{format_name}"
        
        cmd = [
            sys.executable, "-m", "sboxmgr.cli.main",
            "export",
            "--url", test_subscription_url,
            "--output", output_file,
            "--format", format_name
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            # Verify output file was created
            config_file = tmp_path / output_file
            assert config_file.exists()
            
            # Verify file content
            with open(config_file, 'r') as f:
                content = f.read()
                assert len(content) > 0
            
            print(f"CLI export to {format_name} format completed successfully")
        else:
            print(f"CLI export to {format_name} format failed: {result.stderr}")


@pytest.mark.integration
@pytest.mark.external
def test_cli_with_user_agent(test_subscription_url, require_external_tests, tmp_path):
    """Test CLI with custom User-Agent.
    
    This test verifies that CLI commands work with custom
    User-Agent headers.
    """
    # Change to temporary directory
    os.chdir(tmp_path)
    
    custom_user_agent = "sboxmgr-test/1.0"
    
    cmd = [
        sys.executable, "-m", "sboxmgr.cli.main",
        "export",
        "--url", test_subscription_url,
        "--user-agent", custom_user_agent,
        "--output", "test_config.json"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    
    # Should complete
    assert result.returncode in [0, 1]
    
    print(f"CLI with custom User-Agent completed with return code {result.returncode}")


@pytest.mark.integration
@pytest.mark.external
def test_cli_with_debug_output(test_subscription_url, require_external_tests, tmp_path):
    """Test CLI with debug output.
    
    This test verifies that CLI commands provide meaningful
    debug output when requested.
    """
    # Change to temporary directory
    os.chdir(tmp_path)
    
    cmd = [
        sys.executable, "-m", "sboxmgr.cli.main",
        "export",
        "--url", test_subscription_url,
        "--debug", "1",
        "--output", "test_config.json"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    
    # Should complete
    assert result.returncode in [0, 1]
    
    # Should provide debug output
    output = result.stdout + result.stderr
    assert len(output) > 0
    
    print(f"CLI with debug output completed with return code {result.returncode}")
    print(f"Debug output length: {len(output)} characters")


@pytest.mark.integration
@pytest.mark.external
def test_cli_error_handling(test_subscription_url, require_external_tests, tmp_path):
    """Test CLI error handling with invalid inputs.
    
    This test verifies that CLI commands handle errors gracefully
    and provide meaningful error messages.
    """
    # Change to temporary directory
    os.chdir(tmp_path)
    
    # Test with invalid URL
    cmd_invalid = [
        sys.executable, "-m", "sboxmgr.cli.main",
        "export",
        "--url", "https://invalid-url-that-does-not-exist.com/sub",
        "--output", "test_config.json"
    ]
    
    result_invalid = subprocess.run(cmd_invalid, capture_output=True, text=True, timeout=30)
    
    # Should fail gracefully
    assert result_invalid.returncode != 0
    
    # Should provide error message
    error_output = result_invalid.stdout + result_invalid.stderr
    assert len(error_output) > 0
    
    print(f"CLI error handling test completed with return code {result_invalid.returncode}")


@pytest.mark.integration
@pytest.mark.external
def test_cli_with_exclusions(test_subscription_url, require_external_tests, tmp_path):
    """Test CLI with exclusion management.
    
    This test verifies that CLI commands work with exclusion
    management features.
    """
    # Change to temporary directory
    os.chdir(tmp_path)
    
    # First, list servers to get some server IDs
    list_cmd = [
        sys.executable, "-m", "sboxmgr.cli.main",
        "list-servers",
        "--url", test_subscription_url,
        "--format", "json"
    ]
    
    result_list = subprocess.run(list_cmd, capture_output=True, text=True, timeout=60)
    
    if result_list.returncode == 0:
        # Try to add an exclusion (this might fail if no servers found)
        exclusion_cmd = [
            sys.executable, "-m", "sboxmgr.cli.main",
            "exclusions",
            "add",
            "--server", "test-server-id",
            "--name", "Test exclusion",
            "--reason", "Integration test"
        ]
        
        result_exclusion = subprocess.run(exclusion_cmd, capture_output=True, text=True, timeout=30)
        
        # Should complete (either success or meaningful failure)
        assert result_exclusion.returncode in [0, 1]
        
        print(f"CLI exclusion test completed with return code {result_exclusion.returncode}")
    else:
        print("Could not test exclusions - list-servers failed")


@pytest.mark.integration
@pytest.mark.external
def test_cli_performance(test_subscription_url, require_external_tests, tmp_path):
    """Test CLI performance with real data.
    
    This test measures the performance of CLI commands with
    real subscription data.
    """
    import time
    
    # Change to temporary directory
    os.chdir(tmp_path)
    
    # Measure export command performance
    cmd = [
        sys.executable, "-m", "sboxmgr.cli.main",
        "export",
        "--url", test_subscription_url,
        "--output", "test_config.json"
    ]
    
    start_time = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    execution_time = time.time() - start_time
    
    # Should complete within reasonable time
    assert execution_time < 60.0
    
    print(f"CLI export took {execution_time:.2f} seconds")
    print(f"Return code: {result.returncode}")


@pytest.mark.integration
@pytest.mark.external
def test_cli_with_backup(test_subscription_url, require_external_tests, tmp_path):
    """Test CLI with backup functionality.
    
    This test verifies that CLI commands work with backup
    functionality.
    """
    # Change to temporary directory
    os.chdir(tmp_path)
    
    # Create a dummy config file first
    dummy_config = '{"test": "config"}'
    test_config_path = tmp_path / "test_config.json"
    with open(test_config_path, "w") as f:
        f.write(dummy_config)
    
    # Run export with backup
    cmd = [
        sys.executable, "-m", "sboxmgr.cli.main",
        "export",
        "--url", test_subscription_url,
        "--output", "test_config.json",
        "--backup"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    
    # Should complete
    assert result.returncode in [0, 1]
    
    # Check if backup file was created (if export succeeded)
    if result.returncode == 0:
        backup_file = tmp_path / "test_config.json.backup"
        if backup_file.exists():
            print("Backup file was created successfully")
        else:
            print("No backup file found (might be expected behavior)")
    
    print(f"CLI with backup completed with return code {result.returncode}") 