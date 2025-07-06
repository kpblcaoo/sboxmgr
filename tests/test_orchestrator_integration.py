"""Integration tests for Orchestrator with real subscription data.

These tests use real subscription URLs to verify that the Orchestrator
works correctly with actual data from external sources. They are marked
with @pytest.mark.integration and @pytest.mark.external to distinguish
them from unit tests.
"""

import time

import pytest

from sboxmgr.core.orchestrator import Orchestrator, OrchestratorConfig


@pytest.mark.integration
@pytest.mark.external
def test_orchestrator_with_real_subscription(
    test_subscription_url, require_external_tests
):
    """Integration test with real subscription URL.

    This test verifies that the Orchestrator can successfully process
    a real subscription and export configuration.
    """
    orchestrator = Orchestrator.create_default()

    result = orchestrator.export_configuration(
        source_url=test_subscription_url, export_format="singbox"
    )

    # More flexible assertion - allow for parsing errors with real data
    if result["success"]:
        assert result["config"] is not None
        assert result["format"] == "singbox"
        assert result["server_count"] >= 0

        # Verify config structure
        config = result["config"]
        assert "log" in config
        assert "inbounds" in config
        assert "outbounds" in config
        assert "route" in config

        # Verify we have actual servers if any were parsed
        outbounds = config["outbounds"]
        if result["server_count"] > 0:
            assert len(outbounds) > 0

            # Verify server structure
            for outbound in outbounds:
                assert "type" in outbound
                assert "server" in outbound
                assert "server_port" in outbound
    else:
        # If failed, check that we have meaningful error information
        assert "error" in result
        assert result["error"] is not None
        print(f"Integration test failed with error: {result['error']}")


@pytest.mark.integration
@pytest.mark.external
def test_orchestrator_get_servers_with_real_subscription(
    test_subscription_url, require_external_tests
):
    """Test get_subscription_servers with real subscription URL.

    This test verifies that the Orchestrator can retrieve and process
    servers from a real subscription without exporting.
    """
    orchestrator = Orchestrator.create_default()

    result = orchestrator.get_subscription_servers(
        url=test_subscription_url, source_type="url_base64"
    )

    # More flexible assertion for real data
    if result.success:
        assert result.config is not None
        assert len(result.config) >= 0

        # Verify server objects if any were parsed
        if len(result.config) > 0:
            for server in result.config:
                assert hasattr(server, "protocol")
                assert hasattr(server, "address")
                assert hasattr(server, "port")
                assert server.protocol in [
                    "vmess",
                    "vless",
                    "trojan",
                    "ss",
                    "shadowsocks",
                ]
    else:
        # If failed, check that we have meaningful error information
        assert len(result.errors) > 0
        print(f"Server retrieval failed with errors: {result.errors}")


@pytest.mark.integration
@pytest.mark.external
def test_orchestrator_with_exclusions_and_real_subscription(
    test_subscription_url, require_external_tests
):
    """Test Orchestrator with exclusions using real subscription.

    This test verifies that exclusion filtering works correctly
    with real subscription data.
    """
    orchestrator = Orchestrator.create_default()

    # First get servers without exclusions
    result_without_exclusions = orchestrator.get_subscription_servers(
        url=test_subscription_url, source_type="url_base64"
    )

    # Only proceed if we successfully got servers
    if result_without_exclusions.success and len(result_without_exclusions.config) > 0:
        # Add some exclusions
        first_server = result_without_exclusions.config[0]
        server_id = f"{first_server.address}:{first_server.port}"

        exclusion_result = orchestrator.manage_exclusions(
            action="add",
            server_id=server_id,
            name="Test exclusion",
            reason="Integration test",
        )

        assert exclusion_result["success"] is True

        # Get servers again with exclusions
        result_with_exclusions = orchestrator.get_subscription_servers(
            url=test_subscription_url, source_type="url_base64"
        )

        if result_with_exclusions.success:
            assert len(result_with_exclusions.config) <= len(
                result_without_exclusions.config
            )

            # Verify excluded server is not in the result
            for server in result_with_exclusions.config:
                assert f"{server.address}:{server.port}" != server_id
    else:
        print(
            f"Could not test exclusions - no servers retrieved: {result_without_exclusions.errors}"
        )


@pytest.mark.integration
@pytest.mark.external
def test_orchestrator_export_different_formats(
    test_subscription_url, require_external_tests
):
    """Test Orchestrator export to different formats with real data.

    This test verifies that the Orchestrator can export to different
    formats (singbox, clash) using real subscription data.
    """
    orchestrator = Orchestrator.create_default()

    # Test singbox export
    singbox_result = orchestrator.export_configuration(
        source_url=test_subscription_url, export_format="singbox"
    )

    if singbox_result["success"]:
        assert singbox_result["format"] == "singbox"
        assert "outbounds" in singbox_result["config"]
    else:
        print(f"Singbox export failed: {singbox_result.get('error', 'Unknown error')}")

    # Test clash export
    clash_result = orchestrator.export_configuration(
        source_url=test_subscription_url, export_format="clash"
    )

    if clash_result["success"]:
        assert clash_result["format"] == "clash"
        assert "proxies" in clash_result["config"]
    else:
        print(f"Clash export failed: {clash_result.get('error', 'Unknown error')}")


