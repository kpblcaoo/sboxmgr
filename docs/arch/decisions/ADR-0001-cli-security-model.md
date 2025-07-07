# ADR-0001: CLI Security Model

_This ADR was written retrospectively to document a decision made earlier in the project._

## Context
Для CLI и подписочного пайплайна требовалась формализованная модель безопасности, чтобы минимизировать риски (инъекции, path traversal, утечка секретов, DoS и др.).

## Decision
- Введён SEC-чеклист (SEC-01...SEC-10) и threat model (см. docs/security.md, sec_checklist.md).
- Все новые точки входа и плагины проходят SEC-анализ.
- Чеклист дополняется по мере появления новых поверхностей атаки.

## Alternatives
- Не фиксировать SEC-стандарты явно — приводит к разрозненным мерам, сложно поддерживать и аудировать.

## Consequences
+ Прозрачность и зрелость архитектуры
+ Лёгкость аудита и развития
– Требует дисциплины при добавлении новых фич
