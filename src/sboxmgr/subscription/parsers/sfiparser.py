from ..registry import register
from ..base_parser import BaseParser
from ..models import SubscriptionSource, ParsedServer


@register("custom_parser")
class SfiParser(BaseParser):
    """SfiParser parses subscription data.

    Example:
        parser = SfiParser()
        servers = parser.parse(raw)
    """
    def parse(self, raw: bytes):
        """Parse subscription data.

        Args:
            raw (bytes): Raw data.

        Returns:
            list[ParsedServer]: Servers.
        """
        raise NotImplementedError()

