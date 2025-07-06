"""Tests for Phase 3 postprocessor architecture.

This module tests the enhanced postprocessor architecture including
profile integration, chain execution, error handling, and metadata
collection features introduced in Phase 3.
"""

from unittest.mock import Mock

import pytest

from src.sboxmgr.profiles.models import FilterProfile, FullProfile
from src.sboxmgr.subscription.models import ParsedServer, PipelineContext
from src.sboxmgr.subscription.postprocessors import (
    BasePostProcessor,
    GeoFilterPostProcessor,
    LatencySortPostProcessor,
    PostProcessorChain,
    ProfileAwarePostProcessor,
    TagFilterPostProcessor,
)


class TestBasePostProcessor:
    """Test enhanced BasePostProcessor functionality."""

    def test_base_postprocessor_initialization(self):
        """Test base postprocessor initialization with config."""
        config = {"test_option": "test_value"}

        class TestProcessor(BasePostProcessor):
            def process(self, servers, context=None, profile=None):
                return servers

        processor = TestProcessor(config)
        assert processor.config == config
        assert processor.plugin_type == "postprocessor"

    def test_can_process_method(self):
        """Test can_process method logic."""

        class TestProcessor(BasePostProcessor):
            def process(self, servers, context=None, profile=None):
                return servers

        processor = TestProcessor()

        # Should return True for non-empty server list
        servers = [Mock(spec=ParsedServer)]
        assert processor.can_process(servers) is True

        # Should return False for empty server list
        assert processor.can_process([]) is False

    def test_get_metadata_method(self):
        """Test get_metadata method."""
        config = {"option1": "value1", "option2": "value2"}

        class TestProcessor(BasePostProcessor):
            def process(self, servers, context=None, profile=None):
                return servers

        processor = TestProcessor(config)
        metadata = processor.get_metadata()

        assert metadata["name"] == "TestProcessor"
        assert metadata["type"] == "postprocessor"
        assert metadata["config"] == config


class TestProfileAwarePostProcessor:
    """Test ProfileAwarePostProcessor functionality."""

    def test_extract_filter_config(self):
        """Test filter configuration extraction from profile."""
        filter_profile = FilterProfile(
            exclude_tags=["blocked", "slow"],
            only_tags=["premium"],
            exclusions=["bad.server.com"],
        )
        profile = FullProfile(id="test", filters=filter_profile)

        class TestProcessor(ProfileAwarePostProcessor):
            def process(self, servers, context=None, profile=None):
                return servers

        processor = TestProcessor()
        extracted_config = processor.extract_filter_config(profile)

        assert extracted_config == filter_profile
        assert extracted_config.exclude_tags == ["blocked", "slow"]
        assert extracted_config.only_tags == ["premium"]

    def test_should_exclude_server(self):
        """Test server exclusion logic."""
        filter_profile = FilterProfile(
            exclude_tags=["blocked"],
            only_tags=["premium"],
            exclusions=["bad.server.com:8080"],
        )

        class TestProcessor(ProfileAwarePostProcessor):
            def process(self, servers, context=None, profile=None):
                return servers

        processor = TestProcessor()

        # Test tag exclusion
        server1 = ParsedServer(
            type="vmess", address="test.com", port=443, tag="blocked"
        )
        assert processor.should_exclude_server(server1, filter_profile) is True

        # Test only_tags filtering
        server2 = ParsedServer(type="vmess", address="test.com", port=443, tag="basic")
        assert processor.should_exclude_server(server2, filter_profile) is True

        # Test address exclusion
        server3 = ParsedServer(
            type="vmess", address="bad.server.com", port=8080, tag="premium"
        )
        assert processor.should_exclude_server(server3, filter_profile) is True

        # Test valid server
        server4 = ParsedServer(
            type="vmess", address="good.server.com", port=443, tag="premium"
        )
        assert processor.should_exclude_server(server4, filter_profile) is False


