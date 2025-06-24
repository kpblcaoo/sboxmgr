# Edge Cases: Subscription Pipeline

## Summary
- Покрыто тестами: ✔️
- Требует покрытия/реализации: ❗ (TODO)
- См. также: sec_checklist.md, tests/edge/

## Fetcher
- ✔️ Некорректный URL (протокол, опечатка, несуществующий домен) — tests/edge/test_fetcher_oversize.py
- ✔️ HTTP 404/500, timeouts, SSL error — tests/edge/test_fetcher_oversize.py
- ✔️ Ограничение размера (oversize, >2MB) — tests/edge/test_fetcher_oversize.py
- ✔️ file:// вне разрешённой директории — tests/edge/test_fetcher_oversize.py
- ✔️ User-Agent: пустой, нестандартный, fingerprinting — test_apifetcher.py
- ✔️ partial_success, логирование ошибки, не падает весь пайплайн — tests/edge/test_fetcher_oversize.py
- ✔️ Fetcher: нестандартные схемы (ftp://, data://, chrome-extension:// и др.) — SEC-FETCH-01: централизованный SEC-контур, тесты, safe fallback
- ❗ TODO: добавить негативные edge-тесты на нестандартные схемы (ftp, data, chrome-extension)

## Parser
- ✔️ Невалидный base64/JSON/YAML — tests/edge/test_parser_edge_cases.py
- ✔️ ss:// как base64 и как URI — tests/edge/test_parser_edge_cases.py
- ✔️ URI с query, emoji, комментариями — tests/edge/test_parser_edge_cases.py
- ✔️ Clash config: proxies в корне и в секции — tests/edge/test_parser_edge_cases.py
- ✔️ Tolerant JSON: комментарии, trailing comma, _comment — tests/edge/test_parser_edge_cases.py
- ✔️ partial_success, логирование ошибки, fallback, sanitization — tests/edge/test_parser_edge_cases.py
- ❗ TODO: вредоносный payload (инъекции, DoS, eval, неожиданные структуры)

## Exporter
- ✔️ Unsupported outbound type (skip, warning) — tests/edge/test_exporter_edge_cases.py
- ✔️ Отсутствие обязательных полей (address, port) — tests/edge/test_exporter_edge_cases.py
- ✔️ Генерация пустого/частичного конфига — tests/edge/test_exporter_edge_cases.py
- ✔️ warning+skip, partial config, не падает — tests/edge/test_exporter_edge_cases.py
- ❗ TODO: edge-cases для новых outbound-протоколов (WireGuard, tuic, hysteria и др.)

## Selector
- ✔️ Нет подходящих серверов (empty) — tests/edge/test_selector_edge_cases.py
- ✔️ Некорректный фильтр/tag — tests/edge/test_selector_edge_cases.py
- ✔️ empty result, warning, не падает — tests/edge/test_selector_edge_cases.py

## Postprocessor
- ✔️ Дубликаты, некорректные geo — tests/edge/test_geofilterpostprocessor.py
- ✔️ Ошибка enrichment — tests/edge/test_geofilterpostprocessor.py
- ✔️ partial_success, warning, не падает — tests/edge/test_geofilterpostprocessor.py
- ❗ TODO: внешний enrichment (sandbox, таймаут, edge-тесты при появлении)

## Middleware
- ✔️ Некорректный input (валидация) — tests/edge/test_parser_edge_cases.py::test_tagfilter_middleware_invalid_input
- ✔️ Ошибка внутри middleware — tests/edge/test_parser_edge_cases.py::test_middleware_with_error_accumulates
- ✔️ Порядок применения влияет на результат — tests/edge/test_parser_edge_cases.py::test_middleware_chain_order_tagfilter_vs_enrich
- ✔️ Циклическая цепочка — tests/edge/test_subscription_fail_tolerance.py
- ✔️ Timeout для enrichment — tests/edge/test_parser_edge_cases.py::test_enrichmiddleware_external_lookup_timeout
- ✔️ Sandbox для хуков — tests/edge/test_parser_edge_cases.py::test_hookmiddleware_privilege_escalation
- ✔️ логирование, ограничение глубины, не падает пайплайн — tests/edge/test_parser_edge_cases.py
- ❗ TODO: хуки/команды — расширить edge-тесты на sandbox-изоляцию, передачу переменных, обход

## i18n
- ✔️ Некорректный JSON, длинные строки, ANSI-escape, попытка вставить код — tests/edge/test_i18n_loader.py
- ✔️ Отсутствие файла, подмена файла — tests/edge/test_i18n_loader.py
- ✔️ fallback на английский, логирование, отсутствие краша — tests/edge/test_i18n_loader.py

## DX/CLI
- ✔️ Ошибка генерации шаблона (невалидное имя, конфликт) — test_cli_errors.py
- ✔️ Ошибка автотеста для нового плагина — test_typer_cli_general.py
- ✔️ user-friendly ошибка, не ломает пайплайн — test_cli_errors.py, test_typer_cli_general.py

# Критичные SEC edge-cases (TODO)
- ❗ Parser: вредоносный payload (инъекции, DoS, eval, неожиданные структуры)
- ❗ Fetcher: нестандартные схемы (ftp://, data://, chrome-extension:// и др.) — негативные edge-тесты
- ❗ Exporter: edge-cases для новых outbound-протоколов (WireGuard, tuic, hysteria и др.)
- ❗ Postprocessor: внешний enrichment (sandbox, таймаут, edge-тесты при появлении)
- ❗ Middleware: хуки/команды — sandbox-изоляция, обход

# См. также: sec_checklist.md, README.md, tests/edge/

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