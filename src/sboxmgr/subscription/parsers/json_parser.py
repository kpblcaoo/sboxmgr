import json
from typing import List
from ..models import ParsedServer
from ..base_parser import BaseParser
from sboxmgr.utils.env import get_debug_level

class JSONParser(BaseParser):
    def parse(self, raw: bytes) -> List[ParsedServer]:
        debug_level = get_debug_level()
        try:
            data = json.loads(raw.decode("utf-8"))
        except Exception as e:
            if debug_level > 1:
                print(f"[WARN] JSON parse error: {e}")
            raise  # выбрасываем ошибку дальше
        # TODO: распарсить data в список ParsedServer (заглушка)
        return [] 