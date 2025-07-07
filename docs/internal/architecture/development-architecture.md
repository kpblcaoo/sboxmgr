# SBoxMgr Architecture Deep Dive

> **Complete technical description of SBoxMgr architecture from input to output**

## 🎯 Overall Data Flow

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   CLI Command   │───▶│  Configuration   │───▶│   Subscription  │
│                 │    │    Loading       │    │    Fetching     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Final Config   │◀───│   Export Layer   │◀───│   Processing    │
│   (sing-box)    │    │                  │    │    Pipeline     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 📥 Input Layer (CLI Commands)

### File: `src/sboxmgr/cli/commands/export.py`

**Input parameters:**
```bash
sboxctl export \
  -u "https://example.com/subscription" \      # Subscription URL
  --inbound-types tun,socks \                  # Inbound types
  --socks-port 1080 \                         # Inbound parameters
  --postprocessors geo_filter \               # Postprocessors
  --output config.json                        # Output file
```

**Configuration source priority:**
1. `--client-profile file.json` (highest priority)
2. CLI parameters (`--inbound-types`, `--socks-port`, etc.)
3. `--profile profile.json` (if contains client config)
4. Default minimal profile (lowest priority)

**Internal processing:**
```python
def export(...):
    # 1. Load profiles and parameters
    loaded_profile = _load_profile_from_file(profile) if profile else None
    loaded_client_profile = _load_client_profile_from_file(client_profile) if client_profile else None

    # 2. Create ClientProfile from CLI parameters (if needed)
    if not loaded_client_profile and inbound_types:
        loaded_client_profile = build_client_profile_from_cli(...)

    # 3. Create processing chains
    postprocessor_chain = _create_postprocessor_chain(postprocessors)
    middleware_chain = _create_middleware_chain(middleware)

    # 4. Generate configuration
    config_data = _generate_config_from_subscription(...)

    # 5. Save result
    _save_config_to_file(config_data, output)
```

## 🏗️ ClientProfile Building Layer

### File: `src/sboxmgr/cli/inbound_builder.py`

**InboundBuilder - Builder pattern for creating profiles:**

```python
# Usage example
builder = InboundBuilder()
profile = (builder
    .add_tun(address="198.18.0.1/16", mtu=1500)
    .add_socks(port=1080, auth="user:pass")
    .set_dns_mode("tunnel")
    .build())
```

**Supported inbound types:**

1. **TUN** (`add_tun`):
   - `address`: Interface IP address (default: `["198.18.0.1/16"]`)
   - `mtu`: MTU value (default: `1500`, range: `576-9000`)
   - `stack`: Network stack (`system`, `gvisor`, `mixed`, default: `mixed`)
   - `auto_route`: Automatic routing (default: `True`)

2. **SOCKS** (`add_socks`):
   - `port`: Port (default: `1080`, range: `1024-65535`)
   - `listen`: Bind address (default: `"127.0.0.1"` for security)
   - `auth`: Authentication in `"user:pass"` format (optional)

3. **HTTP** (`add_http`):
   - `port`: Port (default: `8080`, range: `1024-65535`)
   - `listen`: Bind address (default: `"127.0.0.1"` for security)
   - `auth`: Authentication in `"user:pass"` format (optional)

4. **TPROXY** (`add_tproxy`):
   - `port`: Port (default: `7895`, range: `1024-65535`)
   - `listen`: Bind address (default: `"0.0.0.0"` - required for TPROXY)
   - `network`: Network type (`tcp`, `udp`, `tcp,udp`, default: `tcp`)

**Security by default:**
- SOCKS/HTTP bind to localhost (`127.0.0.1`)
- Port validation (only unprivileged: 1024-65535)
- Warnings when binding to `0.0.0.0`

## 🌐 Subscription Loading Layer

### File: `src/sboxmgr/subscription/fetchers/`

**Available fetchers:**

1. **URLFetcher** (`url_fetcher.py`):
   - HTTP/HTTPS downloading
   - User-Agent support
   - Automatic decompression (gzip, deflate)
   - Timeout handling

2. **FileFetcher** (`file_fetcher.py`):
   - Local files
   - Relative path support

3. **ApiFetcher** (`apifetcher.py`):
   - API endpoints with tokens
   - JSON response parsing

**URLFetcher example:**
```python
fetcher = URLFetcher()
raw_data = fetcher.fetch("https://example.com/sub", user_agent="sboxmgr/1.0")
# raw_data contains raw subscription data (YAML, JSON, base64, etc.)
```

## 🔍 Subscription Parsing Layer

### File: `src/sboxmgr/subscription/parsers/`

**Format auto-detection:**
```python
def _detect_source_type(raw_data: bytes) -> str:
    """Automatically detects subscription data type."""
    # 1. Check for base64
    # 2. Check for JSON
    # 3. Check for YAML
    # 4. Fallback to URI list
```

**Available parsers:**

1. **Base64Parser** (`base64_parser.py`):
   - Decodes base64 data
   - Parses URI lists inside

