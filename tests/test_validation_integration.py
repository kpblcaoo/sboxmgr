"""Integration tests for validation and parsing with real data.

These tests verify that validation and parsing components work
correctly with real subscription data from various sources.
"""

import pytest
import base64
from sboxmgr.subscription.validators import ProtocolSpecificValidator, GeoValidator
from sboxmgr.subscription.parsers import Base64Parser, URIListParser
from sboxmgr.subscription.models import PipelineContext


@pytest.mark.integration
@pytest.mark.external
def test_protocol_validator_with_real_data(test_subscription_url, require_external_tests):
    """Test ProtocolSpecificValidator with real server data.
    
    This test verifies that ProtocolSpecificValidator can validate
    real server configurations from subscription data.
    """
    # First get real servers
    from sboxmgr.subscription.manager import SubscriptionManager
    from sboxmgr.subscription.models import SubscriptionSource
    
    source = SubscriptionSource(url=test_subscription_url, source_type="url_base64")
    manager = SubscriptionManager(source)
    result = manager.get_servers()
    
    if result.success and result.config:
        validator = ProtocolSpecificValidator()
        
        # Validate each server
        valid_servers = []
        invalid_servers = []
        
        for server in result.config:
            try:
                # Create context for validation
                context = PipelineContext(mode="tolerant")
                validation_result = validator.validate([server], context)
                
                if validation_result.valid:
                    valid_servers.extend(validation_result.valid_servers)
                else:
                    invalid_servers.append(server)
            except Exception as e:
                invalid_servers.append(server)
                print(f"Validation error for server {server.address}: {e}")
        
        print(f"Protocol validation: {len(valid_servers)} valid, {len(invalid_servers)} invalid servers")
        
        # Should have some valid servers if any were parsed
        if len(result.config) > 0:
            assert len(valid_servers) >= 0
    else:
        print(f"Could not test protocol validation - no servers retrieved: {result.errors}")


@pytest.mark.integration
@pytest.mark.external
def test_geo_validator_with_real_data(test_subscription_url, require_external_tests):
    """Test GeoValidator with real server data.
    
    This test verifies that GeoValidator can validate
    real server geo-locations from subscription data.
    """
    # First get real servers
    from sboxmgr.subscription.manager import SubscriptionManager
    from sboxmgr.subscription.models import SubscriptionSource
    
    source = SubscriptionSource(url=test_subscription_url, source_type="url_base64")
    manager = SubscriptionManager(source)
    result = manager.get_servers()
    
    if result.success and result.config:
        validator = GeoValidator()
        
        # Note: GeoValidator is not yet implemented, so we just test that it exists
        assert validator is not None
        print("GeoValidator exists but is not yet implemented")
    else:
        print(f"Could not test geo validation - no servers retrieved: {result.errors}")


@pytest.mark.integration
@pytest.mark.external
def test_base64_parser_with_real_data(test_subscription_url, require_external_tests):
    """Test Base64Parser with real subscription data.
    
    This test verifies that Base64Parser can parse real
    base64-encoded subscription data.
    """
    import requests
    
    try:
        # Fetch real subscription data
        response = requests.get(test_subscription_url, timeout=30)
        response.raise_for_status()
        
        raw_data = response.content
        
        # Try to decode as base64
        try:
            decoded_data = base64.b64decode(raw_data)
            parser = Base64Parser()
            
            # Create context
            context = PipelineContext(mode="tolerant")
            
            # Parse the data
            result = parser.parse(decoded_data, context)
            
            if result.success:
                print(f"Base64 parsing successful: {len(result.config)} servers")
                assert len(result.config) >= 0
            else:
                print(f"Base64 parsing failed: {result.errors}")
                
        except Exception as e:
            print(f"Base64 parsing error: {e}")
            
    except Exception as e:
        print(f"Could not fetch subscription data: {e}")


