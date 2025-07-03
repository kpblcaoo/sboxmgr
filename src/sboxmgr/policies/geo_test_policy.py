"""Example geo policy for demonstration purposes."""
from .base import BasePolicy, PolicyContext, PolicyResult

class GeoTestPolicy(BasePolicy):
    """Test policy for geo group (demo only)."""
    name = "GeoTestPolicy"
    description = "Demo geo policy that always allows."
    group = "geo"

    def evaluate(self, context: PolicyContext) -> PolicyResult:
        return PolicyResult.allow("GeoTestPolicy always allows") 