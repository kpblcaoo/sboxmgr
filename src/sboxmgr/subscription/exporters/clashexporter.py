from ..registry import register
from ..base_exporter import BaseExporter


@register("custom_exporter")
class ClashExporter(BaseExporter):
    """ClashExporter exports parsed servers to config.

Example:
    exporter = ClashExporter()
    config = exporter.export(servers)"""
    def export(self, servers):
        """Export parsed servers to config.

        Args:
            servers (list[ParsedServer]): List of servers.

        Returns:
            dict: Exported config.
        """
        raise NotImplementedError()

