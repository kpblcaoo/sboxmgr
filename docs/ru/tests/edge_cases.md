# Граничные случаи: Пайплайн подписок

## Сводка
- Покрыто тестами: ✔️
- Требует покрытия/реализации: ❗ (TODO)
- См. также: sec_checklist.md, tests/edge/

## Fetcher
- ✔️ Невалидный URL (протокол, опечатка, несуществующий домен) — tests/edge/test_fetcher_oversize.py
- ✔️ HTTP 404/500, таймауты, SSL ошибки — tests/edge/test_fetcher_oversize.py
- ✔️ Лимит размера (превышение, >2MB) — tests/edge/test_fetcher_oversize.py
- ✔️ file:// вне разрешенной директории — tests/edge/test_fetcher_oversize.py
- ✔️ User-Agent: пустой, нестандартный, fingerprinting — test_apifetcher.py
- ✔️ partial_success, логирование ошибок, пайплайн не падает — tests/edge/test_fetcher_oversize.py
- ✔️ Fetcher: нестандартные схемы (ftp://, data://, chrome-extension://, etc.) — SEC-FETCH-01: централизованный SEC контроль, тесты, безопасный fallback
- ❗ TODO: добавить негативные edge-тесты для нестандартных схем (ftp, data, chrome-extension)

## Parser
- ✔️ Невалидный base64/JSON/YAML — tests/edge/test_parser_edge_cases.py
- ✔️ ss:// как base64 и как URI — tests/edge/test_parser_edge_cases.py
- ✔️ URI с query, emoji, комментариями — tests/edge/test_parser_edge_cases.py
- ✔️ Clash config: proxies в корне и в секции — tests/edge/test_parser_edge_cases.py
- ✔️ Tolerant JSON: комментарии, trailing comma, _comment — tests/edge/test_parser_edge_cases.py
- ✔️ partial_success, логирование ошибок, fallback, sanitization — tests/edge/test_parser_edge_cases.py
- ❗ TODO: злонамеренная нагрузка (инъекции, DoS, eval, неожиданные структуры)

## Exporter
- ✔️ Неподдерживаемый outbound тип (skip, warning) — tests/edge/test_exporter_edge_cases.py
- ✔️ Отсутствие обязательных полей (address, port) — tests/edge/test_exporter_edge_cases.py
- ✔️ Генерация пустого/частичного конфига — tests/edge/test_exporter_edge_cases.py
- ✔️ warning+skip, partial config, пайплайн не падает — tests/edge/test_exporter_edge_cases.py
- ❗ TODO: edge-cases для новых outbound-протоколов (WireGuard, tuic, hysteria, etc.)

## Selector
- ✔️ Нет подходящих серверов (пустой) — tests/edge/test_selector_edge_cases.py
- ✔️ Невалидный фильтр/тег — tests/edge/test_selector_edge_cases.py
- ✔️ пустой результат, warning, пайплайн не падает — tests/edge/test_selector_edge_cases.py

## Postprocessor
- ✔️ Дубликаты, невалидная гео — tests/edge/test_geofilterpostprocessor.py
- ✔️ Ошибка обогащения — tests/edge/test_geofilterpostprocessor.py
- ✔️ partial_success, warning, пайплайн не падает — tests/edge/test_geofilterpostprocessor.py
- ❗ TODO: внешнее обогащение (sandbox, таймаут, edge-тесты когда доступны)

## Middleware
- ✔️ Невалидный ввод (валидация) — tests/edge/test_parser_edge_cases.py::test_tagfilter_middleware_invalid_input
- ✔️ Ошибка внутри middleware — tests/edge/test_parser_edge_cases.py::test_middleware_with_error_accumulates
- ✔️ Порядок применения влияет на результат — tests/edge/test_parser_edge_cases.py::test_middleware_chain_order_tagfilter_vs_enrich
- ✔️ Циклическая цепочка — tests/edge/test_subscription_fail_tolerance.py
- ✔️ Таймаут для обогащения — tests/edge/test_parser_edge_cases.py::test_enrichmiddleware_external_lookup_timeout
- ✔️ Sandbox для hooks — tests/edge/test_parser_edge_cases.py::test_hookmiddleware_privilege_escalation
- ✔️ логирование, лимит глубины, пайплайн не падает — tests/edge/test_parser_edge_cases.py
- ❗ TODO: hooks/команды — расширить edge-тесты для sandbox изоляции, передачи переменных, bypass

## i18n
- ✔️ Невалидный JSON, длинные строки, ANSI-escape, попытка инъекции кода — tests/edge/test_i18n_loader.py
- ✔️ Отсутствующий файл, замена файла — tests/edge/test_i18n_loader.py
- ✔️ fallback на английский, логирование, не падает — tests/edge/test_i18n_loader.py

## DX/CLI
- ✔️ Ошибка генерации шаблона (невалидное имя, конфликт) — test_cli_errors.py
- ✔️ Ошибка автотеста для нового плагина — test_typer_cli_general.py
- ✔️ user-friendly ошибка, пайплайн не падает — test_cli_errors.py, test_typer_cli_general.py

# Критические SEC edge cases (TODO)
- ❗ Parser: злонамеренная нагрузка (инъекции, DoS, eval, неожиданные структуры)
- ❗ Fetcher: нестандартные схемы (ftp://, data://, chrome-extension://, etc.) — негативные edge-тесты
- ❗ Exporter: edge-cases для новых outbound-протоколов (WireGuard, tuic, hysteria, etc.)
- ❗ Postprocessor: внешнее обогащение (sandbox, таймаут, edge-тесты когда доступны)
- ❗ Middleware: hooks/команды — sandbox изоляция, bypass

# См. также: sec_checklist.md, README.md, tests/edge/

## Критические SEC edge cases
- [ ] Parser: злонамеренная нагрузка (инъекции, DoS, eval, неожиданные структуры)
- [ ] Fetcher: нестандартные схемы (ftp://, data://, chrome-extension://, etc.)
- [ ] Middleware: небезопасный hook/внешняя команда (sandbox, эскалация привилегий)
- [ ] Postprocessor: внешнее обогащение без таймаута/валидации

## TODO (дополнительно)
- [ ] Parser: злонамеренная нагрузка (DoS, инъекции, eval, неожиданные структуры)
- [ ] Fetcher: ftp://, data://, chrome-extension:// — добавить негативные edge-тесты, безопасный fallback/ban
- [ ] Exporter: edge-cases для новых outbound-протоколов (WireGuard, tuic, hysteria, etc.)
- [ ] Postprocessor: внешнее обогащение (sandbox, таймаут, edge-тесты когда доступны)
- [ ] Middleware: hooks/команды — расширить edge-тесты для sandbox изоляции, передачи переменных, bypass

## Новое поведение
- Неподдерживаемая схема (ftp, data, chrome-extension): безопасный fail, логирование, partial success (см. SEC-FETCH-01)
