from ..registry import register
from ..postprocessor_base import BasePostProcessor
from ..models import SubscriptionSource, ParsedServer


@register("geo_filter")
class GeoFilterPostProcessor(BasePostProcessor):
    """GeoFilterPostProcessor post-processes parsed servers.

Example:
    pp = GeoFilterPostProcessor()
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

