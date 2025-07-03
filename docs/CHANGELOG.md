# Changelog

## Other languages / Другие языки
- [Русский (ru/CHANGELOG.md)](ru/CHANGELOG.md)

# pre-mvp0.1.0 (2025-01-27)

## Added
- **Full Profile Architecture**: Complete profile system with Pydantic models (ADR-0017)
  - `sboxmgr profile apply/validate/explain/diff/list/switch` commands
  - FullProfile, SubscriptionProfile, FilterProfile, RoutingProfile models
  - ExportProfile, AgentProfile, UIProfile, LegacyProfile support
  - 8 new JSON schemas for profile validation
  - Example profiles in `examples/profiles/`
- **Policy & Security Framework**: Comprehensive security policy system (Phase 5)
  - EncryptionPolicy, ProtocolPolicy, AuthenticationPolicy
  - GeoTestPolicy, CountryPolicy, ASNPolicy
  - IntegrityPolicy, PermissionPolicy, LimitPolicy
  - Policy evaluation with detailed logging and metadata
- **Agent Cleanup**: Complete agent architecture refactoring (Phase 2-3)
  - Removed service management from agent (ADR-0015)
  - Agent-installer separation for clean architecture
  - Pydantic schema generation (ADR-0016)
- **Pydantic Migration**: Major type safety improvements (Phase 1)
  - Extensive type annotation improvements across codebase
  - Fixed critical type errors in CLI, parsers, and fetchers
  - Enhanced type safety for core modules and exporters
- **CLI Enhancements**: Improved user experience and functionality
  - Auto-detect subscription format in list-servers
  - Robust SingBoxParser with comprehensive format support
  - `--format` option for forced format detection
  - UX improvements: hide service outbounds, better User-Agent logging
- **Routing Improvements**: Enhanced DefaultRouter with fallback rules
  - Fixed dead code in DefaultRouter
  - Added fallback routing rule for remaining traffic
  - Comprehensive routing tests and validation

## Changed
- **Profile Management**: New unified configuration approach
  - Single JSON profile replaces multiple config files
  - Backward compatibility with existing CLI commands
  - Gradual migration path from legacy configuration
- **Security Validation**: Enhanced policy evaluation
  - Real-time policy evaluation with detailed reporting
  - Policy violations, warnings, and info tracking
  - Integration with subscription pipeline
- **Type System**: Improved type annotations and validation
  - Better error messages for type validation
  - Enhanced Pydantic model integration
  - Improved type safety across all modules

## Fixed
- **DefaultRouter**: Fixed dead code and improved fallback logic
  - Server tag computation now properly used in routing
  - Fallback rules handle edge cases correctly
  - All routing tests pass with proper rule generation
- **CLI UX**: Improved user experience issues
  - Service outbounds (urltest/auto) hidden from list-servers output
  - Better User-Agent logging (shows actual values instead of [default])
  - Enhanced error handling and validation
- **Test Stability**: Fixed integration test issues
  - Comprehensive test cleanup and config.json pollution prevention
  - Fixed CLI matrix tests for real data scenarios
  - Improved test isolation and reliability

## Technical Details
- **Architecture**: Full profile system with Pydantic validation
- **Backward Compatibility**: Existing workflows continue to work
- **Performance**: No significant impact on existing operations
- **Documentation**: Comprehensive ADR documentation (0017-0019)
- **Type Safety**: Significant improvements in type annotations
- **Policy System**: Comprehensive security evaluation framework
- **Test Coverage**: Enhanced integration and unit test coverage

## Migration Notes
- Existing CLI commands continue to work unchanged
- New profile system is optional and additive
- Gradual migration to profiles recommended for complex configurations
- Policy system provides enhanced security validation

---

# 1.5.0 (2025-07-01)

## Added
- **CLI Inbound Parameters**: Added comprehensive CLI parameters for inbound configuration in export command
  - `--inbound-types`: Specify inbound types (tun, socks, http, tproxy)
  - `--tun-address`, `--tun-mtu`, `--tun-stack`: TUN interface configuration
  - `--socks-port`, `--socks-listen`, `--socks-auth`: SOCKS proxy configuration
  - `--http-port`, `--http-listen`, `--http-auth`: HTTP proxy configuration
  - `--tproxy-port`, `--tproxy-listen`: TPROXY configuration
  - `--dns-mode`: DNS resolution mode (system, tunnel, off)
