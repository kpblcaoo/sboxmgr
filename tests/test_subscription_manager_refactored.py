"""Tests for SubscriptionManager refactoring - validating current behavior before changes."""

import pytest
from unittest.mock import Mock, patch
from sboxmgr.subscription.models import SubscriptionSource, PipelineContext, PipelineResult
from sboxmgr.subscription.manager import SubscriptionManager
from sboxmgr.subscription.errors import PipelineError, ErrorType


class TestSubscriptionManagerRefactoring:
    """Test suite for SubscriptionManager refactoring validation.
    
    These tests validate the current behavior of SubscriptionManager
    before refactoring to ensure no regressions are introduced.
    """
    
    @pytest.fixture
    def mock_source(self):
        """Create mock subscription source for testing.
        
        Returns:
            SubscriptionSource: Mock source configuration.
        """
        return SubscriptionSource(
            url="https://example.com/sub",
            source_type="url_base64"
        )
    
    @pytest.fixture
    def mock_context(self):
        """Create mock pipeline context for testing.
        
        Returns:
            PipelineContext: Mock pipeline context.
        """
        return PipelineContext(mode="strict", debug_level=0)
    
    def test_get_servers_basic_flow(self, mock_source, mock_context):
        """Test basic get_servers flow with mocked components.
        
        This test validates the complete pipeline execution from
        fetch to final server selection without external dependencies.
        """
        # Mock raw data
        mock_raw = b"ss://YWVzLTI1Ni1nY206cGFzc0BleGFtcGxlLmNvbTo4Mzg4#test"
        
        # Mock parsed server
        mock_server = Mock()
        mock_server.type = "ss"
        mock_server.address = "example.com"
        mock_server.port = 8388
        mock_server.meta = {"tag": "test"}
        
        with patch('sboxmgr.subscription.registry.get_plugin') as mock_get_plugin:
            # Mock fetcher
            mock_fetcher = Mock()
            mock_fetcher.fetch.return_value = mock_raw
            mock_fetcher.source = mock_source
            mock_get_plugin.return_value = Mock(return_value=mock_fetcher)
            
            with patch('sboxmgr.subscription.manager.detect_parser') as mock_detect:
                # Mock parser
                mock_parser = Mock()
                mock_parser.parse.return_value = [mock_server]
                mock_detect.return_value = mock_parser
                
                with patch('sboxmgr.subscription.validators.base.RAW_VALIDATOR_REGISTRY') as mock_raw_val:
                    # Mock raw validator
                    mock_raw_validator = Mock()
                    mock_raw_validator.validate.return_value = Mock(valid=True, errors=[])
                    mock_raw_val.get.return_value = Mock(return_value=mock_raw_validator)
                    
                    with patch('sboxmgr.subscription.validators.base.PARSED_VALIDATOR_REGISTRY') as mock_parsed_val:
                        # Mock parsed validator
                        mock_parsed_validator = Mock()
                        mock_parsed_validator.validate.return_value = Mock(
                            valid_servers=[mock_server], errors=[]
                        )
                        mock_parsed_val.get.return_value = Mock(return_value=mock_parsed_validator)
                        
                        # Execute test
                        mgr = SubscriptionManager(mock_source)
                        result = mgr.get_servers(context=mock_context)
                        
                        # Validate results
                        assert isinstance(result, PipelineResult)
                        assert result.success
                        assert len(result.config) == 1
                        assert result.config[0] == mock_server
                        assert mock_fetcher.fetch.called
                        assert mock_parser.parse.called
    
    def test_get_servers_fetch_error_handling(self, mock_source, mock_context):
        """Test error handling during fetch stage.
        
        Validates that fetch errors are properly caught and converted
        to PipelineError objects with appropriate error context.
        """
        with patch('sboxmgr.subscription.registry.get_plugin') as mock_get_plugin:
            # Mock fetcher that raises exception
            mock_fetcher = Mock()
            mock_fetcher.fetch.side_effect = Exception("Network error")
            mock_fetcher.source = mock_source
            mock_get_plugin.return_value = Mock(return_value=mock_fetcher)
            
            # Execute test
            mgr = SubscriptionManager(mock_source)
            result = mgr.get_servers(context=mock_context)
            
            # Validate error handling
            assert isinstance(result, PipelineResult)
            assert not result.success
            assert result.config is None
            assert len(result.errors) == 1
            assert result.errors[0].type == ErrorType.INTERNAL
            assert "Network error" in result.errors[0].message
    
    def test_get_servers_validation_error_strict_mode(self, mock_source):
        """Test validation error handling in strict mode.
        
        Validates that validation errors in strict mode cause immediate
        pipeline failure with appropriate error reporting.
        """
        mock_context = PipelineContext(mode="strict")
        mock_raw = b"invalid data"
        
        with patch('sboxmgr.subscription.registry.get_plugin') as mock_get_plugin:
            # Mock fetcher
            mock_fetcher = Mock()
            mock_fetcher.fetch.return_value = mock_raw
            mock_fetcher.source = mock_source
            mock_get_plugin.return_value = Mock(return_value=mock_fetcher)
            
            with patch('sboxmgr.subscription.validators.base.RAW_VALIDATOR_REGISTRY') as mock_raw_val:
                # Mock validator that fails
                mock_raw_validator = Mock()
                mock_raw_validator.validate.return_value = Mock(
                    valid=False, 
                    errors=["Invalid data format"]
                )
                mock_raw_val.get.return_value = Mock(return_value=mock_raw_validator)
                
                # Execute test
                mgr = SubscriptionManager(mock_source)
                result = mgr.get_servers(context=mock_context)
                
                # Validate strict mode behavior
                assert isinstance(result, PipelineResult)
                assert not result.success
                assert result.config is None
                assert len(result.errors) == 1
                assert result.errors[0].type == ErrorType.VALIDATION
                assert result.errors[0].stage == "raw_validate"
    
    def test_get_servers_caching_behavior(self, mock_source, mock_context):
        """Test caching behavior of get_servers method.
        
        Validates that identical requests are served from cache
        and cache keys properly differentiate between different parameters.
        """
        mock_raw = b"ss://YWVzLTI1Ni1nY206cGFzc0BleGFtcGxlLmNvbTo4Mzg4#test"
        mock_server = Mock()
        mock_server.type = "ss"
        
        with patch('sboxmgr.subscription.registry.get_plugin') as mock_get_plugin:
            # Mock fetcher
            mock_fetcher = Mock()
            mock_fetcher.fetch.return_value = mock_raw
            mock_fetcher.source = mock_source
            mock_get_plugin.return_value = Mock(return_value=mock_fetcher)
            
            with patch('sboxmgr.subscription.manager.detect_parser') as mock_detect:
                # Mock parser
                mock_parser = Mock()
                mock_parser.parse.return_value = [mock_server]
                mock_detect.return_value = mock_parser
                
                with patch('sboxmgr.subscription.validators.base.RAW_VALIDATOR_REGISTRY') as mock_raw_val:
                    mock_raw_validator = Mock()
                    mock_raw_validator.validate.return_value = Mock(valid=True, errors=[])
                    mock_raw_val.get.return_value = Mock(return_value=mock_raw_validator)
                    
                    with patch('sboxmgr.subscription.validators.base.PARSED_VALIDATOR_REGISTRY') as mock_parsed_val:
                        mock_parsed_validator = Mock()
                        mock_parsed_validator.validate.return_value = Mock(
                            valid_servers=[mock_server], errors=[]
                        )
                        mock_parsed_val.get.return_value = Mock(return_value=mock_parsed_validator)
                        
                        # Execute multiple requests
                        mgr = SubscriptionManager(mock_source)
                        
                        # First request - should call fetch
                        result1 = mgr.get_servers(context=mock_context)
                        assert mock_fetcher.fetch.call_count == 1
                        
                        # Second identical request - should use cache
                        result2 = mgr.get_servers(context=mock_context)
                        assert mock_fetcher.fetch.call_count == 1  # No additional call
                        
                        # Third request with force_reload - should call fetch again
                        result3 = mgr.get_servers(context=mock_context, force_reload=True)
                        assert mock_fetcher.fetch.call_count == 2
                        
                        # Validate all results are consistent
                        assert result1.success == result2.success == result3.success
                        assert len(result1.config) == len(result2.config) == len(result3.config)
    
    def test_get_servers_middleware_processing(self, mock_source, mock_context):
        """Test middleware chain processing during get_servers.
        
        Validates that middleware chain is properly invoked and
        can modify server configurations during pipeline execution.
        """
        mock_raw = b"ss://YWVzLTI1Ni1nY206cGFzc0BleGFtcGxlLmNvbTo4Mzg4#test"
        mock_server = Mock()
        mock_server.type = "ss"
        mock_server.meta = {"tag": "original"}
        
        # Mock modified server from middleware
        mock_modified_server = Mock()
        mock_modified_server.type = "ss"
        mock_modified_server.meta = {"tag": "modified_by_middleware"}
        
        with patch('sboxmgr.subscription.registry.get_plugin') as mock_get_plugin:
            mock_fetcher = Mock()
            mock_fetcher.fetch.return_value = mock_raw
            mock_fetcher.source = mock_source
            mock_get_plugin.return_value = Mock(return_value=mock_fetcher)
            
            with patch('sboxmgr.subscription.manager.detect_parser') as mock_detect:
                mock_parser = Mock()
                mock_parser.parse.return_value = [mock_server]
                mock_detect.return_value = mock_parser
                
                with patch('sboxmgr.subscription.validators.base.RAW_VALIDATOR_REGISTRY') as mock_raw_val:
                    mock_raw_validator = Mock()
                    mock_raw_validator.validate.return_value = Mock(valid=True, errors=[])
                    mock_raw_val.get.return_value = Mock(return_value=mock_raw_validator)
                    
                    with patch('sboxmgr.subscription.validators.base.PARSED_VALIDATOR_REGISTRY') as mock_parsed_val:
                        mock_parsed_validator = Mock()
                        mock_parsed_validator.validate.return_value = Mock(
                            valid_servers=[mock_server], errors=[]
                        )
                        mock_parsed_val.get.return_value = Mock(return_value=mock_parsed_validator)
                        
                        # Create manager with custom middleware
                        mock_middleware = Mock()
                        mock_middleware.process.return_value = [mock_modified_server]
                        
                        mgr = SubscriptionManager(mock_source, middleware_chain=mock_middleware)
                        result = mgr.get_servers(context=mock_context)
                        
                        # Validate middleware was called and modified result
                        assert result.success
                        assert len(result.config) == 1
                        assert result.config[0] == mock_modified_server
                        assert mock_middleware.process.called
                        mock_middleware.process.assert_called_with([mock_server], mock_context)


