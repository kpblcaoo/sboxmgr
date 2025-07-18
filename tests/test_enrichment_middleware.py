from sboxmgr.subscription.middleware.enrichment.core import EnrichmentMiddleware
from sboxmgr.subscription.middleware.tag_normalizer import TagNormalizer
from sboxmgr.subscription.models import ParsedServer, PipelineContext


class TestEnrichmentMiddleware:
    def setup_method(self):
        self.middleware = EnrichmentMiddleware()
        self.context = PipelineContext(source="test")

    def test_enrichment_preserves_tags(self):
        """Test that EnrichmentMiddleware preserves existing tags and does not normalize them."""
        servers = [
            ParsedServer(
                type="vless",
                address="1.1.1.1",
                port=443,
                tag="Test Server",
                meta={"name": "Test Server"},
            ),
            ParsedServer(
                type="vless",
                address="2.2.2.2",
                port=443,
                tag="Test Server (1)",
                meta={"name": "Test Server"},
            ),
            ParsedServer(
                type="vless",
                address="3.3.3.3",
                port=443,
                tag="Test Server (2)",
                meta={"name": "Test Server"},
            ),
        ]
        result = self.middleware.process(servers, self.context)
        tags = [s.tag for s in result]
        # EnrichmentMiddleware should preserve existing tags, not normalize them
        assert tags[0] == "Test Server"
        assert tags[1] == "Test Server (1)"
        assert tags[2] == "Test Server (2)"
        assert len(set(tags)) == 3

    def test_enrichment_without_tag_normalization(self):
        """Test that EnrichmentMiddleware does not perform tag normalization."""
        servers = [
            ParsedServer(
                type="vless",
                address="1.1.1.1",
                port=443,
                tag="",
                meta={"name": "Test Server"},
            ),
            ParsedServer(
                type="vless",
                address="2.2.2.2",
                port=443,
                tag="",
                meta={"name": "Test Server"},
            ),
        ]
        result = self.middleware.process(servers, self.context)
        # EnrichmentMiddleware should not normalize tags, so they should remain empty
        assert result[0].tag == ""
        assert result[1].tag == ""

    def test_enrichment_adds_metadata(self):
        """Test that EnrichmentMiddleware adds enrichment metadata."""
        server = ParsedServer(
            type="vless", address="1.1.1.1", port=443, tag="test", meta={}
        )
        result = self.middleware.process([server], self.context)[0]

        # EnrichmentMiddleware should add basic metadata
        assert "enriched_at" in result.meta
        assert "trace_id" in result.meta
        assert "server_id" in result.meta
        assert "source" in result.meta

    def test_integration_with_tag_normalizer(self):
        """Test that EnrichmentMiddleware works correctly with TagNormalizer in pipeline."""
        servers = [
            ParsedServer(
                type="vless", address="1.1.1.1", port=443, meta={"name": "Alpha"}
            ),
            ParsedServer(
                type="vless", address="2.2.2.2", port=443, meta={"label": "Beta"}
            ),
            ParsedServer(
                type="vless", address="3.3.3.3", port=443, meta={"tag": "Gamma"}
            ),
            ParsedServer(
                type="vless", address="4.4.4.4", port=443, tag="Delta", meta={}
            ),
            ParsedServer(type="vless", address="5.5.5.5", port=443, tag="", meta={}),
        ]

        # First, normalize tags with TagNormalizer
        normalizer = TagNormalizer()
        normalized_servers = normalizer.process(servers, self.context)

        # Then, enrich with EnrichmentMiddleware
        enriched_servers = self.middleware.process(normalized_servers, self.context)

        # Tags should remain normalized from TagNormalizer
        assert enriched_servers[0].tag == "Alpha"
        assert enriched_servers[1].tag == "Beta"
        assert enriched_servers[2].tag == "Gamma"
        assert enriched_servers[3].tag == "Delta"
        assert enriched_servers[4].tag == "vless-5.5.5.5"  # TagNormalizer fallback

        # All tags should be unique
        tags = [s.tag for s in enriched_servers]
        assert len(set(tags)) == len(tags)

    def test_enrichment_configuration(self):
        """Test that EnrichmentMiddleware respects configuration options."""
        config = {
            "enable_geo_enrichment": False,
            "enable_performance_enrichment": False,
            "enable_security_enrichment": False,
            "enable_custom_enrichment": False,
        }
        middleware = EnrichmentMiddleware(config)

        server = ParsedServer(
            type="vless", address="1.1.1.1", port=443, tag="test", meta={}
        )
        result = middleware.process([server], self.context)[0]

        # Should still add basic metadata even with all enrichment disabled
        assert result.tag == "test"  # Tag preserved
        assert "enriched_at" in result.meta
        assert "trace_id" in result.meta
        assert "server_id" in result.meta
        assert "source" in result.meta
