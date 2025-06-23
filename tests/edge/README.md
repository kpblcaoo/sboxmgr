# Edge Tests: Structure and Coverage

- В этой директории собраны edge-тесты для всех слоёв пайплайна (fetcher, parser, exporter, postprocessor, middleware, selector, i18n, DX/CLI).
- Каждый тест проверяет поведение на ошибочных, граничных и опасных входных данных.
- Для каждого слоя есть отдельный файл с edge-тестами (см. [docs/tests/edge_cases.md](../../docs/tests/edge_cases.md)).
- Критичные SEC edge-cases выделены отдельно (см. sec_checklist.md).
- Поведение пайплайна при ошибках: partial_success, fallback, логирование, пайплайн не падает.
- Если тест падает — это сигнал о потенциальной уязвимости или регрессии. 