class TestGeoFilterPostProcessor:
    """Test GeoFilterPostProcessor functionality."""

    def test_initialization(self):
        """Test geo filter initialization."""
        config = {
            "allowed_countries": ["US", "CA"],
            "blocked_countries": ["CN"],
            "fallback_mode": "allow_all",
        }
        processor = GeoFilterPostProcessor(config)

        assert processor.allowed_countries == ["US", "CA"]
        assert processor.blocked_countries == ["CN"]
        assert processor.fallback_mode == "allow_all"

    def test_extract_country_code(self):
        """Test country code extraction from server metadata."""
        processor = GeoFilterPostProcessor()

        # Test with country in meta
        server1 = ParsedServer(
            type="vmess", address="test.com", port=443, meta={"country": "us"}
        )
        assert processor._extract_country_code(server1) == "US"

        # Test with geo metadata
        server2 = ParsedServer(
            type="vmess", address="test.com", port=443, meta={"geo": {"country": "ca"}}
        )
        assert processor._extract_country_code(server2) == "CA"

        # Test with tag extraction
        server3 = ParsedServer(
            type="vmess", address="test.com", port=443, tag="US-Server-1"
        )
        assert processor._extract_country_code(server3) == "US"

        # Test with domain TLD
        server4 = ParsedServer(type="vmess", address="server.uk", port=443)
        assert processor._extract_country_code(server4) == "UK"

    def test_geo_filtering(self):
        """Test geographic filtering logic."""
        config = {
            "allowed_countries": ["US", "CA"],
            "blocked_countries": ["CN"],
            "fallback_mode": "allow_all",
        }
        processor = GeoFilterPostProcessor(config)

        servers = [
            ParsedServer(
                type="vmess", address="us.server.com", port=443, meta={"country": "US"}
            ),
            ParsedServer(
                type="vmess", address="ca.server.com", port=443, meta={"country": "CA"}
            ),
            ParsedServer(
                type="vmess", address="cn.server.com", port=443, meta={"country": "CN"}
            ),
            ParsedServer(type="vmess", address="unknown.com", port=443),
        ]

        context = PipelineContext()
        filtered = processor.process(servers, context)

        # Should include US and CA servers, exclude CN, include unknown (fallback)
        assert len(filtered) == 3
        countries = [s.meta.get("country") for s in filtered]
        assert "US" in countries
        assert "CA" in countries
        assert "CN" not in countries


class TestTagFilterPostProcessor:
    """Test TagFilterPostProcessor functionality."""

    def test_initialization(self):
        """Test tag filter initialization."""
        config = {
            "include_tags": ["premium", "fast"],
            "exclude_tags": ["blocked"],
            "case_sensitive": False,
        }
        processor = TagFilterPostProcessor(config)

        assert "premium" in processor.include_tags
        assert "fast" in processor.include_tags
        assert "blocked" in processor.exclude_tags
        assert processor.case_sensitive is False

    def test_extract_server_tags(self):
        """Test tag extraction from server."""
        processor = TagFilterPostProcessor()

        # Test primary tag field
        server1 = ParsedServer(
            type="vmess", address="test.com", port=443, tag="premium"
        )
        tags = processor._extract_server_tags(server1)
        assert "premium" in tags

        # Test meta tags
        server2 = ParsedServer(
            type="vmess",
            address="test.com",
            port=443,
            meta={"tags": ["fast", "reliable"]},
        )
        tags = processor._extract_server_tags(server2)
        assert "fast" in tags
        assert "reliable" in tags

        # Test name parsing
        server3 = ParsedServer(
            type="vmess", address="test.com", port=443, meta={"name": "US-Premium-01"}
        )
        tags = processor._extract_server_tags(server3)
        assert "US" in tags
        assert "Premium" in tags
        assert "01" in tags

    def test_tag_filtering(self):
        """Test tag-based filtering logic."""
        config = {
            "include_tags": ["premium"],
            "exclude_tags": ["blocked"],
            "case_sensitive": False,
        }
        processor = TagFilterPostProcessor(config)

        servers = [
            ParsedServer(type="vmess", address="test1.com", port=443, tag="premium"),
            ParsedServer(type="vmess", address="test2.com", port=443, tag="blocked"),
            ParsedServer(type="vmess", address="test3.com", port=443, tag="basic"),
            ParsedServer(
                type="vmess", address="test4.com", port=443, tag="PREMIUM"
            ),  # Case test
        ]

        context = PipelineContext()
        filtered = processor.process(servers, context)

        # Should include premium servers (case insensitive), exclude blocked and basic
        assert len(filtered) == 2
        tags = [s.tag for s in filtered]
        assert "premium" in tags
        assert "PREMIUM" in tags
        assert "blocked" not in tags


class TestLatencySortPostProcessor:
    """Test LatencySortPostProcessor functionality."""

    def test_initialization(self):
        """Test latency sort initialization."""
        config = {
            "sort_order": "asc",
            "max_latency_ms": 500,
            "measurement_method": "cached",
        }
        processor = LatencySortPostProcessor(config)

        assert processor.sort_order == "asc"
        assert processor.max_latency_ms == 500
        assert processor.measurement_method == "cached"

    def test_latency_sorting(self):
        """Test latency-based sorting."""
        config = {
            "sort_order": "asc",
            "measurement_method": "cached",
            "fallback_latency": 1000,
        }
        processor = LatencySortPostProcessor(config)

        servers = [
            ParsedServer(
                type="vmess", address="slow.com", port=443, meta={"latency_ms": 300}
            ),
            ParsedServer(
                type="vmess", address="fast.com", port=443, meta={"latency_ms": 50}
            ),
            ParsedServer(
                type="vmess", address="medium.com", port=443, meta={"latency_ms": 150}
            ),
        ]

        context = PipelineContext()
        sorted_servers = processor._do_process(servers, context)

        # Should be sorted by latency ascending
        latencies = [s.meta["latency_ms"] for s in sorted_servers]
        assert latencies == [50, 150, 300]
        assert sorted_servers[0].address == "fast.com"
        assert sorted_servers[-1].address == "slow.com"

    def test_can_process(self):
        """Test can_process logic for latency sorting."""
        processor = LatencySortPostProcessor()

        # Should return True for multiple servers
        servers = [Mock(spec=ParsedServer), Mock(spec=ParsedServer)]
        assert processor.can_process(servers) is True

        # Should return False for single server (no point in sorting)
        single_server = [Mock(spec=ParsedServer)]
        assert processor.can_process(single_server) is False