- **InboundBuilder Class**: Dynamic ClientProfile creation from CLI parameters
- **Enhanced Validation**: Port range validation, address validation, format validation
- **Improved UX**: No need to create JSON profiles manually for simple inbound configurations
- **Agent-Installer Separation**: ADR-0015 implementation for clean separation of concerns
- **Pydantic Schema Generation**: ADR-0016 implementation for automatic schema generation
- **Type Annotation Audit**: Complete type safety improvements across all modules
- **CLI Matrix Testing**: Comprehensive CLI behavior testing with real data
- **Event System**: Comprehensive event system for sboxmgr operations
- **Agent Bridge**: IPC protocol implementation for future sboxagent integration

## Changed
- **Export Command**: Enhanced with inbound parameter support while maintaining backward compatibility
- **SingBox Exporter**: Updated to use `listen_port` field instead of `port` for better compatibility
- **Test Coverage**: Added 41 new tests (25 unit + 16 integration) for inbound functionality
- **CLI Reorganization**: Complete CLI refactoring with new export command structure
- **DefaultRouter Implementation**: Enhanced routing with fallback rules and improved logic
- **Exclusion Management**: Robust error handling and file recovery mechanisms
- **Logging System**: Improved initialization and error handling
- **Configuration System**: Enhanced validation and error handling

## Fixed
- **Edge Case Tests**: Fixed compatibility issues with new inbound field names
- **Validation**: Proper error handling for invalid inbound types and parameters
- **Security**: Address validation prevents unsafe bind configurations
- **Critical Type Issues**: Resolved all type annotation errors across codebase
- **Dead Code Removal**: Eliminated unused code and improved code quality
- **Context Argument Bugs**: Fixed postprocessor chain context handling
- **Validation Bypass**: Resolved critical Pydantic validation bypass issues
- **CLI Error Handling**: Improved error messages and exception handling
- **Test Stability**: Fixed 23 test regressions after Event System integration

## Technical Details
- **Architecture**: Clean separation between CLI parameters and core logic
- **Backward Compatibility**: Existing JSON profiles continue to work
- **Performance**: No significant impact on export performance
- **Documentation**: Comprehensive examples and architecture documentation
- **Type Safety**: 100% type annotation coverage with mypy compliance
- **Event System**: Comprehensive event handling with middleware support
- **IPC Protocol**: Robust socket-based communication for agent integration
- **Test Infrastructure**: Comprehensive CLI matrix testing with real data

## Migration Notes
- Existing workflows continue to work unchanged
- New CLI parameters are optional and additive
- JSON profiles can be gradually migrated to CLI parameters

---

# 1.4.0 (2025-06-20)

## Added
- Full CLI refactor: migrated to Typer for modern, modular CLI.
- All CLI scenarios (run, dry-run, exclusions, list-servers, clear-exclusions) are now commands with unified interface.
- Centralized logging (utils/logging.py), atomic file write, and environment variable management (utils/env.py).
- .env.example added with all supported environment variables.
- Entry point: CLI available as `sboxctl` after install.
- CLI matrix tests: all scenarios covered, tolerant output matching.
- New onboarding and usage examples in documentation.

## Changed
- All business logic moved out of CLI wrappers into core modules.
- CLI wrappers are now thin orchestrators only.
- Directory structure reorganized: cli/, core/, utils/, tests/ follow best practices.
- All artifact paths (config, log, exclusions, etc.) are now controlled via environment variables.
- Dev dependencies separated in pyproject.toml (`pip install .[dev]`).
- Documentation (README, DEVELOPMENT, TESTING, ru/) fully updated and unified.

## Fixed
- All tests now isolated from .env and global environment.
- Edge-case bugs with exclusions, selected_config.json, and server return fixed.
- Improved error handling for invalid/empty URLs (always returns code 1).
- Deprecation warnings (datetime, etc.) resolved.

## Removed
- requirements.txt deleted; all dependencies now in pyproject.toml (PEP 621).
- All duplicate, dead, and legacy code removed.
- Old CLI flags and patterns deprecated.