2. **ClashParser** (`clash_parser.py`):
   - Clash YAML format
   - Extracts proxies section
   - Converts to ParsedServer objects

3. **JsonParser** (`json_parser.py`):
   - JSON subscription format
   - Nested structure support

4. **URIListParser** (`uri_list_parser.py`):
   - Simple URI lists (ss://, vmess://, etc.)
   - Line-by-line parsing

5. **SingboxParser** (`singbox_parser.py`):
   - Native sing-box format
   - Extracts outbounds

**Parsing result:**
```python
class ParsedServer:
    protocol: str           # "shadowsocks", "vmess", "vless", etc.
    server: str            # IP or domain
    port: int              # Server port
    meta: Dict[str, Any]   # All other parameters (passwords, ciphers, etc.)
```

## ⚙️ Processing Layer (Middleware)

### File: `src/sboxmgr/subscription/middleware/`

**Available middleware:**

1. **LoggingMiddleware** (`logging.py`):
   - Logs all operations
   - Server statistics counting
   - Debug information

2. **EnrichmentMiddleware** (`enrichment.py`):
   - Enriches server metadata
   - GeoIP country detection
   - Adds tags and labels

**Execution order:**
```
Raw Data → Parsing → [Middleware Chain] → Parsed Servers
                     ↓
              1. Logging (statistics)
              2. Enrichment (geo data)
```

## 🔄 Postprocessing Layer

### File: `src/sboxmgr/subscription/postprocessors/`

**Available postprocessors:**

1. **GeoFilterPostprocessor** (`geo_filter.py`):
   - Filters servers by country
   - Includes/excludes specific countries
   - Uses GeoIP databases

2. **TagFilterPostprocessor** (`tag_filter.py`):
   - Filters by server tags
   - Whitelist/blacklist functionality

3. **LatencySortPostprocessor** (`latency_sort.py`):
   - Sorts servers by latency
   - Ping testing functionality

**Postprocessor chain:**
```python
chain = PostprocessorChain([
    GeoFilterPostprocessor(exclude=["CN", "RU"]),
    TagFilterPostprocessor(include=["premium"]),
    LatencySortPostprocessor()
])
servers = chain.process(servers, context)
```

## 📤 Export Layer

### File: `src/sboxmgr/subscription/exporters/`

**Available exporters:**

1. **SingboxExporter** (`singbox_exporter_v2.py`):
   - Generates sing-box configuration
   - Supports all sing-box protocols
   - Routing rule generation

2. **ClashExporter** (`clashexporter.py`):
   - Generates Clash configuration
   - Proxy group support

**Export process:**
```python
exporter = SingboxExporter()
config = exporter.export(
    servers=parsed_servers,
    client_profile=client_profile,
    routing_profile=routing_profile
)
```

## 🛡️ Security Layer

### Security Features

1. **Input Validation:**
   - URL validation and sanitization
   - Port range validation (1024-65535)
   - Address validation (localhost by default)

2. **Sandboxing:**
   - Middleware execution isolation
   - Plugin sandboxing
   - Resource limits

3. **Error Handling:**
   - Fail-tolerant pipeline
   - Partial success handling
   - Secure error messages

## 🔧 Configuration Management

### Environment Variables
- `SBOXMGR_CONFIG_FILE`: Output config path
- `SBOXMGR_LOG_FILE`: Log file path
- `SBOXMGR_DEBUG`: Debug level
- `SBOXMGR_LANG`: Interface language

### Profile System
- JSON-based configuration profiles
- Environment variable overrides
- Profile inheritance and composition

## 📊 Testing Architecture

### Test Coverage
- Unit tests for all components
- Integration tests for pipelines
- Edge case testing
- Security testing

### Test Structure
```
tests/
├── unit/           # Unit tests
├── integration/    # Integration tests
├── edge/          # Edge case tests
└── e2e/           # End-to-end tests
```

## 🚀 Performance Considerations

### Caching
- In-memory caching for subscriptions
- Cache invalidation strategies
- Force reload options

### Optimization
- Lazy loading of components
- Efficient data structures
- Minimal memory footprint

## 🔗 Integration Points

### External Dependencies
- sing-box: Configuration format
- GeoIP databases: Country detection
- HTTP clients: Subscription fetching

### Plugin System
- Extensible fetcher/parser/exporter system
- Plugin registration and discovery
- Sandboxed execution

## 📈 Monitoring and Logging

### Logging Levels
- DEBUG: Detailed debugging information
- INFO: General operational information
- WARNING: Warning messages
- ERROR: Error conditions

### Metrics
- Server count statistics
- Processing time measurements
- Error rate tracking

## 🔄 Future Architecture

### Planned Improvements
- Plugin marketplace
- Advanced routing rules
- Real-time configuration updates
- Distributed deployment support

## See Also

- [Contributing](contributing.md) - Development guidelines
- [Testing](testing.md) - Testing practices
- [Security](../security.md) - Security considerations
