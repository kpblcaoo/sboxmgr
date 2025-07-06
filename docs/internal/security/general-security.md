# Security Model

## Threats

### Code Quality & Architecture Threats (NEW - 2025-06-25)
- **Critical Code Complexity**: функции с F-E сложностью (singbox_export F-53, run_installation_wizard E-37, prepare_selection E-33) создают риски необнаруженных багов, сложности аудита, maintenance overhead
- **Security Vulnerabilities**: shell=True в subprocess, MD5 хеширование, HTTP запросы без timeout
- **Dead Code**: неиспользуемые импорты и переменные могут скрывать уязвимости, создавать confusion при аудите
- **Code Duplication**: дублированная логика увеличивает attack surface, усложняет патчинг уязвимостей
- **Missing Error Handling**: try-except-pass блоки могут скрывать security-критичные ошибки

### Legacy & Deprecated Components
- ~~Installation Wizard: subprocess vulnerabilities, privilege escalation через sudo, path traversal~~ **ARCHIVED** - moved to archive/install_wizard_legacy

### Core Pipeline Threats
- Path traversal (file:// fetcher)
- Инъекции (в конфиг, shell, параметры)
- Утечка секретов (логи, исключения)
- DoS на больших файлах/подписках
- Fail of one subscription source leads to DoS (pipeline aborts on single error)
- Uncaught edge cases in input/parameters may lead to crash or data leak

### Component-Specific Threats
- Языковые модули: code injection, supply chain, log poisoning, DoS
- PipelineContext: утечка чувствительных данных через trace_id, metadata overflow, context manipulation
- Error Reporter: log injection через error messages, memory exhaustion через error accumulation
- Validator плагины: несанкционированное выполнение кода, resource exhaustion, timeout bypass
- Middleware registry: регистрация вредоносных плагинов, interface spoofing, execution isolation bypass
- MiddlewareChain: регистрация вредоносных middleware, side effects, leakage через context, DoS через бесконечные цепочки, log injection через LoggingMiddleware, privilege escalation через HookMiddleware
- EnrichMiddleware: утечка гео-данных, подмена/фальсификация enrichment, DoS через внешние lookup
- TagFilterMiddleware: bypass фильтрации, некорректная фильтрация по user input
- LoggingMiddleware: log poisoning, утечка чувствительных данных при debug_level>0
- Кеширование подписок (SubscriptionManager, fetcher): in-memory only, ключи учитывают все параметры, force_reload, ошибки не кешируются — risks mitigated
- DX/CLI-генератор плагинов: генерация вредоносных шаблонов, подмена шаблонов, supply chain через внешние плагины
- Автодокументация: инъекции через docstring, DoS через автогенерацию большого числа файлов, подмена автодокументации

## Mitigations

### Code Quality Mitigations (NEW)
- **Complexity Reduction**: рефакторинг критически сложных функций на меньшие компоненты
- **Security Hardening**: замена MD5 на SHA256, добавление timeout для HTTP, устранение shell=True
- **Dead Code Removal**: удаление неиспользуемых импортов и переменных
- **Deduplication**: вынос дублированной логики в утилитарные функции
- **Error Handling**: замена try-except-pass на explicit error handling

### Legacy Component Mitigations
- **Wizard Removal**: архивирован legacy installation wizard (security risk eliminated)

### Core Mitigations
- Валидация путей и размеров
- Логирование только безопасных данных
- Исключения без чувствительных данных
- Чеклист SEC-01...SEC-17 (см. sec_checklist.md)
- Fail-tolerant pipeline: errors in one source do not affect others
- Edge case coverage: categorized, tested, and documented (see edge_cases.md)
- Только декларативные форматы, строгая валидация, sanitization, fallback, whitelisted пути (i18n)
- PipelineContext: sanitization metadata, контроль размера, генерация безопасных trace_id
- Error Reporter: redaction чувствительных данных, ограничение размера error stack, защита от injection
- Validator плагины: sandboxing, whitelist, resource limits, timeout enforcement
- Middleware registry: контроль регистрации, валидация интерфейсов, изоляция выполнения
- Sandbox для middleware, аудит цепочки, ограничение глубины, redaction логов, валидация enrichment, контроль user input в фильтрах
- Sandbox и контроль шаблонов для DX/CLI-генератора, review внешних плагинов, валидация автодокументации, ограничение автогенерации файлов
- SEC-PARSER-01: реализована многоуровневая валидация и sanitization данных после парсинга, edge-тесты, fail-tolerant pipeline, документация и чеклист (см. sec_checklist.md, tests/edge/test_parser_edge_cases.py)

## SEC Fallbacks by Pipeline Phase

### Fetcher
- Ошибка сети, oversize, некорректный URL: partial_success, логирование, пайплайн не падает
- Нестандартные схемы (ftp://, data://): safe fallback или запрет
- **HTTP Timeout**: все HTTP запросы должны иметь timeout (NEW)

### Parser
- Невалидный формат, вредоносный payload: partial_success, sanitization, пайплайн не падает
- Инъекции, eval, неожиданные структуры: sanitization, error reporter, пайплайн не падает
- **Complex Function Isolation**: критически сложные функции изолированы и протестированы (NEW)

### Postprocessor
- Ошибка enrichment, внешний сервис: warning, partial_success, sandbox/таймаут (при появлении)

### Middleware
- Ошибка, некорректный input, unsafe hook: логирование, sandbox, пайплайн не падает
- Циклическая цепочка: ограничение глубины, пайплайн не падает

### Exporter
- Unsupported outbound, пустой config: warning+skip, partial config, пайплайн не падает

See also: sec_checklist.md, docs/tests/edge_cases.md

## SEC-контуры и угрозы по фазам пайплайна (актуализация 2025-06-25)

| Фаза             | Основные угрозы/риски | Реализовано | Упущения/рекомендации |
|------------------|----------------------|-------------|-----------------------|
| **Code Quality** | Критическая сложность, security bugs, dead code | Анализ инструментами (Vulture, Radon, Bandit) | Рефакторинг F-E функций, security fixes |
| Fetch            | Невалидированные схемы, path traversal, обход check_url, HTTP без timeout | Валидация схем, ограничение file:// | HTTP timeout, edge-cases (symlink, вложенные file://) |
| Parser           | Side-effects (eval, exec, вложенные base64), proto pollution | Edge-тесты, sanitization | Не все типы вложенности и инъекций покрыты, нет ErrorSeverity |
| Parsed Validator | Silent fallback, success=True при пустом config, неявные ошибки | SEC-PARSER-01: многоуровневая валидация, фильтрация, edge-тесты, fail-tolerant pipeline | Нет ErrorSeverity, не все ошибки фатальны |
| Middleware       | Нет sandbox/изоляции для всех хуков, raise без обработки | Sandbox, audit, ограничение глубины | Нет строгой изоляции для пользовательских middleware |
| Exporter         | Path traversal, запись вне allowed basedir, symlink-атаки | Ограничение file://, edge-тесты | Нет safe_path_check, нет edge-тестов на path traversal |
| Final Validation | Не всегда вызывается, если был fatal error | Частично | Нет единого слоя для финальной проверки |
| Routing Layer    | Конфликты user_routes/exclusions, route-injection, некорректная структура | Плагинная архитектура, edge-тесты | Нет строгой схемы user_routes, нет ErrorSeverity, нет финальной валидации маршрутов |
| i18n             | Ошибки локализации, silent fallback | sync_keys.py, edge-тесты | Нет строгой проверки ключей, silent fallback без логов |
| Plugin Registry  | Подмена REGISTRY, side-effect, нет sandbox | Registry, edge-тесты | Нет audit-обёртки, нет ограничений на параметры |
| Error Handling   | Все ошибки равны, нет деления по значимости | ErrorReporter, redaction | Нет ErrorSeverity, нет категоризации |

### Code Quality Security Recommendations (NEW)
- **Приоритет 1**: Рефакторинг singbox_export (F-53) - критическая сложность создает security risks
- **Приоритет 2**: Устранение security vulnerabilities (shell=True, MD5, HTTP timeout)
- **Приоритет 3**: Удаление dead code и дублирования
- **Приоритет 4**: Улучшение error handling (замена try-except-pass)

### Routing Layer: SEC-контуры и рекомендации
- Ввести строгую валидацию структуры user_routes/exclusions
- Запретить success=True при пустом config после фильтрации маршрутов
- Ввести ErrorSeverity для ошибок маршрутизации
- Edge-тесты на route-injection, path traversal, конфликт exclusions/user_routes
- Финальная валидация маршрутов перед экспортом (уникальность tags, корректность outbounds)

### Новые/уточнённые угрозы (см. чеклист)
- Silent fallback на всех фазах
- Нет sandbox/audit-обёртки на register_*
- Нет safe_path_check для экспортеров
- Нет ErrorSeverity в PipelineError
- Нет строгой проверки i18n-ключей
- Нет финальной валидации маршрутов
- **Code complexity as security risk** (NEW)
- **Dead code hiding vulnerabilities** (NEW)
- **Duplicated security logic** (NEW)