## Breaking changes
- CLI fully migrated to Typer: old flags/commands may not work.
- requirements.txt removed; use only pyproject.toml.
- All artifact paths must be set via environment variables.
- CLI is now only available as `sboxctl` (entry point).

## Migration notes
- Copy `.env.example` to `.env` and adjust as needed.
- Use `pip install .[dev]` for development, `pip install .` for users.
- See updated README.md and usage examples for new CLI commands.

## Lessons learned
- Centralized logging and env management greatly improve maintainability and testability.
- Thin CLI wrappers and modular core logic speed up refactoring and testing.
- Full test isolation and CLI matrix ensure robust coverage.
- Documenting lessons and architecture helps future contributors.

## [1.3.1] — 2024-06-18

### Added
- Full automation of CLI testing: exclusions, clear-exclusions, idempotency, error handling, user-friendly messages, dry-run, selected_config.json, --list-servers, excluded selection.
- User-friendly error handling for invalid URLs, corrupted exclusions.json, and attempts to select an excluded server.
- Logging of key CLI actions and errors.

### Changed
- exclusions.json now stores only SHA256 hashes of IDs, with a human-readable name field for users.
- selected_config.json is not created or modified in --dry-run mode.
- Improved CLI output for repeated server exclusion (informative message instead of duplication).
- clear-exclusions now reliably deletes exclusions.json regardless of URL presence.

### Fixed
- Fixed idempotency of exclusions: repeated addition does not duplicate entries.
- Fixed handling of corrupted exclusions.json (user-friendly reset).
- Fixed handling of invalid URLs (error and return code 1).
- Fixed all bugs found by manual and automated CLI testing.

### Refactored
- Refactored project structure: code moved to src/, large modules decomposed, imports updated.
- Improved modularity and code readability, prepared for automated tests.

### Testing
- Entire CLI covered by automated tests (pytest), manual checklist fully automated.
- Test coverage — 100% for key CLI scenarios.

---

> Some experimental features (e.g., install wizard) are not yet officially documented and will be presented in future releases.

## [v1.3.0] - 2025-05-16

### Added:
- Installer script (`install_update_singbox.sh`) to install the script to `/usr/local/bin/`, set up a systemd service, and configure a timer.
- Dynamic exclusion of servers from routing rules by IP using `ip_cidr` in the configuration template.

### Changed:
- Updated `config.template.json` to include a placeholder for `$excluded_servers` in the `ip_cidr` field.
- Enhanced script logic to replace the placeholder with actual IPs to be routed directly.

### Fixed:
- Ensured that specified IPs are routed directly, bypassing the proxy.

### Closed Issues:
- Issue #2: Implemented installer and enhanced exclusion logic.

---

## [v1.2.1] - 2025-05-16

### Fixed:
- Improved output for `-e` and `-l` options to work without verbosity.
- Allowed `-e` to function without `-u` when viewing exclusions.
- Handled missing `-u` option gracefully to prevent exceptions.
- Included server tags in the exclusions list.
- Corrected display of server ports in the server listing.
- Filtered out non-supported outbound types from the server list.
- Ensured server index numbers start at 0 and match the `-i` index.

---

## [v1.2.0] - 2025-05-15

### Added:
- Server exclusion and management features.
- Option to list servers with indices and details using `-l`.
- Ability to exclude servers by index or name with `-e`.
- Persistent storage for exclusions in `exclusions.json`.
- Option to view current exclusions.
- Option to clear all current exclusions with `--clear-exclusions`.

### Changed:
- Updated `list_servers` function to filter out inbounds and only list outbounds.
- Ensured configuration generation is triggered after server exclusions.

### Fixed:
- Corrected the display of server names and ports in the server listing.

### Known Issues:
 - -e and -l options produce no output unless verbosity is set (-d 1 or higher).
 - -e without an index should work even without -u <url>, but currently doesn't.
 - Server tags are not included in the exclusions list.
 - Server ports still display as N/A in some cases.
 - Non-supported outbound types appear in the server list.
 - Server index numbers do not start at 0 and may not match the -i index used for exclusion.

---

## [v1.1.0] - 2025-05-14

