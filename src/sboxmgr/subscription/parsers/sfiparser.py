"""SFI (Sing-box Format Import) parser implementation.

This module provides the SFIParser class for parsing SFI-format subscription
data. SFI is a specialized format for sing-box configuration imports that
provides native compatibility with sing-box outbound configurations and
routing rules.
"""
from ..registry import register
from ..base_parser import BaseParser


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

