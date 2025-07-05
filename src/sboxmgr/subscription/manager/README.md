# Subscription Manager Module

This module provides modular subscription management functionality, refactored from the original monolithic `manager.py` file.

## Module Structure

```
manager/
├── __init__.py              # Package interface and exports
├── core.py                  # Main SubscriptionManager class
├── parser_detector.py       # Parser auto-detection functionality
├── cache.py                 # Cache management for expensive operations
├── error_handler.py         # Centralized error handling
├── data_processor.py        # Data processing pipeline stages
├── pipeline_coordinator.py  # Pipeline orchestration and coordination
└── README.md               # This documentation
```

## Architecture

The module follows the Single Responsibility Principle (SRP) by separating different aspects of subscription management into specialized components:

### Core Components

1. **core.py** - Main `SubscriptionManager` class that orchestrates all components
2. **parser_detector.py** - Auto-detection of appropriate parsers based on data content
3. **cache.py** - `CacheManager` for thread-safe caching of expensive operations
4. **error_handler.py** - `ErrorHandler` for centralized error creation and management
5. **data_processor.py** - `DataProcessor` for fetching, parsing, and validation stages
6. **pipeline_coordinator.py** - `PipelineCoordinator` for orchestrating pipeline stages

### Key Features

- **Modular Design**: Each component has a single, well-defined responsibility
- **Thread-Safe Caching**: Efficient caching with proper thread synchronization
- **Comprehensive Error Handling**: Centralized error management with context tracking
- **Pipeline Orchestration**: Coordinated execution of all processing stages
- **Parser Auto-Detection**: Intelligent detection of appropriate data parsers
- **Extensible Architecture**: Easy to add new components or modify existing ones

## Usage

### Basic Usage

```python
from sboxmgr.subscription.manager import SubscriptionManager
from sboxmgr.subscription.models import SubscriptionSource, PipelineContext

# Create subscription source
source = SubscriptionSource(
    url="https://example.com/subscription",
    source_type="url_base64"
)

# Create manager
manager = SubscriptionManager(source)

# Get servers
result = manager.get_servers()
print(f"Found {len(result.config)} servers")
```

### Advanced Configuration

```python
from sboxmgr.subscription.middleware_base import MiddlewareChain
from sboxmgr.subscription.postprocessor_base import PostProcessorChain

# Custom middleware and post-processor chains
middleware_chain = MiddlewareChain([...])
postprocessor_chain = PostProcessorChain([...])

# Create manager with custom components
manager = SubscriptionManager(
    source=source,
    middleware_chain=middleware_chain,
    postprocessor_chain=postprocessor_chain
)

# Process with custom context
context = PipelineContext(
    mode='strict',
    debug_level=2
)

result = manager.get_servers(
    user_routes=['US', 'CA'],
    exclusions=['CN'],
    context=context,
    force_reload=True
)
```

### Export Configuration

```python
# Export configuration
export_result = manager.export_config(
    user_routes=['US', 'CA'],
    exclusions=['test'],
    routing_plugin=custom_router
)

if export_result.success:
    print("Export successful:", export_result.config)
else:
    print("Export failed:", export_result.errors)
```

## Component Details

### Core.py - SubscriptionManager

The main orchestrator that coordinates all components:

```python
class SubscriptionManager:
    """Manages subscription data processing pipeline."""
    
    def __init__(self, source, detect_parser=None, postprocessor_chain=None, middleware_chain=None)
    def get_servers(self, user_routes=None, exclusions=None, mode=None, context=None, force_reload=False) -> PipelineResult
    def export_config(self, exclusions=None, user_routes=None, context=None, routing_plugin=None, export_manager=None) -> PipelineResult
```

### Parser_detector.py - Parser Detection

Auto-detects appropriate parsers based on content:

```python
def detect_parser(raw: bytes, source_type: str) -> Optional[ParserProtocol]
```

Supports:
- Explicit type detection (url_json, file_base64, etc.)
- Content-based auto-detection (JSON, YAML, base64, URI lists)
- Fallback to base64 parser

### Cache.py - CacheManager

Thread-safe caching for expensive operations:

```python
class CacheManager:
    def create_cache_key(self, mode: str, context: PipelineContext, fetcher_source) -> tuple
    def get_cached_result(self, cache_key: tuple) -> Any
    def set_cached_result(self, cache_key: tuple, result: Any) -> None
    def clear_cache(self) -> None
```

### Error_handler.py - ErrorHandler

