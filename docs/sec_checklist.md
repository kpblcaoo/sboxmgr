# SEC Checklist

## Core Security Checklist
- [x] SEC-01: URL validation (source_url)  # Реализовано: валидация и логирование source_url, edge-тесты
- [ ] SEC-02: Root checks
- [x] SEC-03: Safe paths (file:// fetcher, inbounds SEC-валидация через pydantic: bind только на localhost/private, порты 1024-65535, edge-тесты)  # Реализовано: file:// fetcher ограничен рабочей директорией, логирование попыток
- [ ] SEC-04: Dry-run by default
- [ ] SEC-05: Backups before overwrite
- [x] SEC-06: Log redaction (source, servers)  # Реализовано: redaction в логах, debug_level, sanitization
- [ ] SEC-07: Write-access checks
- [ ] SEC-08: Atomic writes
- [ ] SEC-09: Env validation
- [ ] SEC-10: Shell input sanitization
- [x] SEC-11: Fail-tolerant subscriptions (partial_success, per-source error handling)  # Реализовано: partial_success, strict/tolerant, тесты
- [x] SEC-12: Безопасная архитектура языковых модулей (i18n)  # Реализовано: LanguageLoader, fallback, sanitization, тесты
- [x] SEC-13: Безопасная автоматизация i18n (sync_keys.py): path validation, diff logging, check-only mode, шаблоны только для review, тесты на edge-cases.  # Реализовано: sync_keys.py, pre-commit, тесты
- [x] SEC-14: PipelineContext безопасность: trace_id не содержит чувствительных данных, metadata sanitization, контроль размера context.  # Реализовано: PipelineContext, sanitization, тесты
- [x] SEC-15: Error Reporter безопасность: redaction чувствительных данных в ошибках, ограничение размера error stack, защита от log injection.  # Реализовано: ErrorReporter, sanitization, тесты
- [ ] SEC-16: Validator плагины: sandboxing, whitelist разрешенных валидаторов, ограничение ресурсов, timeout для валидации.
- [x] SEC-17: Middleware registry: защита от несанкционированной регистрации плагинов, валидация интерфейсов, изоляция выполнения.  # Реализовано: registry, тесты, edge-cases
- [x] SEC-FETCH-01: Проверка схем URL при инициализации fetcher (whitelist: http, https, file). [edge/test_fetcher_oversize.py]

## SEC-CODE: Code Quality Security Checklist (NEW - 2024-12-24, COMPLETED - 2025-06-24)
- [x] SEC-CODE-01: Рефакторинг критически сложных функций (F-E уровень) на меньшие компоненты для снижения security risks  # DONE: singbox_export F-53 → B-7
- [x] SEC-CODE-02: Устранение shell=True в subprocess вызовах, использование безопасных альтернатив  # VERIFIED: No shell=True usage found
- [x] SEC-CODE-03: Замена MD5 хеширования на SHA256 или более безопасные алгоритмы  # DONE: Earlier in branch
- [x] SEC-CODE-04: Добавление timeout для всех HTTP запросов (защита от DoS)  # DONE: Earlier in branch
- [x] SEC-CODE-05: Удаление неиспользуемых импортов и переменных (dead code может скрывать уязвимости)  # DONE: 3 items removed
- [ ] SEC-CODE-06: Устранение дублированного кода (единая точка патчинга уязвимостей)
- [ ] SEC-CODE-07: Замена try-except-pass на explicit error handling (предотвращение скрытых ошибок)
- [ ] SEC-CODE-08: Регулярный аудит кода инструментами (Vulture, Radon, Bandit, Safety)
- [x] SEC-CODE-09: Безопасные пути логирования - использование XDG Base Directory spec вместо /var/log  # DONE: ~/.local/share/sboxmgr/ с fallback

## SEC-LEGACY: Legacy Components Security (NEW - 2024-12-24)
- [x] SEC-LEGACY-01: Installation Wizard архивирован (устранена угроза subprocess vulnerabilities, privilege escalation)  # DONE: moved to archive/install_wizard_legacy
- [ ] SEC-LEGACY-02: Аудит и архивирование/рефакторинг других legacy компонентов с security рисками
- [ ] SEC-LEGACY-03: Документирование архивированных компонентов и причин их удаления

## SEC-MW: Middleware Security Checklist
- [x] SEC-MW-01: MiddlewareChain не допускает бесконечных/рекурсивных цепочек, глубина ограничена.  # Реализовано: ограничение глубины, тесты
- [x] SEC-MW-02: Middleware registry: sandbox/audit при регистрации, строгая валидация интерфейса. [middleware_base.py, worklog]
- [x] SEC-MW-03: LoggingMiddleware не логирует чувствительные данные, redaction при debug_level>0.  # Реализовано: redaction, debug_level
- [x] SEC-MW-04: EnrichMiddleware — запрет внешних lookup без таймаута/валидации. [edge/test_parser_edge_cases.py]
- [x] SEC-MW-05: TagFilterMiddleware — фильтрация только по whitelisted критериям, строгая валидация user input. [middleware_base.py, edge/test_parser_edge_cases.py]
- [x] SEC-MW-06: HookMiddleware — sandbox, запрет эскалации привилегий. [edge/test_parser_edge_cases.py]
- [x] SEC-MW-07: Все middleware валидируют вход/выход, не допускают side effects в context.  # Реализовано: валидация, тесты
- [x] SEC-MW-08: Аудит и логирование регистрации/исполнения middleware.  # Реализовано: логирование, тесты

_Last updated: 2025-06-24. See ADR-0001, ADR-0004, ADR-0005, ADR-0007. See also docs/tests/edge_cases.md._

## SEC Checklist (актуально на 2025-06-24)
- [x] SEC-PARSER-01: sanitize/validate_parsed_data, edge-тесты, документация. [edge/test_parser_edge_cases.py, worklog]
- [x] Fail-tolerance: partial_success, ошибки одной подписки не валят весь пайплайн. [edge/test_subscription_fail_tolerance.py]
- [x] i18n: sync_keys.py, pre-commit, edge-тесты, fallback, sanitization. [worklog]
- [x] Enrichment timeout: sandbox/таймаут для внешних enrichment. [edge/test_parser_edge_cases.py]
- [x] Все публичные методы и классы снабжены Google docstring. [ruff, worklog]
- [x] Installation Wizard удален (security risk eliminated). [refactor/cleanup branch]

**Ссылки на тесты и worklog:**
- tests/edge/
- plans/roadmap_v1.5.0/worklog.md
- archive/install_wizard_legacy/ (archived components)

## SEC-ROUTE: Routing Layer Security Checklist
- [ ] SEC-ROUTE-01: Валидация структуры user_routes/exclusions, запрет route-injection, edge-тесты (см. test_routing.py)
- [ ] SEC-ROUTE-02: Запрет success=True при пустом config после фильтрации маршрутов (user_routes, exclusions)
- [ ] SEC-ROUTE-03: Валидация уникальности tags/outbounds, защита от подмены через user input
- [ ] SEC-ROUTE-04: ErrorSeverity для ошибок маршрутизации, явное логирование конфликтов
- [ ] SEC-EXPORT-01: safe_path_check(path, basedir) для всех экспортеров, edge-тесты на path traversal и symlink
- [ ] SEC-PLUGIN-01: sandbox/audit-обёртки на register_*, тесты на подмену REGISTRY и side-effect
- [ ] SEC-ERROR-01: Ввести ErrorSeverity (fatal, recoverable, warning) в PipelineError, обновить обработку ошибок
- [ ] SEC-FINAL-01: Гарантировать вызов финальной валидации перед экспортом, даже при частичных ошибках
- [ ] SEC-I18N-01: Строгая проверка i18n-ключей, логирование ошибок локализации, запрет silent fallback
- [ ] SEC-META-01: Документировать модель fallbacks по фазам (какой слой может fallback'нуться, а какой обязан упасть)

## Priority Matrix (NEW - 2024-12-24, UPDATED - 2025-06-24)

### 🔴 Critical Priority (Security Impact: High) - COMPLETED ✅
- [x] SEC-CODE-01: Рефакторинг singbox_export (F-53 complexity)  # DONE
- [x] SEC-CODE-02: Устранение shell=True  # VERIFIED
- [x] SEC-CODE-03: Замена MD5 на SHA256  # DONE
- [x] SEC-CODE-04: HTTP timeout  # DONE

### 🟡 High Priority (Security Impact: Medium)
- [x] SEC-CODE-05: Dead code removal  # DONE
- [ ] SEC-CODE-06: Code deduplication
- [ ] SEC-ROUTE-01-04: Routing security
- [ ] SEC-ERROR-01: ErrorSeverity

### 🟢 Medium Priority (Security Impact: Low)
- SEC-CODE-07: Error handling improvement
- SEC-LEGACY-02: Legacy audit
- SEC-I18N-01: i18n validation 