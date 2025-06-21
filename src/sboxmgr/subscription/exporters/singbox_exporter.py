import json
from typing import List
from ..models import ParsedServer
from ..base_exporter import BaseExporter

class SingboxExporter(BaseExporter):
    def export(self, servers: List[ParsedServer]) -> str:
        # Преобразуем ParsedServer в outbounds (минимально)
        outbounds = []
        for s in servers:
            out = {
                "type": s.type,
                "server": s.address,
                "server_port": s.port,
            }
            if s.security:
                out["security"] = s.security
            out.update(s.meta or {})
            outbounds.append(out)
        config = {"outbounds": outbounds}
        return json.dumps(config, indent=2, ensure_ascii=False) 