### Added:
- Automatic server selection using `urltest` for latency-based routing.
- Rule actions in `route` section for DNS (`dns-out`) and private IP routing, replacing deprecated `block` and `dns` outbounds.

### Changed:
- Removed deprecated `block` and `dns` outbounds per `sing-box` 1.11.0 migration guide.
- Updated `config.template.json` to remove unsupported `default` field in `urltest` outbound.
- Fixed tests in `test_protocol_validation.py` and `test_config_generate.py` to align with current implementation.
- Updated `README.md` to reflect `urltest` usage and `sing-box` version requirements.

### Fixed:
- Resolved `ValueError: Unsupported protocol: None` in `test_protocol_validation.py` by using correct `type` field.
- Fixed `json.decoder.JSONDecodeError` in `test_config_generate.py` by using valid JSON template and proper mocking.

---

## [v1.0.0] - 2025-05-13

### Added:
- Automated testing using `pytest`.
- CI/CD process set up with GitHub Actions:
  - Workflow for testing in the `dev` branch.
  - Workflow for release in the `main` branch.
- Documentation:
  - `DEVELOPMENT.md` describing the development process.
  - `TESTING.md` with instructions for running tests.

### Changed:
- Improved project structure to support testing and CI/CD.
- Modules moved to the `modules/` folder:
  - `config_fetch.py`
  - `config_generate.py`
  - `protocol_validation.py`
  - `service_manage.py`
- Documentation moved to the `docs/` folder:
  - `README.md`
  - `CHANGELOG.md`
  - `DEVELOPMENT.md`
  - `TESTING.md`
- Test files now use `tests/config.json` instead of the root `config.json`.

---

## [v0.3.0] - 2025-05-13

### Changed:
- The `update_singbox.py` script was split into modules for improved readability, testability, and extensibility.
  - `logging_setup.py`: Logging setup.
  - `config_fetch.py`: Fetching and selecting configuration.
  - `protocol_validation.py`: Protocol validation and security settings handling.
  - `config_generate.py`: Configuration generation and validation.
  - `service_manage.py`: Managing the `sing-box` service.

---

## [v0.2.3] - 2025-05-13

### Added:
- Configuration changes are checked before applying.
- The `sing-box` service is restarted only if changes are detected.

---

## [v0.2.2] - 2025-05-12

### Added:
- Logging verbosity levels via the `--debug` flag:
  - `--debug 0`: Minimal logs (default).
  - `--debug 1`: Informational logs for key actions.
  - `--debug 2`: Detailed logs for debugging.

---

## [v0.2.1] - 2025-05-12

### Changed:
- Improvement: The configuration writing process was rewritten. Now the configuration is saved to a temporary file, validated, and only then replaces the main file. This prevents possible issues with corrupting the main configuration file.

---

## [v0.2.0] - 2025-05-11

### Added
- Proxy support (SOCKS and HTTP) for downloading remote configurations.
- Started maintaining CHANGELOG.md!

### Changed
- Switched from urllib to the requests library to support proxy usage.

