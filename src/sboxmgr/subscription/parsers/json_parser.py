import json
import re
from typing import List, Tuple
from ..models import ParsedServer
from ..base_parser import BaseParser
from sboxmgr.utils.env import get_debug_level
from ..registry import register

@register("json")
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

@register("tolerant_json")
class TolerantJSONParser(BaseParser):
    def parse(self, raw: bytes) -> List[ParsedServer]:
        debug_level = get_debug_level()
        clean_json, removed = self._strip_comments_and_validate(raw.decode("utf-8"))
        if removed and debug_level > 0:
            print(f"[TolerantJSONParser] Removed comments/fields: {removed}")
        try:
            data = json.loads(clean_json)
        except Exception as e:
            if debug_level > 0:
                print(f"[TolerantJSONParser] JSON parse error after cleaning: {e}")
            raise
        # TODO: распарсить data в список ParsedServer (заглушка)
        return []

    def _strip_comments_and_validate(self, raw_data: str) -> Tuple[str, list]:
        removed = []
        # Удаляем leading комментарии и шум до первой { или [
        lines = raw_data.splitlines()
        clean_lines = []
        found_json_start = False
        for line in lines:
            l = line.strip()
            if not found_json_start:
                if l.startswith("{") or l.startswith("["):
                    found_json_start = True
                    clean_lines.append(line)
                else:
                    removed.append(line)
                continue
            # После старта JSON — обычная очистка
            if l.startswith("//") or l.startswith("#"):
                removed.append(line)
                continue
            # Удаляем inline // и # комментарии
            if '//' in line:
                idx = line.index('//')
                removed.append(line[idx:])
                line = line[:idx]
            if '#' in line and not line.lstrip().startswith('#'):
                idx = line.index('#')
                removed.append(line[idx:])
                line = line[:idx]
            clean_lines.append(line)
        clean_json = '\n'.join(clean_lines)
        # Удаляем поля _comment и trailing commas
        clean_json = re.sub(r'"_comment"\s*:\s*".*?",?', '', clean_json)
        clean_json = re.sub(r',\s*([}\]])', r'\1', clean_json)
        return clean_json, removed 