from ..registry import register
from ..postprocessor_base import BasePostProcessor
from ..models import SubscriptionSource, ParsedServer


@register("custom_postprocessor")
class GeoFilterPostProcessorPostprocessor(BasePostProcessor):
    """GeoFilterPostProcessorPostprocessor post-processes parsed servers.

Example:
    pp = GeoFilterPostProcessorPostprocessor()
    servers = pp.process(servers, context)"""
    def process(self, servers, context):
        """Post-process parsed servers.

        Args:
            servers (list[ParsedServer]): List of servers.
            context (PipelineContext): Pipeline context.

        Returns:
            list[ParsedServer]: Processed servers.
        """
        raise NotImplementedError()

