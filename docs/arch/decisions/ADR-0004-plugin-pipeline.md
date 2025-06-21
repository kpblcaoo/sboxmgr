# ADR-0004: Plugin-Based Subscription Pipeline

_This ADR was written retrospectively to document a decision made earlier in the project._

## Context
Нужно было обеспечить поддержку различных форматов подписок (base64, clash, URI, JSON). Ключевые требования: расширяемость, безопасность, простота интеграции с CLI/wizard.

## Decision
- Реализован SubscriptionManager с плагинной системой из 5 компонентов: Fetcher, Parser, PostProcessor, Selector, Exporter.

## Alternatives
- Монолитный разбор: невозможно расширять, сложно тестировать.
- Простая функция fetch_and_parse(): нарушает SRP, мешает изоляции SEC-валидаторов.

## Consequences
+ Можно расширять без изменения ядра
+ Простота тестирования и отладки
– Чуть выше порог входа 