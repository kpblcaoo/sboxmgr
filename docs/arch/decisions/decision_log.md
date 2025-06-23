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

## Summary
- **Security**: ADR-0001 establishes CLI security foundation
- **Extensibility**: ADR-0002, ADR-0004 define plugin architecture
- **Data Models**: ADR-0003 standardizes subscription data structures  
- **Routing**: ADR-0005 handles config generation and routing
- **i18n**: ADR-0006 provides multilingual support with security focus
- **Validation**: ADR-0007 introduces comprehensive validation pipeline with context tracking and fail-tolerance 