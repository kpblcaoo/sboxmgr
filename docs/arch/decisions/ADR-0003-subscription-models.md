# ADR-0003: Subscription Models & Normalization

_This ADR was written retrospectively to document a decision made earlier in the project._

## Context
Поддержка разных форматов подписок (base64, JSON, URI, clash и др.) требовала унифицированной модели для downstream-задач (SEC, selector, exporter).

## Decision
- Введены dataclass-модели: SubscriptionSource, ParsedServer (см. src/sboxmgr/subscription/models.py).
- Все плагины и менеджеры работают с этими моделями.

## Alternatives
- Использовать разрозненные структуры для каждого формата — усложняет тестирование и расширение.

## Consequences
+ Унификация и переиспользование моделей
+ Простота тестирования и расширения
– Требует дисциплины при добавлении новых форматов