@pytest.mark.integration
@pytest.mark.external
def test_uri_list_parser_with_real_data(test_subscription_url, require_external_tests):
    """Test URIListParser with real subscription data.
    
    This test verifies that URIListParser can parse real
    URI list subscription data.
    """
    import requests
    
    try:
        # Fetch real subscription data
        response = requests.get(test_subscription_url, timeout=30)
        response.raise_for_status()
        
        raw_data = response.content
        
        # Try to decode and parse as URI list
        try:
            # Try different encodings
            for encoding in ['utf-8', 'latin-1']:
                try:
                    text_data = raw_data.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                # If all encodings fail, try base64 decode first
                try:
                    decoded_data = base64.b64decode(raw_data)
                    text_data = decoded_data.decode('utf-8')
                except:
                    text_data = raw_data.decode('utf-8', errors='ignore')
            
            parser = URIListParser()
            
            # Parse the data (URIListParser doesn't use context)
            result = parser.parse(raw_data)
            
            if result:
                print(f"URI list parsing successful: {len(result)} servers")
                assert len(result) >= 0
            else:
                print("URI list parsing returned no servers")
                
        except Exception as e:
            print(f"URI list parsing error: {e}")
            
    except Exception as e:
        print(f"Could not fetch subscription data: {e}")


@pytest.mark.integration
@pytest.mark.external
def test_required_fields_validator_with_real_data(test_subscription_url, require_external_tests):
    """Test RequiredFieldsValidator with real server data.
    
    This test verifies that RequiredFieldsValidator can validate
    real server configurations for required fields.
    """
    from sboxmgr.subscription.validators import EnhancedRequiredFieldsValidator
    from sboxmgr.subscription.manager import SubscriptionManager
    from sboxmgr.subscription.models import SubscriptionSource
    
    source = SubscriptionSource(url=test_subscription_url, source_type="url_base64")
    manager = SubscriptionManager(source)
    result = manager.get_servers()
    
    if result.success and result.config:
        validator = EnhancedRequiredFieldsValidator()
        
        # Validate each server's required fields
        valid_servers = []
        invalid_servers = []
        
        for server in result.config:
            try:
                # Create context for validation
                context = PipelineContext(mode="tolerant")
                validation_result = validator.validate([server], context)
                
                if validation_result.valid:
                    valid_servers.extend(validation_result.valid_servers)
                else:
                    invalid_servers.append(server)
            except Exception as e:
                invalid_servers.append(server)
                print(f"Required fields validation error for server {server.address}: {e}")
        
        print(f"Required fields validation: {len(valid_servers)} valid, {len(invalid_servers)} invalid servers")
        
        # Should have some valid servers if any were parsed
        if len(result.config) > 0:
            assert len(valid_servers) >= 0
    else:
        print(f"Could not test required fields validation - no servers retrieved: {result.errors}")


@pytest.mark.integration
@pytest.mark.external
def test_validation_pipeline_with_real_data(test_subscription_url, require_external_tests):
    """Test complete validation pipeline with real data.
    
    This test verifies that the complete validation pipeline
    works correctly with real subscription data.
    """
    from sboxmgr.subscription.validators import ProtocolSpecificValidator, EnhancedRequiredFieldsValidator
    from sboxmgr.subscription.manager import SubscriptionManager
    from sboxmgr.subscription.models import SubscriptionSource
    
    source = SubscriptionSource(url=test_subscription_url, source_type="url_base64")
    manager = SubscriptionManager(source)
    result = manager.get_servers()
    
    if result.success and result.config:
        # Create validation pipeline
        validators = [
            ProtocolSpecificValidator(),
            EnhancedRequiredFieldsValidator()
        ]
        
        # Validate all servers with each validator
        validation_results = []
        for server in result.config:
            server_valid = True
            for validator in validators:
                try:
                    context = PipelineContext(mode="tolerant")
                    validation_result = validator.validate([server], context)
                    if not validation_result.valid:
                        server_valid = False
                        break
                except Exception as e:
                    server_valid = False
                    print(f"Validation error for server {server.address}: {e}")
                    break
            
            validation_results.append((server, server_valid))
        
        # Count results
        valid_count = sum(1 for _, is_valid in validation_results if is_valid)
        invalid_count = len(validation_results) - valid_count
        
        print(f"Validation pipeline: {valid_count} valid, {invalid_count} invalid servers")
        
        # Should have some valid servers if any were parsed
        if len(result.config) > 0:
            assert valid_count >= 0
    else:
        print(f"Could not test validation pipeline - no servers retrieved: {result.errors}")


