# Edge Cases: Subscription Pipeline

## Summary
- Covered by tests: ✔️
- Needs coverage/implementation: ❗ (TODO)
- See also: sec_checklist.md, tests/edge/

## Fetcher
- ✔️ Invalid URL (protocol, typo, non-existent domain) — tests/edge/test_fetcher_oversize.py
- ✔️ HTTP 404/500, timeouts, SSL error — tests/edge/test_fetcher_oversize.py
- ✔️ Size limit (oversize, >2MB) — tests/edge/test_fetcher_oversize.py
- ✔️ file:// outside allowed directory — tests/edge/test_fetcher_oversize.py
- ✔️ User-Agent: empty, non-standard, fingerprinting — test_apifetcher.py
- ✔️ partial_success, error logging, pipeline does not crash — tests/edge/test_fetcher_oversize.py
- ✔️ Fetcher: non-standard schemes (ftp://, data://, chrome-extension://, etc.) — SEC-FETCH-01: centralized SEC control, tests, safe fallback
- ❗ TODO: add negative edge tests for non-standard schemes (ftp, data, chrome-extension)

## Parser
- ✔️ Invalid base64/JSON/YAML — tests/edge/test_parser_edge_cases.py
- ✔️ ss:// as base64 and as URI — tests/edge/test_parser_edge_cases.py
- ✔️ URI with query, emoji, comments — tests/edge/test_parser_edge_cases.py
- ✔️ Clash config: proxies at root and in section — tests/edge/test_parser_edge_cases.py
- ✔️ Tolerant JSON: comments, trailing comma, _comment — tests/edge/test_parser_edge_cases.py
- ✔️ partial_success, error logging, fallback, sanitization — tests/edge/test_parser_edge_cases.py
- ❗ TODO: malicious payload (injections, DoS, eval, unexpected structures)

## Exporter
- ✔️ Unsupported outbound type (skip, warning) — tests/edge/test_exporter_edge_cases.py
- ✔️ Missing required fields (address, port) — tests/edge/test_exporter_edge_cases.py
- ✔️ Generation of empty/partial config — tests/edge/test_exporter_edge_cases.py
- ✔️ warning+skip, partial config, pipeline does not crash — tests/edge/test_exporter_edge_cases.py
- ❗ TODO: edge cases for new outbound protocols (WireGuard, tuic, hysteria, etc.)

## Selector
- ✔️ No suitable servers (empty) — tests/edge/test_selector_edge_cases.py
- ✔️ Invalid filter/tag — tests/edge/test_selector_edge_cases.py
- ✔️ empty result, warning, pipeline does not crash — tests/edge/test_selector_edge_cases.py

## Postprocessor
- ✔️ Duplicates, invalid geo — tests/edge/test_geofilterpostprocessor.py
- ✔️ Enrichment error — tests/edge/test_geofilterpostprocessor.py
- ✔️ partial_success, warning, pipeline does not crash — tests/edge/test_geofilterpostprocessor.py
- ❗ TODO: external enrichment (sandbox, timeout, edge tests when available)

## Middleware
- ✔️ Invalid input (validation) — tests/edge/test_parser_edge_cases.py::test_tagfilter_middleware_invalid_input
- ✔️ Error inside middleware — tests/edge/test_parser_edge_cases.py::test_middleware_with_error_accumulates
- ✔️ Order of application affects result — tests/edge/test_parser_edge_cases.py::test_middleware_chain_order_tagfilter_vs_enrich
- ✔️ Cyclic chain — tests/edge/test_subscription_fail_tolerance.py
- ✔️ Timeout for enrichment — tests/edge/test_parser_edge_cases.py::test_enrichmiddleware_external_lookup_timeout
- ✔️ Sandbox for hooks — tests/edge/test_parser_edge_cases.py::test_hookmiddleware_privilege_escalation
- ✔️ logging, depth limit, pipeline does not crash — tests/edge/test_parser_edge_cases.py
- ❗ TODO: hooks/commands — expand edge tests for sandbox isolation, variable passing, bypass

## i18n
- ✔️ Invalid JSON, long strings, ANSI-escape, code injection attempt — tests/edge/test_i18n_loader.py
- ✔️ Missing file, file replacement — tests/edge/test_i18n_loader.py
- ✔️ fallback to English, logging, no crash — tests/edge/test_i18n_loader.py

## DX/CLI
- ✔️ Template generation error (invalid name, conflict) — test_cli_errors.py
- ✔️ Autotest error for new plugin — test_typer_cli_general.py
- ✔️ user-friendly error, pipeline does not crash — test_cli_errors.py, test_typer_cli_general.py

# Critical SEC edge cases (TODO)
- ❗ Parser: malicious payload (injections, DoS, eval, unexpected structures)
- ❗ Fetcher: non-standard schemes (ftp://, data://, chrome-extension://, etc.) — negative edge tests
- ❗ Exporter: edge cases for new outbound protocols (WireGuard, tuic, hysteria, etc.)
- ❗ Postprocessor: external enrichment (sandbox, timeout, edge tests when available)
- ❗ Middleware: hooks/commands — sandbox isolation, bypass

# See also: sec_checklist.md, README.md, tests/edge/

## Critical SEC edge cases
- [ ] Parser: malicious payload (injections, DoS, eval, unexpected structures)
- [ ] Fetcher: non-standard schemes (ftp://, data://, chrome-extension://, etc.)
- [ ] Middleware: unsafe hook/external command (sandbox, privilege escalation)
- [ ] Postprocessor: external enrichment without timeout/validation

## TODO (additional)
- [ ] Parser: malicious payload (DoS, injections, eval, unexpected structures)
- [ ] Fetcher: ftp://, data://, chrome-extension:// — add negative edge tests, safe fallback/ban
- [ ] Exporter: edge cases for new outbound protocols (WireGuard, tuic, hysteria, etc.)
- [ ] Postprocessor: external enrichment (sandbox, timeout, edge tests when available)
- [ ] Middleware: hooks/commands — expand edge tests for sandbox isolation, variable passing, bypass

## New behavior
- Unsupported scheme (ftp, data, chrome-extension): safe fail, log, partial success (see SEC-FETCH-01) 