class TestPostProcessorChain:
    """Test PostProcessorChain functionality."""

    def test_initialization(self):
        """Test chain initialization."""
        processors = [Mock(spec=BasePostProcessor), Mock(spec=BasePostProcessor)]
        config = {"execution_mode": "sequential", "error_strategy": "continue"}

        chain = PostProcessorChain(processors, config)

        assert len(chain.processors) == 2
        assert chain.execution_mode == "sequential"
        assert chain.error_strategy == "continue"

    def test_sequential_execution(self):
        """Test sequential processor execution."""
        # Create mock processors
        processor1 = Mock(spec=BasePostProcessor)
        processor2 = Mock(spec=BasePostProcessor)

        # Configure processor behavior
        processor1.can_process.return_value = True
        processor2.can_process.return_value = True
        processor1.get_metadata.return_value = {"name": "Processor1"}
        processor2.get_metadata.return_value = {"name": "Processor2"}

        # Configure process methods
        servers_input = [Mock(spec=ParsedServer)]
        servers_intermediate = [Mock(spec=ParsedServer), Mock(spec=ParsedServer)]
        servers_output = [Mock(spec=ParsedServer)]

        processor1.process.return_value = servers_intermediate
        processor2.process.return_value = servers_output

        # Create and execute chain
        chain = PostProcessorChain(
            [processor1, processor2], {"execution_mode": "sequential"}
        )
        context = PipelineContext()
        result = chain.process(servers_input, context)

        # Verify execution order and results
        processor1.process.assert_called_once_with(servers_input, context, None)
        processor2.process.assert_called_once_with(servers_intermediate, context, None)
        assert result == servers_output

    def test_error_handling(self):
        """Test error handling strategies."""
        # Create processor that raises exception
        failing_processor = Mock(spec=BasePostProcessor)
        failing_processor.can_process.return_value = True
        failing_processor.process.side_effect = Exception("Test error")
        failing_processor.get_metadata.return_value = {"name": "FailingProcessor"}

        success_processor = Mock(spec=BasePostProcessor)
        success_processor.can_process.return_value = True
        success_processor.process.return_value = [Mock(spec=ParsedServer)]
        success_processor.get_metadata.return_value = {"name": "SuccessProcessor"}

        # Test continue strategy
        chain = PostProcessorChain(
            [failing_processor, success_processor],
            {"execution_mode": "sequential", "error_strategy": "continue"},
        )

        servers = [Mock(spec=ParsedServer)]
        context = PipelineContext()
        chain.process(servers, context)

        # Should continue processing despite error
        success_processor.process.assert_called_once()
        assert len(chain._execution_metadata["processors_failed"]) == 1
        # The name will be the class name of the mock object
        assert (
            "Mock" in chain._execution_metadata["processors_failed"][0]["name"]
            or "BasePostProcessor"
            in chain._execution_metadata["processors_failed"][0]["name"]
        )

    def test_processor_management(self):
        """Test adding and removing processors."""
        processor1 = Mock(spec=BasePostProcessor)
        processor2 = Mock(spec=BasePostProcessor)
        processor3 = Mock(spec=BasePostProcessor)

        chain = PostProcessorChain([processor1])

        # Test adding processor
        chain.add_processor(processor2)
        assert len(chain.processors) == 2
        assert processor2 in chain.processors

        # Test inserting processor
        chain.add_processor(processor3, index=0)
        assert len(chain.processors) == 3
        assert chain.processors[0] == processor3

        # Test removing by index
        assert chain.remove_processor(0) is True
        assert processor3 not in chain.processors

        # Test removing by instance
        assert chain.remove_processor(processor2) is True
        assert processor2 not in chain.processors

    def test_can_process(self):
        """Test chain can_process logic."""
        processor1 = Mock(spec=BasePostProcessor)
        processor2 = Mock(spec=BasePostProcessor)

        processor1.can_process.return_value = False
        processor2.can_process.return_value = True

        chain = PostProcessorChain([processor1, processor2])

        servers = [Mock(spec=ParsedServer)]
        # Should return True if at least one processor can process
        assert chain.can_process(servers) is True

        # Test with no capable processors
        processor2.can_process.return_value = False
        assert chain.can_process(servers) is False


if __name__ == "__main__":
    pytest.main([__file__])
