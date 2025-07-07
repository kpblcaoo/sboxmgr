# ADR-0002: Plugin Registry System

_This ADR was written retrospectively to document a decision made earlier in the project._

## Context
Для поддержки расширяемости и сторонних плагинов (fetcher, parser, exporter и др.) требовалась универсальная система регистрации.

## Decision
- Реализован registry через декораторы (@register) и поддержку entry points (setuptools/pip).
- Registry позволяет динамически обнаруживать и подключать плагины без изменения ядра.

## Alternatives
- Жёсткая регистрация плагинов в коде — плохо расширяется, не поддерживает сторонние плагины.

## Consequences
+ Лёгкость расширения и поддержки
+ Возможность сторонних плагинов (pip install)
– Требует дисциплины в именовании и регистрации