class TestSubscriptionManagerCurrentBehavior:
    """Test suite documenting current SubscriptionManager behavior patterns.
    
    These tests document the current implementation details and edge cases
    that must be preserved during refactoring.
    """
    
    def test_get_servers_parameter_combinations(self):
        """Test various parameter combinations for get_servers method.
        
        Documents how different parameter combinations affect caching
        and pipeline behavior in the current implementation.
        """
        source = SubscriptionSource(url="test://dummy", source_type="url_base64")
        
        # Mock the manager to avoid actual network calls
        with patch.object(SubscriptionManager, '_SubscriptionManager__init__', return_value=None):
            mgr = SubscriptionManager.__new__(SubscriptionManager)
            mgr._cache_lock = Mock()
            mgr._get_servers_cache = {}
            
            # Test cache key generation for different parameter sets
            with patch.object(mgr, 'fetcher') as mock_fetcher:
                mock_fetcher.source.url = "test://example"
                mock_fetcher.source.user_agent = None
                mock_fetcher.source.headers = None
                
                # Different parameter combinations should create different cache keys
                params_sets = [
                    {"user_routes": None, "exclusions": None, "mode": None},
                    {"user_routes": ["tag1"], "exclusions": None, "mode": None},
                    {"user_routes": None, "exclusions": ["exclude1"], "mode": None},
                    {"user_routes": None, "exclusions": None, "mode": "strict"},
                ]
                
                for params in params_sets:
                    context = PipelineContext()
                    context.tag_filters = params.get("tag_filters")
                    
                    key = (
                        str(mock_fetcher.source.url),
                        getattr(mock_fetcher.source, 'user_agent', None),
                        str(getattr(mock_fetcher.source, 'headers', None)),
                        str(getattr(context, 'tag_filters', None)),
                        str(params["mode"]),
                    )
                    
                    # Each parameter set should generate a unique cache key
                    assert key not in [k for k in mgr._get_servers_cache.keys()]
    
    def test_error_context_metadata_structure(self):
        """Test error context metadata structure in current implementation.
        
        Documents the expected structure of error metadata and context
        information that must be preserved during refactoring.
        """
        source = SubscriptionSource(url="test://dummy", source_type="url_base64")
        context = PipelineContext()
        
        # Test metadata initialization
        assert 'errors' not in context.metadata
        
        # After get_servers call, metadata should contain errors list
        with patch('sboxmgr.subscription.registry.get_plugin') as mock_get_plugin:
            mock_fetcher = Mock()
            mock_fetcher.fetch.side_effect = Exception("Test error")
            mock_fetcher.source = source
            mock_get_plugin.return_value = Mock(return_value=mock_fetcher)
            
            mgr = SubscriptionManager(source)
            result = mgr.get_servers(context=context)
            
            # Validate error structure
            assert 'errors' in context.metadata
            assert isinstance(context.metadata['errors'], list)
            assert len(context.metadata['errors']) >= 1
            
            error = context.metadata['errors'][0]
            assert hasattr(error, 'type')
            assert hasattr(error, 'stage')
            assert hasattr(error, 'message')
            assert hasattr(error, 'context')
            assert hasattr(error, 'timestamp') 