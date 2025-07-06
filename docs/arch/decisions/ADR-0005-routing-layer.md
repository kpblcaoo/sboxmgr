# ADR-0005: Extensible Routing Layer

## Context
Требуется поддержка пользовательских и расширяемых правил маршрутизации (по тегам, geo, exclusions, user-routes и т.д.) для генерации sing-box config. Важно обеспечить forward-совместимость и возможность расширения без переписывания ExportManager.

## Decision
- Вынести генерацию маршрутов в отдельный RoutingPlugin (BaseRoutingPlugin, DefaultRouter).
- В интерфейс BaseRoutingPlugin добавить параметр context: dict, обязательно с ключом mode ("default" | "geo" | ...).
- В ExportManager вызывать routing_plugin после фильтрации servers/exclusions, до сериализации.
- Fallback реализовать только через плагин (DefaultRouter).
- Добавить минимальные тесты, включая фиктивный TestRouter для проверки передачи всех параметров.

## Alternatives
- Жёстко реализовать генерацию маршрутов в ExportManager (монолит) — плохо расширяется, сложно тестировать.
- Использовать только статические шаблоны — не поддерживает динамические сценарии.

## Consequences
+ Легко расширять новыми плагинами (geo, tag, UI и т.д.)
+ Forward-совместимость через context
+ Простота тестирования (можно мокать плагины)
– Чуть выше порог входа для новых разработчиков
