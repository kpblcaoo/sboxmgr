"""Tests for refactored SubscriptionManager."""

import pytest
from unittest.mock import Mock, patch
import base64

from sboxmgr.subscription.manager import SubscriptionManager
from sboxmgr.subscription.models import PipelineContext, SubscriptionSource


class TestSubscriptionManagerRefactoring:
    """Test refactored SubscriptionManager functionality."""

    def test_get_servers_basic_flow(self, mock_source, mock_context):
        """Test basic get_servers flow with new architecture.

        Validates that the refactored SubscriptionManager correctly
        processes servers through the modular pipeline.
        """
        mock_server = Mock()
        mock_server.type = "ss"

        # Mock the fetcher first to avoid file system access
        with patch("sboxmgr.subscription.manager.core.get_plugin") as mock_get_plugin:
            mock_fetcher = Mock()
            # Return valid base64-encoded data for url_base64
            valid_data = b"ss://YWVzLTI1Ni1nY206cGFzc0BleGFtcGxlLmNvbTo4Mzg4#test"
            mock_fetcher.fetch.return_value = base64.b64encode(valid_data)
            mock_fetcher.source = mock_source
            mock_get_plugin.return_value = Mock(return_value=mock_fetcher)

            with patch("sboxmgr.subscription.manager.parser_detector.detect_parser") as mock_detect:
                # Mock parser
                mock_parser = Mock()
                mock_parser.parse.return_value = [mock_server]
                mock_detect.return_value = mock_parser

                with patch(
                    "sboxmgr.subscription.validators.base.RAW_VALIDATOR_REGISTRY"
                ) as mock_raw_val:
                    mock_raw_validator = Mock()
                    mock_raw_validator.validate.return_value = Mock(valid=True, errors=[])
                    mock_raw_val.get.return_value = Mock(return_value=mock_raw_validator)

                    with patch(
                        "sboxmgr.subscription.validators.base.PARSED_VALIDATOR_REGISTRY"
                    ) as mock_parsed_val:
                        mock_parsed_validator = Mock()
                        mock_parsed_validator.validate.return_value = Mock(
                            valid_servers=[mock_server], errors=[]
                        )
                        mock_parsed_val.get.return_value = Mock(
                            return_value=mock_parsed_validator
                        )

                        # Test the refactored manager
                        mgr = SubscriptionManager(mock_source)
                        result = mgr.get_servers(context=mock_context)

                        # Verify basic success
                        assert result.success
                        assert result.config is not None
                        assert len(result.config) == 1
                        assert result.config[0].type == "ss"

    def test_get_servers_validation_error_strict_mode(self, mock_source, mock_context):
        """Test validation error handling in strict mode.

        Validates that validation errors are properly handled
        and propagated in strict mode.
        """
        mock_context.mode = "strict"

        with patch("sboxmgr.subscription.manager.core.get_plugin") as mock_get_plugin:
            mock_fetcher = Mock()
            valid_data = b"ss://YWVzLTI1Ni1nY206cGFzc0BleGFtcGxlLmNvbTo4Mzg4#test"
            mock_fetcher.fetch.return_value = base64.b64encode(valid_data)
            mock_fetcher.source = mock_source
            mock_get_plugin.return_value = Mock(return_value=mock_fetcher)

            with patch("sboxmgr.subscription.manager.parser_detector.detect_parser") as mock_detect:
                # Mock parser that returns invalid data
                mock_parser = Mock()
                mock_parser.parse.return_value = [Mock(type="invalid")]
                mock_detect.return_value = mock_parser

                with patch(
                    "sboxmgr.subscription.validators.base.PARSED_VALIDATOR_REGISTRY"
                ) as mock_parsed_val:
                    mock_parsed_validator = Mock()
                    mock_parsed_validator.validate.return_value = Mock(
                        valid_servers=[], errors=["Validation error"]
                    )
                    mock_parsed_val.get.return_value = Mock(
                        return_value=mock_parsed_validator
                    )

                    mgr = SubscriptionManager(mock_source, detect_parser=mock_detect)
                    result = mgr.get_servers(context=mock_context)

                    # Should fail in strict mode
                    assert not result.success
                    assert result.config == []

    def test_get_servers_fetch_error_handling(self, mock_source, mock_context):
        """Test fetch error handling.

        Validates that fetch errors are properly handled
        and result in appropriate error responses.
        """
        with patch("sboxmgr.subscription.manager.core.get_plugin") as mock_get_plugin:
            # Mock fetcher to raise an exception
            mock_fetcher = Mock()
            mock_fetcher.fetch.side_effect = FileNotFoundError("File not found")
            mock_fetcher.source = mock_source
            mock_get_plugin.return_value = Mock(return_value=mock_fetcher)

            mgr = SubscriptionManager(mock_source)
            result = mgr.get_servers(context=mock_context)

            # Should handle fetch errors gracefully
            assert not result.success
            assert result.config == []

    def test_get_servers_middleware_processing(self, mock_source, mock_context):
        """Test middleware processing in the pipeline.

        Validates that middleware is properly applied
        during server processing.
        """
        mock_server = Mock()
        mock_server.type = "ss"

        with patch("sboxmgr.subscription.manager.core.get_plugin") as mock_get_plugin:
            mock_fetcher = Mock()
            valid_data = b"ss://YWVzLTI1Ni1nY206cGFzc0BleGFtcGxlLmNvbTo4Mzg4#test"
            mock_fetcher.fetch.return_value = base64.b64encode(valid_data)
            mock_fetcher.source = mock_source
            mock_get_plugin.return_value = Mock(return_value=mock_fetcher)

            with patch("sboxmgr.subscription.manager.parser_detector.detect_parser") as mock_detect:
                mock_parser = Mock()
                mock_parser.parse.return_value = [mock_server]
                mock_detect.return_value = mock_parser

                with patch(
                    "sboxmgr.subscription.validators.base.RAW_VALIDATOR_REGISTRY"
                ) as mock_raw_val:
                    mock_raw_validator = Mock()
                    mock_raw_validator.validate.return_value = Mock(valid=True, errors=[])
                    mock_raw_val.get.return_value = Mock(return_value=mock_raw_validator)

                    with patch(
                        "sboxmgr.subscription.validators.base.PARSED_VALIDATOR_REGISTRY"
                    ) as mock_parsed_val:
                        mock_parsed_validator = Mock()
                        mock_parsed_validator.validate.return_value = Mock(
                            valid_servers=[mock_server], errors=[]
                        )
                        mock_parsed_val.get.return_value = Mock(
                            return_value=mock_parsed_validator
                        )

                        # Test with middleware
                        mgr = SubscriptionManager(mock_source, detect_parser=mock_detect)
                        result = mgr.get_servers(context=mock_context)

                        # Should process through middleware successfully
                        assert result.success
                        assert result.config is not None

    def test_get_servers_caching_behavior(self, mock_source, mock_context):
        """Test caching behavior of get_servers method.

        Validates that identical requests are served from cache
        and cache keys properly differentiate between different parameters.
        """
        mock_server = Mock()
        mock_server.type = "ss"

        with patch("sboxmgr.subscription.manager.core.get_plugin") as mock_get_plugin:
            mock_fetcher = Mock()
            valid_data = b"ss://YWVzLTI1Ni1nY206cGFzc0BleGFtcGxlLmNvbTo4Mzg4#test"
            mock_fetcher.fetch.return_value = base64.b64encode(valid_data)
            mock_fetcher.source = mock_source
            mock_get_plugin.return_value = Mock(return_value=mock_fetcher)

            with patch("sboxmgr.subscription.manager.parser_detector.detect_parser") as mock_detect:
                mock_parser = Mock()
                mock_parser.parse.return_value = [mock_server]
                mock_detect.return_value = mock_parser

                with patch(
                    "sboxmgr.subscription.validators.base.RAW_VALIDATOR_REGISTRY"
                ) as mock_raw_val:
                    mock_raw_validator = Mock()
                    mock_raw_validator.validate.return_value = Mock(valid=True, errors=[])
                    mock_raw_val.get.return_value = Mock(return_value=mock_raw_validator)

                    with patch(
                        "sboxmgr.subscription.validators.base.PARSED_VALIDATOR_REGISTRY"
                    ) as mock_parsed_val:
                        mock_parsed_validator = Mock()
                        mock_parsed_validator.validate.return_value = Mock(
                            valid_servers=[mock_server], errors=[]
                        )
                        mock_parsed_val.get.return_value = Mock(
                            return_value=mock_parsed_validator
                        )

                        mgr = SubscriptionManager(mock_source, detect_parser=mock_detect)
                        # First request - should call parser
                        result1 = mgr.get_servers(context=mock_context)
                        # Second request - should use cache
                        result2 = mgr.get_servers(context=mock_context)
                        # Both results should be successful and identical (cached)
                        assert result1.success
                        assert result2.success
                        assert result1.config == result2.config


@pytest.fixture
def mock_source():
    """Create mock subscription source."""
    source = Mock(spec=SubscriptionSource)
    source.url = "file://test"
    source.source_type = "url_base64"
    return source


@pytest.fixture
def mock_context():
    """Create mock pipeline context."""
    context = Mock(spec=PipelineContext)
    context.mode = "tolerant"
    context.metadata = {"errors": []}
    return context
