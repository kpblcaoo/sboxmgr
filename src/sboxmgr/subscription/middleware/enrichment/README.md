# Enrichment Middleware Module

This module provides modular data enrichment functionality for subscription processing, refactored from the original monolithic `enrichment.py` file.

## Module Structure

```
enrichment/
├── __init__.py      # Package interface and exports
├── core.py          # Main EnrichmentMiddleware coordinator
├── basic.py         # Basic metadata enrichment
├── geo.py           # Geographic information enrichment
├── performance.py   # Performance metrics enrichment
├── security.py      # Security analysis enrichment
├── custom.py        # Custom profile-based enrichment
└── README.md        # This documentation
```

## Architecture

The module follows the Single Responsibility Principle (SRP) by separating different types of enrichment into specialized components:

### Core Components

1. **core.py** - Main `EnrichmentMiddleware` class that coordinates all enrichers
2. **basic.py** - `BasicEnricher` for fundamental metadata (timestamps, IDs, tags)
3. **geo.py** - `GeoEnricher` for geographic information (country, city, coordinates)
4. **performance.py** - `PerformanceEnricher` for performance metrics (latency, efficiency)
5. **security.py** - `SecurityEnricher` for security analysis (encryption, vulnerabilities)
6. **custom.py** - `CustomEnricher` for profile-specific enrichment

### Key Features

- **Modular Design**: Each enricher has a single responsibility
- **Configurable**: Enable/disable individual enrichers via configuration
- **Cacheable**: Geographic and performance data are cached for efficiency
- **Profile-Aware**: Custom enrichment based on profile configuration
- **Error-Tolerant**: Failures in one enricher don't affect others

## Usage

### Basic Usage

```python
from sboxmgr.subscription.middleware.enrichment import EnrichmentMiddleware

# Create middleware with default configuration
middleware = EnrichmentMiddleware()

# Process servers
enriched_servers = middleware.process(servers, context, profile)
```

### Advanced Configuration

```python
config = {
    'enable_geo_enrichment': True,
    'enable_performance_enrichment': True,
    'enable_security_enrichment': True,
    'enable_custom_enrichment': True,
    'geo_database_path': '/path/to/geoip.db',
    'performance_cache_duration': 300,
    'custom_enrichers': ['subscription_tags', 'priority_scoring'],
    'max_enrichment_time': 1.0
}

middleware = EnrichmentMiddleware(config)
```

### Individual Enrichers

```python
from sboxmgr.subscription.middleware.enrichment import (
    BasicEnricher, GeoEnricher, PerformanceEnricher
)

# Use individual enrichers
basic_enricher = BasicEnricher()
geo_enricher = GeoEnricher('/path/to/geoip.db')
performance_enricher = PerformanceEnricher(cache_duration=600)

# Apply enrichment
server = basic_enricher.enrich(server, context)
server = geo_enricher.enrich(server, context)
server = performance_enricher.enrich(server, context)
```

## Enrichment Types

### Basic Enrichment

Always applied to all servers:
- `enriched_at`: Processing timestamp
- `trace_id`: Pipeline trace ID
- `server_id`: Unique server identifier hash
- `source`: Source URL/file information
- `tag`: Normalized server tag

### Geographic Enrichment

Adds geographic metadata:
- `geo.country`: ISO country code
- `geo.country_name`: Full country name
- `geo.city`: City name
- `geo.latitude/longitude`: Coordinates
- `geo.timezone`: Timezone information
- `geo.type`: Address type (private/public)

### Performance Enrichment

Adds performance indicators:
- `performance.estimated_latency_class`: Estimated latency (low/medium/high)
- `performance.protocol_efficiency`: Protocol efficiency rating
- `performance.security_level`: Security level assessment
- `performance.reliability_score`: Reliability score (0.0-1.0)

### Security Enrichment

Adds security analysis:
- `security.encryption_level`: Encryption strength (strong/moderate/weak/none)
- `security.port_classification`: Port type classification
- `security.protocol_vulnerabilities`: Known vulnerabilities list
- `security.recommended_settings`: Recommended configuration

### Custom Enrichment

Profile-based enrichment includes:
- `subscription_tags`: Subscription metadata and tags
- `priority_scoring`: Priority score based on profile preferences
- `compatibility_check`: Export format compatibility analysis
- `region_preference`: Regional scoring and preferences
- `usage_hints`: Usage recommendations

## Configuration Options

### Main Configuration

- `enable_geo_enrichment` (bool): Enable geographic enrichment
- `enable_performance_enrichment` (bool): Enable performance metrics
- `enable_security_enrichment` (bool): Enable security analysis
- `enable_custom_enrichment` (bool): Enable custom profile-based enrichment
- `max_enrichment_time` (float): Maximum time per server (seconds)

### Geographic Configuration

- `geo_database_path` (str): Path to GeoIP2 database file

### Performance Configuration

- `performance_cache_duration` (int): Cache duration in seconds

### Custom Enrichment Configuration

- `custom_enrichers` (list): List of custom enrichers to apply:
  - `subscription_tags`: Add subscription metadata
  - `priority_scoring`: Calculate priority scores
  - `compatibility_check`: Check export format compatibility
  - `region_preference`: Add regional preferences
  - `usage_hints`: Add usage recommendations

## Profile Integration

The enrichment system integrates with FullProfile configuration:

```python
# Profile metadata configuration
profile.metadata['enrichment'] = {
    'enable_geo_enrichment': True,
    'custom_enrichers': ['priority_scoring', 'compatibility_check']
}
```

## Performance Considerations

### Caching

- Geographic data is cached by server address
- Performance data is cached by server address:port
- Cache durations are configurable per enricher type

### Time Limits

- `max_enrichment_time` prevents slow enrichment from blocking pipeline
- If time limit exceeded, remaining servers are processed without enrichment

### Error Handling

- Individual enricher failures don't stop the pipeline
- Errors are logged in server metadata for debugging
- Graceful degradation ensures core functionality continues

## Migration

The original `enrichment.py` file has been preserved as a compatibility layer. All existing code will continue to work without changes.

To use the new modular version:

```python
# Old way (still works)
from sboxmgr.subscription.middleware.enrichment import EnrichmentMiddleware

# New way (recommended for new features)
from sboxmgr.subscription.middleware.enrichment import (
    EnrichmentMiddleware, GeoEnricher, PerformanceEnricher
)
```

## Refactoring Statistics

- **Before**: 1 file, 695 lines
- **After**: 6 files, ~650 lines
- **Improvement**: Better organization, testability, and maintainability

## Benefits

1. **Maintainability**: Easier to modify individual enrichers
2. **Testability**: Each enricher can be tested independently
3. **Performance**: Optional enrichers reduce processing overhead
4. **Extensibility**: Easy to add new enrichment types
5. **Reusability**: Individual enrichers can be used in other contexts
