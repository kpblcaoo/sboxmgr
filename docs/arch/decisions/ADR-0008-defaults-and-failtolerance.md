# ADR-0008: Defaults and Fail-Tolerance in Subscription Pipeline

**Status:** Proposed  
**Date:** 2025-06-XX

## Context

В подписочном пайплайне поддерживаются различные форматы и протоколы, а также множество внешних сервисов. Для обеспечения безопасности, предсказуемости и fail-tolerance требуется явно зафиксировать ключевые дефолты и ограничения.

## Решения

1. **Default User-Agent**
   - По умолчанию используется User-Agent: `ClashMeta/1.0`.
   - Мотивация: максимальная совместимость с современными подписочными сервисами, минимизация fingerprinting.
   - Переопределяется через CLI (`--user-agent`), config.toml или переменную окружения.

2. **Ограничение на размер входных данных**
   - Максимальный размер подписки: **2 MB** (по умолчанию).
   - Лимит можно задать через переменную окружения `SBOXMGR_FETCH_SIZE_LIMIT` (в байтах) и/или в `config.toml`.
   - Мотивация: защита от DoS, переполнения памяти, случайных/злонамеренных больших файлов.
   - При превышении лимита — Warning + skip, пайплайн не падает.

3. **Fail-tolerance для unsupported outbound types**
   - Если встречается ParsedServer.type, не поддерживаемый экспортером, генерируется Warning и skip.
   - Пайплайн продолжает обработку остальных серверов.
   - Мотивация: не ломать генерацию конфига из-за одной неподдерживаемой записи, обеспечить плавный rollout новых фич.

4. **config.toml как основной источник дефолтов**
   - Все ключевые параметры (язык, лимиты, User-Agent, agent thresholds и др.) должны поддерживаться через config.toml.
   - Переменные окружения и CLI имеют приоритет над config.toml.

## Влияние на архитектуру

- Все дефолты и ограничения должны быть отражены в SEC checklist, CLI help, README и .env.example.
- Unit-тесты должны покрывать fail-tolerance (partial config, skip oversize, skip unknown type).

## Ссылки
- [SEC checklist](../../sec_checklist.md)
- [roadmap_v1.5.0/subplans/subscription_pipeline.md](../../../plans/roadmap_v1.5.0/subplans/subscription_pipeline.md)
- [README.md](../../../README.md)

## SEC: Централизованный контроль схем URL (SEC-FETCH-01)
- Введён централизованный SEC-контур для fetcher'ов: SUPPORTED_SCHEMES, validate_url_scheme.
- Проверка схемы URL происходит при инициализации любого fetcher (BaseFetcher).
- Поддерживаются только http, https, file (whitelist).
- Для неподдерживаемых схем (ftp, data, chrome-extension и др.) выбрасывается ValueError("unsupported scheme: ...").
- Все edge-тесты для нестандартных схем теперь зелёные, обход невозможен.
- Решение масштабируется на все будущие fetcher-плагины.
- См. также: tests/edge/test_fetcher_oversize.py, sec_checklist.md (SEC-FETCH-01). 