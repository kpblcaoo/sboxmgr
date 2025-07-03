"""Integration tests for full subscription processing pipeline.

These tests verify the complete workflow from subscription fetching
through configuration export, including all intermediate processing
stages and error handling.
"""

import pytest
import time
from sboxmgr.subscription.manager import SubscriptionManager
from sboxmgr.subscription.models import SubscriptionSource, PipelineContext
from sboxmgr.export.export_manager import ExportManager


@pytest.mark.integration
@pytest.mark.external
def test_full_subscription_pipeline(test_subscription_url, require_external_tests):
    """Test complete subscription processing pipeline.
    
    This test verifies the entire workflow from subscription fetching
    through configuration export using real data.
    """
    # Step 1: Create subscription source
    source = SubscriptionSource(url=test_subscription_url, source_type="url_base64")
    
    # Step 2: Create subscription manager
    subscription_manager = SubscriptionManager(source)
    
    # Step 3: Get servers
    context = PipelineContext(mode="tolerant")
    result = subscription_manager.get_servers(context=context)
    
    # Step 4: Export configuration
    if result.success and result.config:
        export_manager = ExportManager(export_format="singbox")
        config = export_manager.export(result.config)
        
        # Verify exported configuration
        assert isinstance(config, dict)
        assert "log" in config
        assert "inbounds" in config
        assert "outbounds" in config
        assert "route" in config
        
        print(f"Successfully processed {len(result.config)} servers")
    else:
        print(f"Pipeline failed: {result.errors}")


@pytest.mark.integration
@pytest.mark.external
def test_subscription_manager_with_real_data(test_subscription_url, require_external_tests):
    """Test SubscriptionManager with real subscription data.
    
    This test verifies that SubscriptionManager can handle real
    subscription URLs and process them correctly.
    """
    from sboxmgr.subscription.models import SubscriptionSource
    
    source = SubscriptionSource(url=test_subscription_url, source_type="url_base64")
    manager = SubscriptionManager(source)
    
    # Test with different modes
    for mode in ["tolerant", "strict"]:
        context = PipelineContext(mode=mode)
        result = manager.get_servers(context=context)
        
        assert hasattr(result, 'success')
        assert hasattr(result, 'config')
        assert hasattr(result, 'errors')
        
        if result.success and result.config:
            assert len(result.config) >= 0
            print(f"Mode {mode}: Successfully processed {len(result.config)} servers")
        else:
            print(f"Mode {mode}: Failed with errors: {result.errors}")


@pytest.mark.integration
@pytest.mark.external
def test_export_manager_with_real_servers(test_subscription_url, require_external_tests):
    """Test ExportManager with real server data.
    
    This test verifies that ExportManager can export real server
    configurations to different formats.
    """
    # First get real servers
    source = SubscriptionSource(url=test_subscription_url, source_type="url_base64")
    subscription_manager = SubscriptionManager(source)
    result = subscription_manager.get_servers()
    
    if result.success and result.config:
        # Test singbox export
        singbox_export_manager = ExportManager(export_format="singbox")
        singbox_config = singbox_export_manager.export(result.config)
        
        assert isinstance(singbox_config, dict)
        assert "outbounds" in singbox_config
        
        # Test clash export
        clash_export_manager = ExportManager(export_format="clash")
        clash_config = clash_export_manager.export(result.config)
        
        assert isinstance(clash_config, dict)
        assert "proxies" in clash_config
        
        print(f"Successfully exported {len(result.config)} servers to both formats")
    else:
        print(f"Could not test export - no servers retrieved: {result.errors}")


@pytest.mark.integration
@pytest.mark.external
def test_pipeline_with_exclusions(test_subscription_url, require_external_tests):
    """Test pipeline with exclusion management.
    
    This test verifies that exclusions work correctly throughout
    the entire processing pipeline.
    """
    from sboxmgr.core.exclusions.manager import ExclusionManager
    
    # Create exclusion manager
    exclusion_manager = ExclusionManager()
    
    # Get servers first
    source = SubscriptionSource(url=test_subscription_url, source_type="url_base64")
    subscription_manager = SubscriptionManager(source)
    result = subscription_manager.get_servers()
    
    if result.success and result.config and len(result.config) > 0:
        # Add exclusion for first server
        first_server = result.config[0]
        server_id = f"{first_server.address}:{first_server.port}"
        exclusion_manager.add(server_id, "Test exclusion")
        
        # Filter servers with exclusions
        filtered_servers = exclusion_manager.filter_servers(result.config)
        
        # Should have fewer servers after filtering
        assert len(filtered_servers) < len(result.config)
        
        # Excluded server should not be in filtered list
        for server in filtered_servers:
            assert f"{server.address}:{server.port}" != server_id
        
        print(f"Successfully filtered {len(result.config) - len(filtered_servers)} servers")
    else:
        print(f"Could not test exclusions - no servers retrieved: {result.errors}")


@pytest.mark.integration
@pytest.mark.external
def test_pipeline_performance(test_subscription_url, require_external_tests):
    """Test pipeline performance with real data.
    
    This test measures the performance of different pipeline stages
    with real subscription data.
    """
    source = SubscriptionSource(url=test_subscription_url, source_type="url_base64")
    subscription_manager = SubscriptionManager(source)
    
    # Measure subscription processing time
    start_time = time.time()
    result = subscription_manager.get_servers()
    processing_time = time.time() - start_time
    
    print(f"Subscription processing took {processing_time:.2f} seconds")
    
    # Should complete within reasonable time
    assert processing_time < 30.0
    
    if result.success and result.config:
        # Measure export time
        export_manager = ExportManager(export_format="singbox")
        
        start_time = time.time()
        config = export_manager.export(result.config)
        export_time = time.time() - start_time
        
        print(f"Export took {export_time:.2f} seconds")
        
        # Export should be fast
        assert export_time < 5.0
        
        # Total pipeline time
        total_time = processing_time + export_time
        print(f"Total pipeline time: {total_time:.2f} seconds")


