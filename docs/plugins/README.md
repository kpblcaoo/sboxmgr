# Плагины и генератор шаблонов (plugin-template)

Этот README содержит примеры и советы по использованию CLI-генератора шаблонов плагинов (`sboxctl plugin-template`) для расширения подписочного пайплайна.

---

## Быстрый старт

Сгенерировать шаблон плагина:
```bash
sboxctl plugin-template <type> <ClassName> --output-dir ./src/sboxmgr/subscription/<type>s/
```
- `<type>`: fetcher, parser, validator, exporter, postprocessor
- `<ClassName>`: имя класса (CamelCase, без суффикса)

**Пример:**
```bash
sboxctl plugin-template exporter ClashExporter --output-dir ./src/sboxmgr/subscription/exporters/
sboxctl plugin-template postprocessor GeoFilterPostProcessor --output-dir ./src/sboxmgr/subscription/postprocessors/
sboxctl plugin-template fetcher ApiFetcher --output-dir ./src/sboxmgr/subscription/fetchers/
sboxctl plugin-template parser SfiParser --output-dir ./src/sboxmgr/subscription/parsers/
sboxctl plugin-template validator GeoValidator --output-dir ./src/sboxmgr/subscription/validators/
```

---

## Пример сгенерированного класса (fetcher)
```python
from ..registry import register
from ..base_fetcher import BaseFetcher
from ..models import SubscriptionSource, ParsedServer

@register("custom_fetcher")
class ApiFetcher(BaseFetcher):
    """ApiFetcher fetches subscription data.

    Example:
        fetcher = ApiFetcher(source)
        data = fetcher.fetch()
    """
    def fetch(self, force_reload: bool = False) -> bytes:
        """Fetch subscription data.

        Args:
            force_reload (bool, optional): Force reload and ignore cache.

        Returns:
            bytes: Raw data.
        """
        raise NotImplementedError()
```

---

## Пример сгенерированного класса (postprocessor)
```python
from ..registry import register
from ..postprocessor_base import BasePostProcessor
from ..models import SubscriptionSource, ParsedServer

@register("custom_postprocessor")
class GeoFilterPostProcessor(BasePostProcessor):
    """GeoFilterPostProcessor post-processes parsed servers.

    Example:
        pp = GeoFilterPostProcessor()
        servers = pp.process(servers, context)
    """
    def process(self, servers, context):
        """Post-process parsed servers.

        Args:
            servers (list[ParsedServer]): List of servers.
            context (PipelineContext): Pipeline context.

        Returns:
            list[ParsedServer]: Processed servers.
        """
        raise NotImplementedError()
```

---

## Пример сгенерированного класса (parser)
```python
from ..registry import register
from ..base_parser import BaseParser
from ..models import SubscriptionSource, ParsedServer

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
```

---

## Пример сгенерированного класса (exporter)
```python
from ..registry import register
from ..base_exporter import BaseExporter
from ..models import SubscriptionSource, ParsedServer

@register("custom_exporter")
class ClashExporter(BaseExporter):
    """ClashExporter exports parsed servers to config.

    Example:
        exporter = ClashExporter()
        config = exporter.export(servers)
    """
    def export(self, servers):
        """Export parsed servers to config.

        Args:
            servers (list[ParsedServer]): List of servers.

        Returns:
            dict: Exported config.
        """
        raise NotImplementedError()
```

---

## Пример сгенерированного класса (validator)
```python
from ..validators.base import BaseValidator
from ..models import SubscriptionSource, ParsedServer

class GeoValidator(BaseValidator):
    """GeoValidator validates subscription data.

    Example:
        validator = GeoValidator()
        result = validator.validate(raw)
    """
    def validate(self, raw: bytes):
        """Validate subscription data.

        Args:
            raw (bytes): Raw data.

        Returns:
            ValidationResult: Result.
        """
        raise NotImplementedError()
```

---

## Best practices
- После генерации — зарегистрируйте плагин через `@register(...)` (если не добавлен автоматически).
- Проверьте docstring, добавьте edge-тесты.
- Для внешних плагинов используйте entry points (см. ADR-0002).
- Для автодокументации используйте шаблонные docstring и примеры.
- Не забывайте про unit-тесты: для каждого плагина генерируется тестовый файл.

---

## Расширение
- Для новых типов (exporter, postprocessor и др.) — расширяйте CLI-генератор по аналогии.
- Документируйте публичные методы и добавляйте примеры использования.
- Примеры и шаблоны можно найти в этой папке и в `src/sboxmgr/subscription/<type>s/`. 