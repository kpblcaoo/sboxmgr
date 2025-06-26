"""Geographic filtering postprocessor implementation.

This module provides postprocessing functionality for filtering servers
based on geographic location. It supports country-based filtering, region
filtering, and custom geographic rules for optimizing server selection
based on user location and preferences.
"""

from ..registry import register
from ..postprocessor_base import BasePostProcessor
from ..models import PipelineContext


@register("geo_filter")
class GeoFilterPostProcessor(BasePostProcessor):
    """GeoFilterPostProcessor post-processes parsed servers.

    Example:
        pp = GeoFilterPostProcessor()
        servers = pp.process(servers, context)
    """

    def process(self, servers, context: PipelineContext | None = None):
        """Post-process parsed servers.

        Args:
            servers (list[ParsedServer]): List of servers.
            context (PipelineContext | None): Pipeline context.

        Returns:
            list[ParsedServer]: Processed servers.
        """
        raise NotImplementedError()

