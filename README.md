# update-singbox

[![Build Status](https://github.com/kpblcaoo/update-singbox/actions/workflows/ci-dev.yml/badge.svg)](https://github.com/kpblcaoo/update-singbox/actions)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen)](https://github.com/kpblcaoo/update-singbox/actions)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## Other languages / Другие языки
- [Русский (docs/ru/README.md)](docs/ru/README.md)

A Python CLI tool for automating and managing [sing-box](https://sing-box.sagernet.org/) proxy configurations. Fetches server lists from a URL, applies exclusions, generates configs, and supports advanced routing and testing.

---

## ✨ Features
- Fetch and apply proxy server configs from a URL
- Supported protocols: VLESS, Shadowsocks, VMess, Trojan, TUIC, Hysteria2
- Direct routing for Russian domains and geoip-ru, proxy for other traffic
- Logging, backup, exclusions, dry-run, and full CLI test coverage
- All paths and artifacts are configurable via environment variables
- Modular architecture, fully tested with pytest + Typer.CliRunner

## Архитектура подписочного пайплайна

Пайплайн построен по модульной архитектуре с поддержкой плагинов для fetcher, parser, exporter, selector, postprocessor, middleware. Все этапы покрыты fail-tolerance, кэшированием, i18n, edge-тестами и best practices.

```mermaid
flowchart TD
    A[Fetcher] --> B[Raw Validator]
    B --> C[Parser]
    C --> D[PostProcessorChain]
    D --> E[MiddlewareChain]
    E --> F[Selector]
    F --> G[Exporter]
    G --> H[Config Output]
    
    subgraph Context
      X[PipelineContext] 
    end
    X -.-> A
    X -.-> D
    X -.-> E
    X -.-> F
    X -.-> G
    
    subgraph ErrorHandling
      Y[Error Reporter]
    end
    Y -.-> A
    Y -.-> B
    Y -.-> C
    Y -.-> D
    Y -.-> E
    Y -.-> F
    Y -.-> G
    
    style X fill:#f9f,stroke:#333,stroke-width:2px
    style Y fill:#ff9,stroke:#333,stroke-width:2px
    
    classDef main fill:#bbf,stroke:#333,stroke-width:2px;
    class A,B,C,D,E,F,G,H main;
```

- **DX/CLI-генератор**: генерация шаблонов плагинов (fetcher, parser, exporter, postprocessor, validator) с автотестами и best practices.
- **i18n**: мультиязычность CLI, fallback, sanitization, автоматизация sync_keys.py, edge-тесты.
- **Middleware**: расширяемая цепочка middleware с edge-тестами, логированием, fail-tolerance.
- **Кэширование**: in-memory кэш для SubscriptionManager и fetcher, поддержка force_reload.
- **Fail-tolerance**: partial_success, strict/tolerant режимы, Error Reporter, покрытие edge-тестами.
- **Coverage**: покрытие >90%, отдельные edge-тесты для всех слоёв пайплайна.
- **Best practices**: модульная архитектура, docstring Google-style, автодокументация, SEC-чеклисты, DX-утилиты.
- **SEC-валидация inbounds**: все inbounds проходят валидацию через pydantic (V2): bind только на localhost/private, порты 1024-65535, внешний bind требует явного подтверждения, edge-тесты, пример профиля см. cli_security.md.

---

## 🚀 Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install .
cp .env.example .env  # Edit as needed
sboxctl run -u https://example.com/proxy-config.json --index 1
```

- See `.env.example` for all environment variables you can configure (paths, URLs, debug, etc).
- **Note:** By default, the config is written to `/etc/sing-box/config.json` (default for sing-box). If your sing-box installation uses a different path, set `SBOXMGR_CONFIG_FILE` accordingly in your `.env`.
- For development, see DEVELOPMENT.md.

---

## 🚀 Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install .
cp .env.example .env  # Edit as needed
```

Requirements: Python 3.10+, sing-box, requests[socks], python-dotenv

---

## ⚙️ Usage

All commands are available via the `sboxctl` CLI (Typer-based):

### Typical scenarios

- **Run with server selection by index:**
  ```bash
  sboxctl run -u https://example.com/proxy-config.json --index 1
  # Generates config.json for the selected server
  ```
- **Dry-run (simulate config generation, no file changes):**
  ```bash
  sboxctl dry-run -u https://example.com/proxy-config.json
  # Prints config to stdout, does not write files
  ```
- **List all available servers:**
  ```bash
  sboxctl list-servers -u https://example.com/proxy-config.json
  # Shows a table of all servers with indices and remarks
  ```
- **Add server to exclusions:**
  ```bash
  sboxctl exclusions -u https://example.com/proxy-config.json --add 1
  # Adds server with index 1 to exclusions.json
  ```
- **Remove server from exclusions:**
  ```bash
  sboxctl exclusions -u https://example.com/proxy-config.json --remove 1
  # Removes server with index 1 from exclusions.json
  ```
- **View current exclusions:**
  ```bash
  sboxctl exclusions --view
  # Prints the current exclusions list
  ```
- **Clear all exclusions:**
  ```bash
  sboxctl clear-exclusions
  # Empties exclusions.json
  ```

### Options
| Option                  | Description                                      |
|------------------------|--------------------------------------------------|
| `-u, --url <URL>`      | Proxy config URL (required)                      |
| `--index <n>`          | Select server by index                           |
| `--remarks <name>`     | Select server by remarks                         |
| `--dry-run`            | Simulate config generation, no file changes      |
| `--list-servers`       | List all available servers                       |
| `--exclusions`         | Manage exclusions (add/remove/list)              |
| `--clear-exclusions`   | Remove all exclusions                            |
| `-d, --debug <level>`  | Set log verbosity (0=min, 1=info, 2=debug)       |

---

## 🛠 CLI architecture

- The CLI is built with [Typer](https://typer.tiangolo.com/), providing modular commands and automatic help.
- Each scenario (run, dry-run, exclusions, list-servers, clear-exclusions) is implemented as a separate command in the `cli/` package.
- CLI wrappers are thin: they only orchestrate, all business logic is in core modules (see `core/`, `utils/`).
- All paths and artifacts (config, log, exclusions, etc.) are controlled via environment variables (see `.env.example`).
- To add or extend commands, create a new file in `cli/` and register it in the main Typer app.
- For development and contribution guidelines, see DEVELOPMENT.md.

## 🐞 Known bugs & limitations

- Server indices in `list-servers` may start from a non-zero value if the list is filtered. [Planned: re-index from 0]
- Removing exclusions by index or ID may not work as expected. Use `sboxctl clear-exclusions --yes` or edit `exclusions.json` as a workaround. [Planned: improve UX]
- See [TODO.md](./TODO.md) or [plans/struct_refactor_next_steps.md](./plans/struct_refactor_next_steps.md) for the full list of known issues and plans.

---

## 🧪 Testing

Run all tests:
```bash
pytest -v tests/
```

All CLI logic is covered by tests using Typer.CliRunner and pytest. Artifacts and paths are isolated via environment variables in tests.

---

## 🛠 Configuration & Environment

All paths are configurable via environment variables:

| Variable                        | Default Value                |
|---------------------------------|------------------------------|
| `SBOXMGR_CONFIG_FILE`           | ./config.json                |
| `SBOXMGR_TEMPLATE_FILE`         | ./config.template.json       |
| `SBOXMGR_LOG_FILE`              | ./sboxmgr.log                |
| `SBOXMGR_EXCLUSION_FILE`        | ./exclusions.json            |
| `SBOXMGR_SELECTED_CONFIG_FILE`  | ./selected_config.json       |
| `SBOXMGR_URL`                   | (no default, must be set)    |

You can use a `.env` file in the project root for local development.

---

## 🤝 Contributing

Contributions are welcome! Fork, make changes, and submit a Pull Request.

---

## 📜 License

This project is licensed under the terms of the MIT License. See the LICENSE file for details.

## Расширение: плагины и генератор шаблонов

Для быстрого старта новых fetcher, parser, exporter, postprocessor, validator используйте CLI-генератор шаблонов:

- Примеры команд, шаблонов и best practices см. в [docs/plugins/README.md](docs/plugins/README.md)
- Генератор: `sboxctl plugin-template <type> <ClassName> --output-dir ./src/sboxmgr/subscription/<type>s/`

Это ускоряет разработку, стандартизирует docstring и тесты, облегчает онбординг новых контрибьюторов.

## Edge-case coverage

- Все ключевые edge-cases пайплайна покрыты тестами (см. [docs/tests/edge_cases.md](docs/tests/edge_cases.md)).
- Для каждого слоя (fetch, parse, postprocess, middleware, export, i18n, DX/CLI) есть отдельные edge-тесты.
- Критичные SEC edge-cases:
  - Parser: вредоносный payload (инъекции, DoS, eval)
  - Fetcher: нестандартные схемы (ftp://, data://, chrome-extension://)
  - Middleware: unsafe hook/external command (sandbox, privilege escalation)
  - Postprocessor: внешний enrichment без таймаута/валидации
- Поведение пайплайна при ошибках: partial_success, fallback, логирование, пайплайн не падает.
- См. также: sec_checklist.md, tests/edge/README.md