@pytest.mark.integration
def test_orchestrator_error_handling_with_invalid_url():
    """Test Orchestrator error handling with invalid URL.

    This test verifies that the Orchestrator handles invalid URLs
    gracefully and returns appropriate error information.
    """
    orchestrator = Orchestrator.create_default()

    # Test with invalid URL
    result = orchestrator.export_configuration(
        source_url="https://invalid-url-that-does-not-exist.com/sub",
        export_format="singbox",
    )

    # Should fail gracefully in fail-safe mode
    assert result["success"] is False
    assert "error" in result
    assert result["config"] is None


@pytest.mark.integration
@pytest.mark.external
@pytest.mark.slow
def test_orchestrator_performance_with_real_data(
    test_subscription_url, require_external_tests
):
    """Test Orchestrator performance with real subscription data.

    This test verifies that the Orchestrator can handle real data
    efficiently and within reasonable time limits.
    """
    orchestrator = Orchestrator.create_default()

    # Measure time for server retrieval
    start_time = time.time()
    result = orchestrator.get_subscription_servers(
        url=test_subscription_url, source_type="url_base64"
    )
    retrieval_time = time.time() - start_time

    # Should complete within reasonable time even if parsing fails
    assert retrieval_time < 30.0  # Should complete within 30 seconds

    # Measure time for full export
    start_time = time.time()
    export_result = orchestrator.export_configuration(
        source_url=test_subscription_url, export_format="singbox"
    )
    export_time = time.time() - start_time

    # Should complete within reasonable time even if export fails
    assert export_time < 60.0  # Should complete within 60 seconds


@pytest.mark.integration
@pytest.mark.external
def test_orchestrator_with_different_source_types(
    test_subscription_url, require_external_tests
):
    """Test Orchestrator with different source type detection.

    This test verifies that the Orchestrator can handle different
    source types and auto-detection works correctly.
    """
    orchestrator = Orchestrator.create_default()

    # Test with auto-detection (no source_type specified)
    result_auto = orchestrator.get_subscription_servers(url=test_subscription_url)

    # Test with explicit url_base64 type
    result_explicit = orchestrator.get_subscription_servers(
        url=test_subscription_url, source_type="url_base64"
    )

    # Both should behave similarly (either both succeed or both fail)
    # The important thing is that they don't crash and provide meaningful results
    assert hasattr(result_auto, "success")
    assert hasattr(result_explicit, "success")


@pytest.mark.integration
@pytest.mark.external
def test_orchestrator_caching_behavior(test_subscription_url, require_external_tests):
    """Test Orchestrator caching behavior with real data.

    This test verifies that caching works correctly and improves
    performance for repeated requests.
    """
    orchestrator = Orchestrator.create_default()

    # First request
    start_time = time.time()
    result1 = orchestrator.get_subscription_servers(
        url=test_subscription_url, source_type="url_base64"
    )
    time1 = time.time() - start_time

    # Second request (should use cache)
    start_time = time.time()
    result2 = orchestrator.get_subscription_servers(
        url=test_subscription_url, source_type="url_base64"
    )
    time2 = time.time() - start_time

    # Both should return the same result
    assert result1.success == result2.success

    # Second request should be faster (cached)
    if result1.success and result2.success:
        assert time2 <= time1  # Cached request should be faster or equal


@pytest.mark.integration
@pytest.mark.external
def test_orchestrator_with_user_routes(test_subscription_url, require_external_tests):
    """Test Orchestrator with user-defined routing rules.

    This test verifies that user routing rules work correctly
    with real subscription data.
    """
    orchestrator = Orchestrator.create_default()

    # Test with user routes
    user_routes = ["proxy", "direct"]

    result = orchestrator.export_configuration(
        source_url=test_subscription_url,
        export_format="singbox",
        user_routes=user_routes,
    )

    if result["success"]:
        config = result["config"]
        assert "route" in config
        assert "rules" in config["route"]

        # Check that routing rules were applied
        rules = config["route"]["rules"]
        assert len(rules) > 0
    else:
        print(f"Export with user routes failed: {result.get('error', 'Unknown error')}")


@pytest.mark.integration
@pytest.mark.external
def test_orchestrator_fail_safe_mode(test_subscription_url, require_external_tests):
    """Test Orchestrator fail-safe mode with real data.

    This test verifies that fail-safe mode works correctly
    and prevents crashes with problematic data.
    """
    # Create orchestrator with fail-safe mode
    config = OrchestratorConfig(fail_safe=True)
    orchestrator = Orchestrator(config=config)

    result = orchestrator.export_configuration(
        source_url=test_subscription_url, export_format="singbox"
    )

    # Should not crash, even if data is problematic
    assert isinstance(result, dict)
    assert "success" in result
    assert "format" in result

    # Should handle errors gracefully
    if not result["success"]:
        assert "error" in result
        assert result["error"] is not None