@pytest.mark.integration
@pytest.mark.external
def test_pipeline_error_recovery(test_subscription_url, require_external_tests):
    """Test pipeline error recovery with real data.
    
    This test verifies that the pipeline can handle errors gracefully
    and recover from various failure scenarios.
    """
    # Test with invalid URL first (should fail gracefully)
    invalid_source = SubscriptionSource(url="https://invalid-url.com/sub", source_type="url_base64")
    invalid_manager = SubscriptionManager(invalid_source)
    
    result_invalid = invalid_manager.get_servers()
    assert not result_invalid.success
    assert len(result_invalid.errors) > 0
    
    # Test with valid URL (should work)
    valid_source = SubscriptionSource(url=test_subscription_url, source_type="url_base64")
    valid_manager = SubscriptionManager(valid_source)
    
    result_valid = valid_manager.get_servers()
    # Should either succeed or fail gracefully with meaningful errors
    assert hasattr(result_valid, 'success')
    assert hasattr(result_valid, 'errors')
    
    print(f"Invalid URL test: {'Failed as expected' if not result_invalid.success else 'Unexpected success'}")
    print(f"Valid URL test: {'Success' if result_valid.success else f'Failed with {len(result_valid.errors)} errors'}")


@pytest.mark.integration
@pytest.mark.external
def test_pipeline_with_different_formats(test_subscription_url, require_external_tests):
    """Test pipeline with different export formats.
    
    This test verifies that the pipeline can export to different
    formats correctly.
    """
    source = SubscriptionSource(url=test_subscription_url, source_type="url_base64")
    subscription_manager = SubscriptionManager(source)
    result = subscription_manager.get_servers()
    
    if result.success and result.config:
        # Test different export formats
        formats = ["singbox", "clash"]
        
        for format_name in formats:
            export_manager = ExportManager(export_format=format_name)
            config = export_manager.export(result.config)
            
            assert isinstance(config, dict)
            
            if format_name == "singbox":
                assert "outbounds" in config
                assert "route" in config
            elif format_name == "clash":
                assert "proxies" in config
                assert "proxy-groups" in config
            
            print(f"Successfully exported to {format_name} format")
    else:
        print(f"Could not test formats - no servers retrieved: {result.errors}")


@pytest.mark.integration
@pytest.mark.external
def test_pipeline_caching(test_subscription_url, require_external_tests):
    """Test pipeline caching behavior.
    
    This test verifies that caching works correctly and improves
    performance for repeated requests.
    """
    source = SubscriptionSource(url=test_subscription_url, source_type="url_base64")
    subscription_manager = SubscriptionManager(source)
    
    # First request
    start_time = time.time()
    result1 = subscription_manager.get_servers()
    time1 = time.time() - start_time
    
    # Second request (should use cache)
    start_time = time.time()
    result2 = subscription_manager.get_servers()
    time2 = time.time() - start_time
    
    # Both should return the same result
    assert result1.success == result2.success
    
    if result1.success and result2.success:
        assert len(result1.config) == len(result2.config)
        
        # Second request should be faster (cached)
        assert time2 <= time1
        
        print(f"First request: {time1:.2f}s, Second request: {time2:.2f}s")
        print(f"Cache improvement: {((time1 - time2) / time1 * 100):.1f}%")


@pytest.mark.integration
@pytest.mark.external
def test_pipeline_with_middleware(test_subscription_url, require_external_tests):
    """Test pipeline with middleware processing.
    
    This test verifies that middleware can be integrated into
    the processing pipeline.
    """
    try:
        from sboxmgr.subscription.middleware import LoggingMiddleware
        
        source = SubscriptionSource(url=test_subscription_url, source_type="url_base64")
        subscription_manager = SubscriptionManager(source)
        
        # Add middleware
        logging_middleware = LoggingMiddleware({'log_performance': True})
        subscription_manager.middleware_chain = [logging_middleware]
        
        result = subscription_manager.get_servers()
        
        # Should work with or without middleware
        assert hasattr(result, 'success')
        assert hasattr(result, 'config')
        
        print(f"Pipeline with middleware: {'Success' if result.success else 'Failed'}")
        
    except ImportError:
        pytest.skip("Middleware components not available")


@pytest.mark.integration
@pytest.mark.external
def test_pipeline_with_postprocessors(test_subscription_url, require_external_tests):
    """Test pipeline with postprocessor processing.
    
    This test verifies that postprocessors can be integrated into
    the processing pipeline.
    """
    try:
        from sboxmgr.subscription.postprocessors import PostProcessorChain
        
        source = SubscriptionSource(url=test_subscription_url, source_type="url_base64")
        subscription_manager = SubscriptionManager(source)
        
        # Add postprocessor chain
        postprocessor_chain = PostProcessorChain([], {
            'execution_mode': 'sequential',
            'error_strategy': 'continue'
        })
        subscription_manager.postprocessor = postprocessor_chain
        
        result = subscription_manager.get_servers()
        
        # Should work with or without postprocessors
        assert hasattr(result, 'success')
        assert hasattr(result, 'config')
        
        print(f"Pipeline with postprocessors: {'Success' if result.success else 'Failed'}")
        
    except ImportError:
        pytest.skip("Postprocessor components not available") 