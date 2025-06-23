from abc import ABC, abstractmethod
from .models import ParsedServer
from typing import List

class BaseExporter(ABC):
    """
    Базовый класс для экспортеров конфигов (sing-box, clash, v2ray и др.)
    Реализации должны преобразовывать список ParsedServer в строку нужного формата.
    """
    plugin_type = "exporter"

    @abstractmethod
    def export(self, servers: List[ParsedServer]) -> str:
        """Экспортировать список ParsedServer в строку (например, JSON, YAML)."""
        pass

# TODO: реализовать sing-box exporter и расширяемую архитектуру для других форматов 