Centralized error management:

```python
class ErrorHandler:
    def create_pipeline_error(self, error_type: ErrorType, stage: str, message: str, context_data: dict = None) -> PipelineError
    def create_fetch_error(self, message: str, context_data: dict = None) -> PipelineError
    def create_validation_error(self, stage: str, message: str, context_data: dict = None) -> PipelineError
    def add_error_to_context(self, context, error: PipelineError) -> None
```

### Data_processor.py - DataProcessor

Handles data processing pipeline stages:

```python
class DataProcessor:
    def fetch_and_validate_raw(self, context: PipelineContext) -> Tuple[bytes, bool]
    def parse_servers(self, raw_data: bytes, context: PipelineContext) -> Tuple[List[Any], bool]
    def validate_parsed_servers(self, servers: List[Any], context: PipelineContext) -> Tuple[List[Any], bool]
```

### Pipeline_coordinator.py - PipelineCoordinator

Coordinates pipeline stages:

```python
class PipelineCoordinator:
    def apply_policies(self, servers: List[Any], context: PipelineContext) -> List[Any]
    def process_middleware(self, servers: List[Any], context: PipelineContext) -> Tuple[List[Any], bool]
    def postprocess_and_select(self, servers: List[Any], user_routes: List[str], exclusions: List[str], mode: str) -> Tuple[List[Any], bool]
    def export_configuration(self, servers_result: PipelineResult, ...) -> PipelineResult
```

## Pipeline Stages

The subscription processing pipeline consists of the following stages:

1. **Fetch & Validate Raw Data**
   - Fetch data from source (URL, file, API)
   - Apply raw data validation
   - Handle User-Agent and headers

2. **Parse Servers**
   - Auto-detect appropriate parser
   - Parse raw data into server objects
   - Handle various formats (JSON, YAML, base64, URI lists)

3. **Validate Parsed Servers**
   - Apply parsed server validation rules
   - Check required fields and formats
   - Handle strict vs tolerant mode

4. **Apply Policies**
   - Run registered policy plugins
   - Apply filtering and transformation rules
   - Continue on policy errors

5. **Process Middleware**
   - Run middleware chain transformations
   - Enrich servers with additional metadata
   - Apply cross-cutting concerns

6. **Post-process & Select**
   - Apply post-processing transformations
   - Deduplicate servers
   - Select servers based on user routes and exclusions

## Error Handling

The module provides comprehensive error handling:

### Error Types

- `FETCH`: Data fetching errors
- `VALIDATION`: Data validation errors  
- `PARSE`: Data parsing errors
- `INTERNAL`: Internal processing errors

### Error Context

Errors include:
- Error type and stage
- Human-readable message
- Additional context data
- Timestamp

### Error Propagation

- Errors are collected in pipeline context
- Processing continues where possible
- Final result includes all errors encountered

## Caching

The cache manager provides:

### Cache Keys

Generated from:
- Source URL
- User-Agent header
- Custom headers
- Tag filters
- Processing mode

### Thread Safety

- Thread-safe operations using locks
- Concurrent access protection
- Cache consistency guarantees

### Cache Operations

- Get/set cached results
- Clear entire cache
- Remove specific entries
- Get cache size statistics

## Configuration Options

### Processing Modes

- `strict`: Continue processing even with validation errors
- `tolerant`: Stop processing on validation failures (default)

### Debug Levels

- `0`: No debug output (default)
- `1`: Basic progress logging
- `2`: Detailed debug information

### Force Reload

- `False`: Use cached results when available (default)
- `True`: Bypass cache and fetch fresh data

## Migration

The original `manager.py` file has been preserved as a compatibility layer. All existing code will continue to work without changes.

To use the new modular version:

```python
# Old way (still works)
from sboxmgr.subscription.manager import SubscriptionManager

# New way (recommended for new features)
from sboxmgr.subscription.manager import (
    SubscriptionManager, CacheManager, ErrorHandler
)
```

## Refactoring Statistics

- **Before**: 1 file, 689 lines
- **After**: 6 files, ~650 lines
- **Improvement**: Better organization, testability, and maintainability

## Benefits

1. **Maintainability**: Easier to modify individual components
2. **Testability**: Each component can be tested independently
3. **Performance**: Improved caching and error handling
4. **Extensibility**: Easy to add new pipeline stages or modify existing ones
5. **Reusability**: Individual components can be used in other contexts
6. **Debugging**: Better error tracking and context management 