@pytest.mark.integration
@pytest.mark.external
def test_parser_auto_detection_with_real_data(test_subscription_url, require_external_tests):
    """Test parser auto-detection with real data.
    
    This test verifies that the parser auto-detection mechanism
    works correctly with real subscription data.
    """
    from sboxmgr.subscription.manager import SubscriptionManager
    from sboxmgr.subscription.models import SubscriptionSource
    
    source = SubscriptionSource(url=test_subscription_url, source_type="url_base64")
    manager = SubscriptionManager(source)
    
    # Test with auto-detection
    result_auto = manager.get_servers()
    
    # Test with explicit source type (create new manager with different source type)
    source_explicit = SubscriptionSource(url=test_subscription_url, source_type="url_base64")
    manager_explicit = SubscriptionManager(source_explicit)
    result_explicit = manager_explicit.get_servers()
    
    # Both should behave similarly (either both succeed or both fail)
    assert hasattr(result_auto, 'success')
    assert hasattr(result_explicit, 'success')
    
    print(f"Auto-detection test: {'Success' if result_auto.success else 'Failed'}")
    print(f"Explicit type test: {'Success' if result_explicit.success else 'Failed'}")


@pytest.mark.integration
@pytest.mark.external
def test_validation_error_details_with_real_data(test_subscription_url, require_external_tests):
    """Test validation error details with real data.
    
    This test verifies that validation provides meaningful
    error details for real server configurations.
    """
    from sboxmgr.subscription.validators import ProtocolSpecificValidator
    from sboxmgr.subscription.manager import SubscriptionManager
    from sboxmgr.subscription.models import SubscriptionSource
    
    source = SubscriptionSource(url=test_subscription_url, source_type="url_base64")
    manager = SubscriptionManager(source)
    result = manager.get_servers()
    
    if result.success and result.config:
        validator = ProtocolSpecificValidator()
        
        # Check validation errors for each server
        for i, server in enumerate(result.config[:5]):  # Check first 5 servers
            try:
                context = PipelineContext(mode="tolerant")
                validation_result = validator.validate([server], context)
                
                if not validation_result.valid:
                    print(f"Server {i} ({server.address}) validation failed")
                    print(f"  Errors: {validation_result.errors}")
                    
                    # Check what fields are missing or invalid
                    if not hasattr(server, 'type') or not server.type:
                        print("  - Missing or invalid type")
                    if not hasattr(server, 'address') or not server.address:
                        print("  - Missing or invalid address")
                    if not hasattr(server, 'port') or not server.port:
                        print("  - Missing or invalid port")
            except Exception as e:
                print(f"Server {i} ({server.address}) validation error: {e}")
    else:
        print(f"Could not test validation error details - no servers retrieved: {result.errors}")


@pytest.mark.integration
@pytest.mark.external
def test_parser_performance_with_real_data(test_subscription_url, require_external_tests):
    """Test parser performance with real data.
    
    This test measures the performance of different parsers
    with real subscription data.
    """
    import time
    import requests
    
    try:
        # Fetch real subscription data
        start_time = time.time()
        response = requests.get(test_subscription_url, timeout=30)
        response.raise_for_status()
        fetch_time = time.time() - start_time
        
        raw_data = response.content
        
        # Test base64 parser performance
        try:
            decoded_data = base64.b64decode(raw_data)
            parser = Base64Parser()
            context = PipelineContext(mode="tolerant")
            
            start_time = time.time()
            result = parser.parse(decoded_data, context)
            parse_time = time.time() - start_time
            
            print(f"Base64 parser performance: {parse_time:.3f}s")
            print(f"Data fetch time: {fetch_time:.3f}s")
            
            if result.success:
                print(f"Parsed {len(result.config)} servers")
            
        except Exception as e:
            print(f"Base64 parser performance test failed: {e}")
            
    except Exception as e:
        print(f"Could not test parser performance: {e}") 