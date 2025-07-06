import pytest
from sboxmgr.subscription.middleware.enrichment.core import EnrichmentMiddleware
from sboxmgr.subscription.middleware.tag_normalizer import TagNormalizer
from sboxmgr.subscription.models import ParsedServer, PipelineContext

class TestEnrichmentMiddleware:
    def setup_method(self):
        self.middleware = EnrichmentMiddleware()
        self.context = PipelineContext(source="test")

    def test_tag_uniqueness(self):
        """Test that EnrichmentMiddleware ensures tag uniqueness within a batch."""
        servers = [
            ParsedServer(type="vless", address="1.1.1.1", port=443, meta={"name": "Test Server"}),
            ParsedServer(type="vless", address="2.2.2.2", port=443, meta={"name": "Test Server"}),
            ParsedServer(type="vless", address="3.3.3.3", port=443, meta={"name": "Test Server"}),
        ]
        result = self.middleware.process(servers, self.context)
        tags = [s.tag for s in result]
        assert tags[0] == "Test Server"
        assert tags[1] == "Test Server (1)"
        assert tags[2] == "Test Server (2)"
        assert len(set(tags)) == 3

    @pytest.mark.parametrize(
        "meta,tag,expected",
        [
            ({"name": "A"}, "B", "A"),
            ({"label": "L"}, "B", "L"),
            ({"tag": "T"}, "B", "T"),
            ({}, "ParserTag", "ParserTag"),
            ({}, "", "vless-1.2.3.4"),
            ({}, "", None),  # Will fallback to protocol/id if no address
        ],
    )
    def test_priority_order(self, meta, tag, expected):
        """Test tag priority order in EnrichmentMiddleware (matches TagNormalizer)."""
        address = "1.2.3.4" if expected != None else ""
        server = ParsedServer(type="vless", address=address, port=443, tag=tag, meta=meta)
        result = self.middleware.process([server], self.context)[0]
        if expected is None:
            assert result.tag.startswith("vless-") and result.tag != "vless-"
        else:
            assert result.tag == expected

    def test_integration_with_tag_normalizer(self):
        """Test that EnrichmentMiddleware and TagNormalizer produce compatible tags."""
        servers = [
            ParsedServer(type="vless", address="1.1.1.1", port=443, meta={"name": "Alpha"}),
            ParsedServer(type="vless", address="2.2.2.2", port=443, meta={"label": "Beta"}),
            ParsedServer(type="vless", address="3.3.3.3", port=443, meta={"tag": "Gamma"}),
            ParsedServer(type="vless", address="4.4.4.4", port=443, tag="Delta", meta={}),
            ParsedServer(type="vless", address="5.5.5.5", port=443, tag="", meta={}),
        ]
        # EnrichmentMiddleware
        enriched = self.middleware.process(servers, self.context)
        # TagNormalizer
        normalizer = TagNormalizer()
        normalized = normalizer.process(servers, self.context)
        # Compare tags for the same logic (should match for single batch)
        for e, n in zip(enriched, normalized):
            assert e.tag == n.tag or e.tag.startswith(n.tag)
