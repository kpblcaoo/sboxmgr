# Test Plan: Subscription Pipeline & Routing Layer

## Coverage Goals
- >=90% coverage обязательно перед миграцией
- Edge-cases: смешанные схемы (ss:// как base64 и как URI), query-параметры, emoji, комментарии, сломанные строки
- Для Routing Layer: тесты на передачу context, exclusions, user_routes, режимов (mode)

## Rationale
Большинство подписок и сценариев маршрутизации в wild доступны в невалидном или нестандартном виде. Парсеры и роутеры обязаны быть fail-safe и forward-compatible. Тесты должны выявлять ошибки на сломанных строках, неожиданных параметрах, edge-cases. 