### Requirements
- Added new dependency: [requests](https://pypi.org/project/requests/). Make sure it is installed.

---

## [v0.1.0] - 2025-05-01

### Added
- Initial version with VLESS and Shadowsocks support.

## [Unreleased]

- Deep refactor of exclusions logic: all duplicate implementations removed, only singbox.server.exclusions remains.
- Centralized atomic file write: now only via singbox.utils.file.handle_temp_file.
- Removed deprecated functions and modules (management.py, temp.py, duplicate exclusions functions).
- Temporary DeprecationWarnings for smooth transition (now unused).
- Improved error handling for loading invalid/empty URLs, always correct return code and message.
- CLI tests no longer depend on .env and environment variables, always check the provided URL.
- Added --exclude-only flag: allows updating exclusions.json without generating the main config.
- Architecture audit and cleanup performed, refactor plan updated in plans/struct_analysis_log.md.

## CLI scenarios: inputs and outputs

| Scenario/Flag                | Input files           | Configs (read)         | Artifacts/outputs                |
|------------------------------|-----------------------|------------------------|----------------------------------|
| -u <url>                     | config.template.json  | exclusions.json        | config.json, backup.json         |
| --dry-run                    | config.template.json  | exclusions.json        | (none, only stdout)              |
| --list-servers               | config.template.json  | exclusions.json        | (none, only stdout)              |
| --exclude <idx>              | config.template.json  | exclusions.json        | exclusions.json                  |
| --exclude-only               | config.template.json  | exclusions.json        | exclusions.json                  |
| --clear-exclusions           | exclusions.json       | exclusions.json        | exclusions.json (cleared/deleted)|
| --remarks/-r <name>          | config.template.json  | exclusions.json        | config.json, backup.json         |
| --index/-i <n>               | config.template.json  | exclusions.json        | config.json, backup.json         |
| (no flags, only -u)          | config.template.json  | exclusions.json        | config.json, backup.json         |

**Notes:**
- exclusions.json is always updated only for relevant actions.
- config.json is not changed in --dry-run mode.
- merged.json and selected_config.json are created only for certain scenarios (see code).
- All artifacts are written to the working directory or the path set by environment variables.

## [Unreleased] — CLI v2: migration to Typer, logic centralization

### Added:
- New CLI on Typer: commands run, dry-run, list-servers, exclusions, clear-exclusions.
- Automatic help generation, aliases, convenient command structure.
- All artifact paths are managed via environment variables (SBOXMGR_LOG, SBOXMGR_CONFIG, etc.).

### Changed:
- All CLI business logic moved to cli_common.py and related modules.
- CLI wrapper is now thin: only routing, no logic duplication.
- Old main.py can be removed after test migration.

### Fixed:
- No more logic duplication between CLI and core modules.
- CLI tests pass for both old and new interfaces (until full migration).

### Best practices:
- For CLI tests, use Typer.CliRunner and monkeypatch for artifact paths.
- All new commands should be implemented as separate Typer functions/subcommands.

## [1.5.0] - 2025-xx-xx
### Changed
- License changed from GPLv3 to MIT License (full project relicensing).

### Fixed
- **sing-box 1.11.0+ Compatibility**: Updated sing-box exporter to remove deprecated legacy special outbounds (`block`, `dns`) and replaced them with modern rule actions (`hijack-dns`) as per sing-box 1.11.0+ requirements
- **Configuration Template**: Updated config template to use `action: "hijack-dns"` instead of deprecated `outbound: "dns-out"` for DNS protocol rules
- **Tests**: Updated test expectations to reflect removal of deprecated outbounds

### Technical Details
- Removed automatic generation of `{"type": "block", "tag": "block"}` and `{"type": "dns", "tag": "dns-out"}` outbounds
- Updated route rules to use rule actions instead of special outbounds
- DNS protocol routing now uses `"action": "hijack-dns"` instead of `"outbound": "dns-out"`
- Maintains backward compatibility with sing-box versions that support the new syntax

### Added
- **Sing-box Version Compatibility**: Automatic version detection and graceful degradation for sing-box < 1.11.0
  - Detects installed sing-box version automatically
  - Uses modern rule actions syntax for sing-box 1.11.0+
  - Falls back to legacy special outbounds for older versions
  - Shows compatibility warnings for outdated versions
  - Added `--skip-version-check` option to bypass version checking
- **Version Utilities**: New `sboxmgr.utils.version` module with version checking functions

### Fixed
- **sing-box 1.11.0+ Compatibility**: Updated sing-box exporter to remove deprecated legacy special outbounds (`block`, `dns`) and replaced them with modern rule actions as per sing-box 1.11.0+ requirements
- **Configuration Template**: Updated config template to use `action: \"hijack-dns\"` instead of deprecated `outbound: \"dns-out\"` for DNS protocol rules
- **Tests**: Updated test expectations to reflect removal of deprecated outbounds

### Technical Details
- Removed automatic generation of `{\"type\": \"block\", \"tag\": \"block\"}` and `{\"type\": \"dns\", \"tag\": \"dns-out\"}` outbounds for sing-box 1.11.0+
- Added automatic legacy outbound generation for sing-box < 1.11.0 compatibility
- Updated route rules to use rule actions instead of special outbounds
- DNS protocol routing now uses `\"action\": \"hijack-dns\"` instead of `\"outbound\": \"dns-out\"` for modern versions
- Added `packaging` dependency for version comparison
- Version checking integrated into CLI commands (`run`, `dry-run`) with debug output
