# Architectural Decision Log

_Часть ADR написана ретроспективно для фиксации ключевых решений, принятых ранее в проекте._

| ID        | Title                                 | Status     | Date       | Summary                                 |
|-----------|---------------------------------------|------------|------------|-----------------------------------------|
| ADR-0001  | CLI Security Model                    | Accepted   | 2025-06-20 | SEC-01...SEC-10, threat model           |
| ADR-0002  | Plugin Registry System                | Accepted   | 2025-06-21 | Decorator/entry-point registry          |
| ADR-0003  | Subscription Models & Normalization   | Accepted   | 2025-06-21 | ParsedServer, SubscriptionSource        |
| ADR-0004  | Plugin-Based Subscription Pipeline    | Accepted   | 2025-06-21 | Fetcher, Parser, Exporter, etc.         |
| ADR-0005  | Extensible Routing Layer              | Accepted   | 2025-06-22 | RoutingPlugin, context, mode, fallback  |
| ADR-0006  | Internationalization (i18n) Architecture | Accepted   | 2025-06-22 | Multilingual support with security focus |
| ADR-0007  | Validator Architecture and Pipeline Context | Proposed | 2025-06-22 | Comprehensive validation pipeline with context tracking and fail-tolerance |
| ADR-0008  | Defaults and Fail-tolerance Architecture    | Accepted | 2025-06-22 | Default value management and graceful degradation patterns |
| ADR-0009  | Configuration System Architecture           | Accepted | 2025-06-15 | Pydantic BaseSettings with hierarchical configuration and service mode detection |
| ADR-0010  | Logging Core Architecture                   | Accepted | 2025-06-15 | Multi-sink structured logging with trace ID propagation |
| ADR-0011  | Event System Architecture                   | Accepted | 2025-06-15 | Lightweight EventBus with pydispatch for component decoupling |
| ADR-0012  | Service Architecture & Dual-Path Support    | Accepted | 2025-07-03 | Three-tier architecture with dual-path support |
| ADR-0015  | Agent-Installer Separation & Installation Strategy | Accepted | 2025-07-03 | Clear separation between agent (runtime) and installer (setup) responsibilities |
| ADR-0016  | Pydantic as Single Source of Truth for Validation and Schema Generation | Accepted | 2025-07-03 | Standardized approach using Pydantic for validation and automatic schema generation |
| ADR-0017  | Full Profile Architecture                    | Accepted | 2025-06-29 | Unified configuration entity covering all configurable components |
| ADR-0018  | Subscription Management Architecture         | Accepted | 2025-06-29 | Subscription lifecycle, validation, and management patterns |
| ADR-0019  | Full Profile UX & Runtime Management         | Accepted | 2025-06-29 | Production-ready UX and runtime aspects for profiles and subscriptions |
| ADR-0020  | Profile Runtime Semantics & Outbound Management | In Progress | 2025-07-01 | Runtime semantics, outbound policies, caching, and versioning |
| ADR-0021  | Licensing Architecture | Accepted | 2025-07-01 | AGPL-3.0 license selection and compliance framework |
| ADR-0022  | Tag Normalization Architecture | Proposed | 2025-07-06 | Centralized tag normalization middleware for consistent server naming |

## Summary
- **Security**: ADR-0001 establishes CLI security foundation
- **Extensibility**: ADR-0002, ADR-0004 define plugin architecture
- **Data Models**: ADR-0003 standardizes subscription data structures
- **Routing**: ADR-0005 handles config generation and routing
- **i18n**: ADR-0006 provides multilingual support with security focus
- **Validation**: ADR-0007 introduces comprehensive validation pipeline with context tracking and fail-tolerance
- **Resilience**: ADR-0008 defines fail-tolerance and default value patterns
- **Configuration**: ADR-0009 establishes Pydantic-based configuration system with service mode detection
- **Logging**: ADR-0010 implements multi-sink structured logging with trace correlation
- **Events**: ADR-0011 provides lightweight event system for component decoupling
- **Services**: ADR-0012 defines three-tier service architecture with dual-path support
- **Installation**: ADR-0015 separates agent runtime from installer setup responsibilities
- **Validation**: ADR-0016 standardizes Pydantic as single source of truth for validation and schema generation
- **Profiles**: ADR-0017 establishes unified configuration entity for all pipeline components
- **Subscriptions**: ADR-0018 provides extended subscription management with isolation and auto-switching
- **UX**: ADR-0019 covers production-ready UX and runtime management for profiles and subscriptions
- **Licensing**: ADR-0021 establishes AGPL-3.0 license selection and compliance framework
- **Tag Normalization**: ADR-0022 centralizes tag normalization for consistent server naming across User-Agent types
