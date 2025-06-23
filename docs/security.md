# Security Model

## Threats
- Path traversal (file:// fetcher)
- Инъекции (в конфиг, shell, параметры)
- Утечка секретов (логи, исключения)
- DoS на больших файлах/подписках
- Fail of one subscription source leads to DoS (pipeline aborts on single error)
- Uncaught edge cases in input/parameters may lead to crash or data leak
- Языковые модули: code injection, supply chain, log poisoning, DoS
- PipelineContext: утечка чувствительных данных через trace_id, metadata overflow, context manipulation
- Error Reporter: log injection через error messages, memory exhaustion через error accumulation
- Validator плагины: несанкционированное выполнение кода, resource exhaustion, timeout bypass
- Middleware registry: регистрация вредоносных плагинов, interface spoofing, execution isolation bypass
- MiddlewareChain: регистрация вредоносных middleware, side effects, leakage через context, DoS через бесконечные цепочки, log injection через LoggingMiddleware, privilege escalation через HookMiddleware.
- EnrichMiddleware: утечка гео-данных, подмена/фальсификация enrichment, DoS через внешние lookup.
- TagFilterMiddleware: bypass фильтрации, некорректная фильтрация по user input.
- LoggingMiddleware: log poisoning, утечка чувствительных данных при debug_level>0.
- Кеширование подписок (SubscriptionManager, fetcher): in-memory only, ключи учитывают все параметры, force_reload, ошибки не кешируются — risks mitigated.
- DX/CLI-генератор плагинов: генерация вредоносных шаблонов, подмена шаблонов, supply chain через внешние плагины
- Автодокументация: инъекции через docstring, DoS через автогенерацию большого числа файлов, подмена автодокументации

## Mitigations
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
- Sandbox для middleware, аудит цепочки, ограничение глубины, redaction логов, валидация enrichment, контроль user input в фильтрах.
- Sandbox и контроль шаблонов для DX/CLI-генератора, review внешних плагинов, валидация автодокументации, ограничение автогенерации файлов.

## SEC Fallbacks by Pipeline Phase

### Fetcher
- Ошибка сети, oversize, некорректный URL: partial_success, логирование, пайплайн не падает.
- Нестандартные схемы (ftp://, data://): safe fallback или запрет.

### Parser
- Невалидный формат, вредоносный payload: partial_success, sanitization, пайплайн не падает.
- Инъекции, eval, неожиданные структуры: sanitization, error reporter, пайплайн не падает.

### Postprocessor
- Ошибка enrichment, внешний сервис: warning, partial_success, sandbox/таймаут (при появлении).

### Middleware
- Ошибка, некорректный input, unsafe hook: логирование, sandbox, пайплайн не падает.
- Циклическая цепочка: ограничение глубины, пайплайн не падает.

### Exporter
- Unsupported outbound, пустой config: warning+skip, partial config, пайплайн не падает.

See also: sec_checklist.md, docs/tests/edge_cases.md 