# Edge Cases: Subscription Pipeline

## Summary
- Покрыто тестами: [x]
- Требует покрытия/реализации: [ ] (TODO)
- См. также: sec_checklist.md, tests/edge/

## Fetcher
- [x] Некорректный URL (протокол, опечатка, несуществующий домен) — tests/edge/test_fetcher_oversize.py
- [x] HTTP 404/500, timeouts, SSL error — tests/edge/test_fetcher_oversize.py
- [x] Ограничение размера (oversize, >2MB) — tests/edge/test_fetcher_oversize.py
- [x] file:// вне разрешённой директории — tests/edge/test_fetcher_oversize.py
- [x] User-Agent: пустой, нестандартный, fingerprinting — test_apifetcher.py
- [x] Ожидание: partial_success, логирование ошибки, не падает весь пайплайн — tests/edge/test_fetcher_oversize.py
- [x] Fetcher: нестандартные схемы (ftp://, data://, chrome-extension:// и др.) — SEC-FETCH-01: централизованный SEC-контур, тесты, safe fallback

## Parser
- [x] Невалидный base64/JSON/YAML — tests/edge/test_parser_edge_cases.py
- [x] ss:// как base64 и как URI — tests/edge/test_parser_edge_cases.py
- [x] URI с query, emoji, комментариями — tests/edge/test_parser_edge_cases.py
- [x] Clash config: proxies в корне и в секции — tests/edge/test_parser_edge_cases.py
- [x] Tolerant JSON: комментарии, trailing comma, _comment — tests/edge/test_parser_edge_cases.py
- [x] Ожидание: partial_success, логирование ошибки, fallback, sanitization — tests/edge/test_parser_edge_cases.py
- [ ] Вредоносный payload (TODO)

## Exporter
- [x] Unsupported outbound type (skip, warning) — tests/edge/test_exporter_edge_cases.py
- [x] Отсутствие обязательных полей (address, port) — tests/edge/test_exporter_edge_cases.py
- [x] Генерация пустого/частичного конфига — tests/edge/test_exporter_edge_cases.py
- [x] Ожидание: warning+skip, partial config, не падает — tests/edge/test_exporter_edge_cases.py

## Selector
- [x] Нет подходящих серверов (empty) — tests/edge/test_selector_edge_cases.py
- [x] Некорректный фильтр/tag — tests/edge/test_selector_edge_cases.py
- [x] Ожидание: empty result, warning, не падает — tests/edge/test_selector_edge_cases.py

## Postprocessor
- [x] Дубликаты, некорректные geo — tests/edge/test_geofilterpostprocessor.py
- [x] Ошибка enrichment — tests/edge/test_geofilterpostprocessor.py
- [x] Ожидание: partial_success, warning, не падает — tests/edge/test_geofilterpostprocessor.py

## Middleware
- [x] Некорректный input (валидация) — tests/edge/test_parser_edge_cases.py::test_tagfilter_middleware_invalid_input
- [x] Ошибка внутри middleware — tests/edge/test_parser_edge_cases.py::test_middleware_with_error_accumulates
- [x] Порядок применения влияет на результат — tests/edge/test_parser_edge_cases.py::test_middleware_chain_order_tagfilter_vs_enrich
- [x] Циклическая цепочка — tests/edge/test_subscription_fail_tolerance.py
- [x] Timeout для enrichment — tests/edge/test_parser_edge_cases.py::test_enrichmiddleware_external_lookup_timeout
- [x] Sandbox для хуков — tests/edge/test_parser_edge_cases.py::test_hookmiddleware_privilege_escalation
- [x] Ожидание: логирование, ограничение глубины, не падает пайплайн — tests/edge/test_parser_edge_cases.py

## i18n
- [x] Некорректный JSON, длинные строки, ANSI-escape, попытка вставить код — tests/edge/test_i18n_loader.py
- [x] Отсутствие файла, подмена файла — tests/edge/test_i18n_loader.py
- [x] Ожидание: fallback на английский, логирование, отсутствие краша — tests/edge/test_i18n_loader.py

## DX/CLI
- [x] Ошибка генерации шаблона (невалидное имя, конфликт) — test_cli_errors.py
- [x] Ошибка автотеста для нового плагина — test_typer_cli_general.py
- [x] Ожидание: user-friendly ошибка, не ломает пайплайн — test_cli_errors.py, test_typer_cli_general.py

# TODO
- [ ] Parser: вредоносный payload (инъекции, DoS, eval, неожиданные структуры)
- [ ] Fetcher: нестандартные схемы (ftp://, data://, chrome-extension:// и др.)
- [ ] Exporter: edge-cases для новых outbound-протоколов (WireGuard, tuic, hysteria и др.)
- [ ] Postprocessor: внешний enrichment (sandbox, таймаут, edge-тесты при появлении)
- [ ] Middleware: хуки/команды — расширить edge-тесты на sandbox-изоляцию, передачу переменных, обход

# См. также: sec_checklist.md, README.md, tests/edge/

# ... existing code ...
- [ ] Языковые модули: некорректный JSON, слишком длинные строки, ANSI-escape, попытка вставить код, отсутствие файла, подмена файла. Ожидаемое поведение: fallback на английский, логирование, отсутствие краша.
# ... existing code ...

## Critical SEC edge cases
- [ ] Parser: вредоносный payload (инъекции, DoS, eval, неожиданные структуры)
- [ ] Fetcher: нестандартные схемы (ftp://, data://, chrome-extension:// и др.)
- [ ] Middleware: unsafe hook/external command (sandbox, privilege escalation)
- [ ] Postprocessor: внешний enrichment без таймаута/валидации

## TODO (дополнительно)
- [ ] Parser: вредоносный payload (DoS, инъекции, eval, неожиданные структуры)
- [ ] Fetcher: ftp://, data://, chrome-extension:// — добавить негативные edge-тесты, safe fallback/запрет
- [ ] Exporter: edge-cases для новых outbound-протоколов (WireGuard, tuic, hysteria и др.)
- [ ] Postprocessor: внешний enrichment (sandbox, таймаут, edge-тесты при появлении)
- [ ] Middleware: хуки/команды — расширить edge-тесты на sandbox-изоляцию, передачу переменных, обход

## Новое поведение
- Unsupported scheme (ftp, data, chrome-extension): безопасный отказ, лог, partial success (см. SEC-FETCH-01) 