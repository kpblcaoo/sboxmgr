# Phase 3 Gherkin Scenarios

## Обзор

Этот документ содержит Gherkin сценарии для Phase 3 архитектуры системы управления подписками, которая включает:

- **PostProcessor Architecture** - система постобработки серверов
- **Middleware System** - промежуточное ПО для обработки данных
- **Profile Integration** - интеграция с профилями пользователей
- **Chain Execution** - цепочки обработки с различными стратегиями
- **Error Handling** - обработка ошибок и восстановление
- **Export Integration** - интеграция с экспортом в sing-box формат

## 1. BasePostProcessor Architecture

### Scenario: Инициализация базового постпроцессора
```gherkin
Feature: BasePostProcessor Initialization
  As a developer
  I want to create postprocessors with configuration
  So that I can customize their behavior

  Scenario: Initialize postprocessor with configuration
    Given I have a postprocessor configuration
      | key           | value     |
      | test_option   | test_value|
    When I create a BasePostProcessor with the configuration
    Then the postprocessor should have the configuration stored
    And the plugin_type should be "postprocessor"
    And the can_process method should return true for non-empty server lists
    And the can_process method should return false for empty server lists
```

### Scenario: Проверка возможности обработки серверов
```gherkin
Feature: PostProcessor Can Process Check
  As a system
  I want to check if postprocessors can handle servers
  So that I can skip incompatible processors

  Scenario: Check processing capability
    Given I have a list of 5 ParsedServer objects
    And I have a BasePostProcessor instance
    When I call can_process with the server list
    Then it should return true
    And when I call can_process with an empty list
    Then it should return false
```

## 2. ProfileAwarePostProcessor

### Scenario: Извлечение конфигурации фильтров из профиля
```gherkin
Feature: Profile Filter Configuration Extraction
  As a postprocessor
  I want to extract filter configuration from profiles
  So that I can apply profile-specific filtering rules

  Background:
    Given I have a FullProfile with FilterProfile
      | exclude_tags | only_tags | exclusions        |
      | blocked,slow | premium   | bad.server.com    |

  Scenario: Extract filter configuration
    Given I have a ProfileAwarePostProcessor
    When I call extract_filter_config with the profile
    Then it should return the FilterProfile
    And the exclude_tags should contain "blocked" and "slow"
    And the only_tags should contain "premium"
    And the exclusions should contain "bad.server.com"

  Scenario: Handle missing profile
    Given I have a ProfileAwarePostProcessor
    When I call extract_filter_config with None
    Then it should return None
```

### Scenario: Проверка исключения серверов на основе профиля
```gherkin
Feature: Server Exclusion Based on Profile
  As a postprocessor
  I want to exclude servers based on profile configuration
  So that I can apply user-specific filtering

  Background:
    Given I have a FilterProfile with exclude_tags ["blocked", "slow"]
    And I have a FilterProfile with only_tags ["premium"]

  Scenario: Exclude server by tag
    Given I have a ParsedServer with tag "blocked"
    And I have a ProfileAwarePostProcessor
    When I call should_exclude_server with the server and filter config
    Then it should return true

  Scenario: Include only specific tags
    Given I have a ParsedServer with tag "basic"
    And I have a ProfileAwarePostProcessor
    And the filter config has only_tags ["premium"]
    When I call should_exclude_server with the server and filter config
    Then it should return true

  Scenario: Exclude by server address
    Given I have a ParsedServer with address "bad.server.com" and port 443
    And I have a ProfileAwarePostProcessor
    And the filter config has exclusions ["bad.server.com"]
    When I call should_exclude_server with the server and filter config
    Then it should return true
```

## 3. ChainablePostProcessor

### Scenario: Обработка с pre/post хуками
```gherkin
Feature: Chainable PostProcessor with Pre/Post Hooks
  As a postprocessor
  I want to execute setup and cleanup logic
  So that I can manage resources and state properly

  Scenario: Execute with pre/post hooks
    Given I have a ChainablePostProcessor
    And I have a list of 3 ParsedServer objects
    And I have a PipelineContext
    When I call process on the postprocessor
    Then pre_process should be called before main processing
    And _do_process should be called with the servers
    And post_process should be called after main processing
    And the result should be returned
```

## 4. GeoFilterPostProcessor

### Scenario: Фильтрация по географическому расположению
```gherkin
Feature: Geographic Server Filtering
  As a user
  I want to filter servers by geographic location
  So that I can optimize for my location

  Background:
    Given I have a GeoFilterPostProcessor with configuration
      | allowed_countries | blocked_countries | fallback_mode |
      | US,CA,UK         | CN                | allow_all     |

  Scenario: Filter servers by allowed countries
    Given I have servers with countries ["US", "CA", "UK", "CN", "DE"]
    When I process the servers through the geo filter
    Then only servers from US, CA, and UK should remain
    And servers from CN should be excluded
    And servers from DE should be included (fallback mode)

  Scenario: Extract country code from metadata
    Given I have a ParsedServer with meta {"country": "us"}
    When I call _extract_country_code on the server
    Then it should return "US"

  Scenario: Extract country code from geo metadata
    Given I have a ParsedServer with meta {"geo": {"country": "ca"}}
    When I call _extract_country_code on the server
    Then it should return "CA"

  Scenario: Extract country code from tag
    Given I have a ParsedServer with tag "US-Server-1"
    When I call _extract_country_code on the server
    Then it should return "US"

  Scenario: Extract country code from domain TLD
    Given I have a ParsedServer with address "server.uk"
    When I call _extract_country_code on the server
    Then it should return "UK"

  Scenario: Handle servers without country information
    Given I have a ParsedServer with no country metadata
    And the fallback_mode is "allow_all"
    When I call _should_include_server
    Then it should return true
```

## 5. TagFilterPostProcessor

### Scenario: Фильтрация по тегам серверов
```gherkin
Feature: Tag-based Server Filtering
  As a user
  I want to filter servers by tags
  So that I can select servers with specific characteristics

  Background:
    Given I have a TagFilterPostProcessor with configuration
      | include_tags | exclude_tags | case_sensitive | fallback_mode |
      | Premium,Fast | Blocked,Slow | false          | allow         |

  Scenario: Filter by include tags
    Given I have servers with tags ["Premium", "Basic", "Standard"]
    When I process the servers through the tag filter
    Then only servers with "Premium" tag should remain
    And servers with "Basic" and "Standard" should be excluded

  Scenario: Filter by exclude tags
    Given I have servers with tags ["Premium", "Blocked", "Fast"]
    When I process the servers through the tag filter
    Then servers with "Premium" and "Fast" should remain
    And servers with "Blocked" should be excluded

  Scenario: Case insensitive tag matching
    Given I have a TagFilterPostProcessor with case_sensitive false
    And I have servers with tags ["premium", "PREMIUM", "Premium"]
    When I process the servers through the tag filter
    Then all servers should be included (case insensitive)

  Scenario: Handle servers without tags
    Given I have servers with no tags
    And the fallback_mode is "allow"
    When I process the servers through the tag filter
    Then all servers should be included

  Scenario: Extract tags from server metadata
    Given I have a ParsedServer with tag "US-Premium-01"
    And meta {"tags": ["Fast", "Reliable"]}
    When I call _extract_server_tags on the server
    Then it should return ["US-Premium-01", "US", "Premium", "01", "Fast", "Reliable"]
```

## 6. LatencySortPostProcessor

### Scenario: Сортировка серверов по задержке
```gherkin
Feature: Latency-based Server Sorting
  As a user
  I want to sort servers by latency
  So that I can prioritize faster servers

  Background:
    Given I have a LatencySortPostProcessor with configuration
      | sort_order | max_latency_ms | measurement_method | remove_unreachable |
      | asc        | 500            | cached             | false              |

  Scenario: Sort servers by latency ascending
    Given I have servers with latencies [300, 150, 450, 100]
    When I process the servers through the latency sorter
    Then the servers should be sorted as [100, 150, 300, 450]
    And each server should have latency_ms in metadata

  Scenario: Filter by maximum latency
    Given I have servers with latencies [300, 600, 150, 800]
    And max_latency_ms is 500
    When I process the servers through the latency sorter
    Then servers with latency > 500 should be marked with high_latency
    And all servers should remain in the list (remove_unreachable = false)

  Scenario: Remove unreachable servers
    Given I have a LatencySortPostProcessor with remove_unreachable true
    And I have servers with latencies [300, 600, 150, 800]
    And max_latency_ms is 500
    When I process the servers through the latency sorter
    Then only servers with latency <= 500 should remain
    And servers with latency > 500 should be removed
```

## 7. PostProcessorChain

### Scenario: Последовательное выполнение цепочки
```gherkin
Feature: Sequential PostProcessor Chain Execution
  As a system
  I want to execute multiple postprocessors in sequence
  So that I can apply complex processing pipelines

  Background:
    Given I have a PostProcessorChain with configuration
      | execution_mode | error_strategy | collect_metadata |
      | sequential     | continue       | true             |
    And I have processors [GeoFilter, TagFilter, LatencySort]

  Scenario: Execute processors sequentially
    Given I have 10 servers with various countries and tags
    When I process the servers through the chain
    Then GeoFilter should execute first
    And TagFilter should execute second with GeoFilter results
    And LatencySort should execute last with TagFilter results
    And the final result should contain filtered and sorted servers

  Scenario: Handle processor failures gracefully
    Given I have a PostProcessorChain with error_strategy "continue"
    And one processor in the chain will fail
    When I process the servers through the chain
    Then the failing processor should be logged
    And the chain should continue with remaining processors
    And the final result should contain processed servers

  Scenario: Collect execution metadata
    Given I have a PostProcessorChain with collect_metadata true
    When I process the servers through the chain
    Then execution metadata should be collected
    And it should include processors_executed list
    And it should include processors_failed list
    And it should include total duration
```

### Scenario: Параллельное выполнение цепочки
```gherkin
Feature: Parallel PostProcessor Chain Execution
  As a system
  I want to execute postprocessors in parallel
  So that I can improve performance for independent processors

  Background:
    Given I have a PostProcessorChain with configuration
      | execution_mode | parallel_workers | error_strategy |
      | parallel       | 4                | continue       |

  Scenario: Execute processors in parallel
    Given I have 3 independent postprocessors
    When I process the servers through the chain
    Then all processors should execute simultaneously
    And the results should be merged appropriately
    And performance should be improved over sequential execution
```

### Scenario: Условное выполнение цепочки
```gherkin
Feature: Conditional PostProcessor Chain Execution
  As a system
  I want to conditionally execute postprocessors
  So that I can optimize processing based on conditions

  Background:
    Given I have a PostProcessorChain with execution_mode "conditional"

  Scenario: Execute processors based on conditions
    Given I have a processor that requires minimum 5 servers
    And I have 3 servers
    When I process the servers through the chain
    Then the processor should be skipped
    And it should be logged in processors_skipped

  Scenario: Execute processors based on profile conditions
    Given I have a processor that requires specific profile configuration
    And I have a profile without the required configuration
    When I process the servers through the chain
    Then the processor should be skipped
    And the chain should continue with remaining processors
```

## 8. BaseMiddleware Architecture

### Scenario: Инициализация базового middleware
```gherkin
Feature: BaseMiddleware Initialization
  As a developer
  I want to create middleware with configuration
  So that I can customize their behavior

  Scenario: Initialize middleware with configuration
    Given I have a middleware configuration
      | enabled | test_option |
      | true    | test_value  |
    When I create a BaseMiddleware with the configuration
    Then the middleware should have the configuration stored
    And the middleware_type should be "middleware"
    And the enabled flag should be true
    And the can_process method should return true for enabled middleware
    And the can_process method should return false for disabled middleware
```

## 9. ProfileAwareMiddleware

### Scenario: Извлечение конфигурации middleware из профиля
```gherkin
Feature: Middleware Configuration from Profile
  As a middleware
  I want to extract configuration from profiles
  So that I can apply profile-specific settings

  Background:
    Given I have a FullProfile with metadata
      | middleware | logging | enrichment |
      | enabled    | true    | false      |

  Scenario: Extract middleware configuration
    Given I have a ProfileAwareMiddleware
    When I call extract_middleware_config with the profile
    Then it should return the middleware configuration
    And it should include profile-specific settings

  Scenario: Handle missing profile metadata
    Given I have a FullProfile without middleware metadata
    When I call extract_middleware_config with the profile
    Then it should return an empty dictionary
```

## 10. ChainableMiddleware

### Scenario: Обработка с pre/post хуками в middleware
```gherkin
Feature: Chainable Middleware with Pre/Post Hooks
  As a middleware
  I want to execute setup and cleanup logic
  So that I can manage resources and state properly

  Scenario: Execute with pre/post hooks
    Given I have a ChainableMiddleware
    And I have a list of 3 ParsedServer objects
    And I have a PipelineContext
    When I call process on the middleware
    Then pre_process should be called before main processing
    And _do_process should be called with the servers
    And post_process should be called after main processing
    And the result should be returned
```

## 11. LoggingMiddleware

### Scenario: Логирование обработки серверов
```gherkin
Feature: Server Processing Logging
  As a system administrator
  I want to log server processing events
  So that I can monitor and debug the system

  Background:
    Given I have a LoggingMiddleware with configuration
      | log_level | log_server_details | log_performance | log_format |
      | info      | true               | true            | json       |

  Scenario: Log processing start
    Given I have 5 servers to process
    When I start processing through the logging middleware
    Then a start event should be logged
    And it should include server count and trace_id
    And server details should be logged if enabled

  Scenario: Log processing completion
    Given I have processed 5 servers
    When I complete processing through the logging middleware
    Then a completion event should be logged
    And it should include duration and performance metrics
    And it should include input/output server counts

  Scenario: Log performance metrics
    Given I have a LoggingMiddleware with log_performance true
    When I process servers through the middleware
    Then performance metrics should be logged
    And it should include servers per second
    And it should include memory usage if available

  Scenario: Handle logging configuration from profile
    Given I have a FullProfile with logging metadata
      | log_level | log_server_details |
      | debug     | false              |
    When I process servers through the logging middleware
    Then the profile logging settings should override defaults
```

## 12. EnrichmentMiddleware

### Scenario: Обогащение данных серверов
```gherkin
Feature: Server Data Enrichment
  As a system
  I want to enrich server data with additional metadata
  So that postprocessors have more information to work with

  Background:
    Given I have an EnrichmentMiddleware with configuration
      | enable_geo_enrichment | enable_performance_enrichment | enable_security_enrichment |
      | true                  | true                          | false                     |

  Scenario: Enrich servers with geographic data
    Given I have servers without geographic metadata
    When I process them through the enrichment middleware
    Then each server should have geographic metadata added
    And it should include country, region, and city information

  Scenario: Enrich servers with performance data
    Given I have servers without performance metadata
    When I process them through the enrichment middleware
    Then each server should have performance metadata added
    And it should include latency and bandwidth indicators

  Scenario: Enrich servers with custom metadata from profile
    Given I have a FullProfile with custom enrichers
    When I process servers through the enrichment middleware
    Then custom metadata should be added based on profile configuration

  Scenario: Handle enrichment timeouts
    Given I have an EnrichmentMiddleware with max_enrichment_time 1 second
    And I have servers that take longer to enrich
    When I process them through the enrichment middleware
    Then enrichment should timeout gracefully
    And servers should still be returned with partial enrichment
```

## 13. ConditionalMiddleware

### Scenario: Условное выполнение middleware
```gherkin
Feature: Conditional Middleware Execution
  As a system
  I want to conditionally execute middleware
  So that I can optimize processing based on conditions

  Background:
    Given I have a ConditionalMiddleware with configuration
      | min_servers | max_servers | execution_mode |
      | 5           | 100         | always         |

  Scenario: Execute based on server count
    Given I have 3 servers (below minimum)
    When I check can_process for the middleware
    Then it should return false

  Scenario: Execute based on required metadata
    Given I have a ConditionalMiddleware with required_metadata ["geo"]
    And I have servers without geo metadata
    When I check can_process for the middleware
    Then it should return false

  Scenario: Execute based on execution mode
    Given I have a ConditionalMiddleware with execution_mode "profile_only"
    And I have no profile
    When I check can_process for the middleware
    Then it should return false
```

## 14. TransformMiddleware

### Scenario: Трансформация данных серверов
```gherkin
Feature: Server Data Transformation
  As a system
  I want to transform server data
  So that I can standardize and normalize server information

  Background:
    Given I have a TransformMiddleware with configuration
      | field_mappings | value_transformers | metadata_enrichers |
      | old_field:new  | port:to_int        | timestamp          |

  Scenario: Apply field mappings
    Given I have servers with old_field values
    When I process them through the transform middleware
    Then old_field should be mapped to new_field
    And the original old_field should be preserved

  Scenario: Apply value transformers
    Given I have servers with port as string "443"
    When I process them through the transform middleware
    Then port should be converted to integer 443

  Scenario: Apply metadata enrichers
    Given I have servers without timestamp metadata
    When I process them through the transform middleware
    Then each server should have timestamp metadata added
```

## 15. Error Handling and Recovery

### Scenario: Обработка ошибок в цепочке
```gherkin
Feature: Error Handling in PostProcessor Chain
  As a system
  I want to handle errors gracefully
  So that the system remains stable and functional

  Background:
    Given I have a PostProcessorChain with error_strategy "continue"

  Scenario: Handle processor failure with continue strategy
    Given I have a processor that will raise an exception
    When I process servers through the chain
    Then the exception should be caught
    And the processor should be logged as failed
    And the chain should continue with remaining processors
    And the final result should contain servers from successful processors

  Scenario: Handle processor failure with fail_fast strategy
    Given I have a PostProcessorChain with error_strategy "fail_fast"
    And I have a processor that will raise an exception
    When I process servers through the chain
    Then the exception should be re-raised
    And processing should stop immediately

  Scenario: Retry failed processors
    Given I have a PostProcessorChain with max_retries 2
    And I have a processor that fails twice then succeeds
    When I process servers through the chain
    Then the processor should be retried twice
    And the final execution should succeed
    And the retry attempts should be logged
```

## 16. Metadata Collection

### Scenario: Сбор метаданных о выполнении
```gherkin
Feature: Execution Metadata Collection
  As a system administrator
  I want to collect metadata about processing
  So that I can monitor and optimize performance

  Background:
    Given I have a PostProcessorChain with collect_metadata true

  Scenario: Collect processor execution metadata
    When I process servers through the chain
    Then execution metadata should be collected
    And it should include start_time and end_time
    And it should include duration calculation
    And it should include processors_executed list
    And it should include processors_failed list
    And it should include processors_skipped list

  Scenario: Collect individual processor metadata
    Given I have processors with custom metadata
    When I process servers through the chain
    Then each processor's get_metadata should be called
    And the metadata should be included in execution metadata
    And it should include input_count and output_count for each processor
```

## 17. Performance Monitoring

### Scenario: Мониторинг производительности
```gherkin
Feature: Performance Monitoring
  As a system administrator
  I want to monitor processing performance
  So that I can identify bottlenecks and optimize

  Background:
    Given I have a LoggingMiddleware with log_performance true

  Scenario: Monitor processing speed
    When I process 100 servers through the middleware
    Then performance metrics should be logged
    And it should include servers per second calculation
    And it should include total processing time

  Scenario: Monitor memory usage
    Given I have a LoggingMiddleware with memory monitoring
    When I process servers through the middleware
    Then memory usage should be logged
    And it should include peak memory usage
    And it should include memory usage per server

  Scenario: Monitor chain performance
    Given I have a PostProcessorChain with performance monitoring
    When I process servers through the chain
    Then each processor's performance should be measured
    And the total chain performance should be calculated
    And performance bottlenecks should be identified
```

## 18. Profile Integration

### Scenario: Интеграция с профилями пользователей
```gherkin
Feature: Profile Integration
  As a user
  I want my preferences to be applied automatically
  So that I get personalized server filtering

  Background:
    Given I have a FullProfile with configuration
      | filters | middleware | logging |
      | enabled | enabled    | enabled |

  Scenario: Apply profile filters to postprocessors
    Given I have a GeoFilterPostProcessor
    And I have a profile with geographic preferences
    When I process servers through the postprocessor with the profile
    Then the profile's geographic settings should be applied
    And the filtering should match user preferences

  Scenario: Apply profile middleware settings
    Given I have a LoggingMiddleware
    And I have a profile with logging preferences
    When I process servers through the middleware with the profile
    Then the profile's logging settings should be applied
    And the logging should match user preferences

  Scenario: Handle missing profile gracefully
    Given I have postprocessors and middleware
    When I process servers without a profile
    Then default configuration should be used
    And processing should complete successfully
```

## 19. Chain Management

### Scenario: Управление цепочками постпроцессоров
```gherkin
Feature: PostProcessor Chain Management
  As a developer
  I want to manage postprocessor chains dynamically
  So that I can create flexible processing pipelines

  Background:
    Given I have a PostProcessorChain with 3 processors

  Scenario: Add processor to chain
    Given I have a new postprocessor
    When I add it to the chain
    Then the chain should have 4 processors
    And the new processor should be at the end

  Scenario: Add processor at specific index
    Given I have a new postprocessor
    When I add it to the chain at index 1
    Then the chain should have 4 processors
    And the new processor should be at index 1

  Scenario: Remove processor by instance
    Given I have a processor in the chain
    When I remove it from the chain
    Then the chain should have 2 processors
    And the removed processor should not be in the chain

  Scenario: Remove processor by name
    Given I have a processor named "GeoFilter" in the chain
    When I remove "GeoFilter" from the chain
    Then the chain should have 2 processors
    And the GeoFilter processor should not be in the chain

  Scenario: Remove processor by index
    Given I have a processor at index 1 in the chain
    When I remove the processor at index 1
    Then the chain should have 2 processors
    And the processor at index 1 should be removed

  Scenario: Get processor by name
    Given I have a processor named "TagFilter" in the chain
    When I get the processor by name "TagFilter"
    Then it should return the TagFilter processor instance
```

## 20. Integration Testing

### Scenario: Полная интеграция Phase 3
```gherkin
Feature: Complete Phase 3 Integration
  As a system
  I want to test the complete Phase 3 architecture
  So that I can ensure all components work together

  Background:
    Given I have a complete Phase 3 setup
      | component           | status  |
      | BasePostProcessor   | ready   |
      | ProfileAware       | ready   |
      | Chainable          | ready   |
      | GeoFilter          | ready   |
      | TagFilter          | ready   |
      | LatencySort        | ready   |
      | PostProcessorChain | ready   |
      | BaseMiddleware     | ready   |
      | LoggingMiddleware  | ready   |
      | EnrichmentMiddleware| ready  |

  Scenario: Complete processing pipeline
    Given I have 20 servers with various characteristics
    And I have a FullProfile with comprehensive settings
    And I have a PostProcessorChain with all postprocessors
    And I have middleware for logging and enrichment
    When I process the servers through the complete pipeline
    Then enrichment middleware should add metadata
    And logging middleware should log all events
    And geo filtering should filter by location
    And tag filtering should filter by tags
    And latency sorting should sort by performance
    And the final result should be optimized servers
    And all metadata should be collected
    And performance metrics should be available

  Scenario: Error recovery in complete pipeline
    Given I have a complete processing pipeline
    And one component will fail during processing
    When I process servers through the pipeline
    Then the failure should be handled gracefully
    And the pipeline should continue where possible
    And error information should be logged
    And partial results should be returned
```

## 21. Export Integration with Phase 3

### Scenario: Интеграция с экспортом в sing-box формат
```gherkin
Feature: Phase 3 Export Integration
  As a user
  I want the postprocessor chain results to be reflected in exported configuration
  So that my filtering and sorting preferences are preserved

  Background:
    Given I have a PostProcessorChain with configuration
      | execution_mode | error_strategy | collect_metadata |
      | sequential     | continue       | true             |
    And I have processors [GeoFilter, TagFilter, LatencySort]
    And I have a SingboxExporter configured

  Scenario: Export filtered and sorted servers to sing-box
    Given I have 20 servers with various countries, tags, and latencies
    And I have a FullProfile with filtering preferences
    When I process the servers through the PostProcessorChain
    And I export the result to sing-box format
    Then the outbounds should contain only servers that passed all filters
    And the outbounds should be sorted by latency (fastest first)
    And each outbound should preserve the original server metadata
    And the export should include processing metadata

  Scenario: Export with geographic filtering applied
    Given I have servers from countries ["US", "CA", "UK", "CN", "DE"]
    And I have a GeoFilterPostProcessor with allowed_countries ["US", "CA", "UK"]
    When I process the servers and export to sing-box
    Then the outbounds should only contain servers from US, CA, and UK
    And servers from CN and DE should be excluded
    And the export metadata should indicate geographic filtering was applied

  Scenario: Export with tag filtering applied
    Given I have servers with tags ["Premium", "Basic", "Blocked", "Fast"]
    And I have a TagFilterPostProcessor with include_tags ["Premium", "Fast"]
    When I process the servers and export to sing-box
    Then the outbounds should only contain servers with Premium or Fast tags
    And servers with Basic or Blocked tags should be excluded
    And the export metadata should indicate tag filtering was applied

  Scenario: Export with latency sorting applied
    Given I have servers with latencies [300, 150, 450, 100, 600]
    And I have a LatencySortPostProcessor with sort_order "asc"
    When I process the servers and export to sing-box
    Then the outbounds should be ordered by latency: [100, 150, 300, 450, 600]
    And each outbound should have latency_ms metadata preserved
    And the export metadata should indicate latency sorting was applied

  Scenario: Export with complete chain processing
    Given I have 15 servers with mixed characteristics
    And I have a PostProcessorChain with GeoFilter, TagFilter, LatencySort
    And I have a FullProfile with comprehensive filtering settings
    When I process the servers through the complete chain
    And I export the result to sing-box format
    Then the outbounds should reflect all filtering and sorting
    And the export should include chain execution metadata
    And the export should include performance metrics
    And the export should be valid sing-box configuration

  Scenario: Handle export with no servers after filtering
    Given I have servers that will be filtered out by all processors
    When I process the servers through the PostProcessorChain
    And I export the result to sing-box format
    Then the outbounds should be empty
    And the export should include a warning about no servers
    And the export should still be valid sing-box configuration
```

## 22. CLI Profile Integration

### Scenario: Интеграция CLI с профилями Phase 3
```gherkin
Feature: CLI Profile Integration with Phase 3
  As a user
  I want to use CLI commands with Phase 3 postprocessor chains
  So that I can easily apply complex processing pipelines

  Background:
    Given I have a profile file "myprofile.json" with Phase 3 configuration
    And I have a subscription file "subscription.txt" with server data

  Scenario: Generate configuration with profile-based postprocessor chain
    Given I have a profile with postprocessor chain configuration
      | processors | execution_mode | error_strategy |
      | geo_filter | sequential     | continue       |
      | tag_filter | sequential     | continue       |
      | latency_sort| sequential    | continue       |
    When I run "sb generate --profile myprofile.json --input subscription.txt"
    Then the PostProcessorChain should be configured from the profile
    And the servers should be processed through the configured chain
    And the output should be a valid sing-box configuration
    And the output should reflect the profile's filtering preferences

  Scenario: Apply profile with middleware configuration
    Given I have a profile with middleware settings
      | middleware | logging | enrichment |
      | enabled    | true    | true       |
    When I run "sb generate --profile myprofile.json --input subscription.txt"
    Then the LoggingMiddleware should be enabled
    And the EnrichmentMiddleware should be enabled
    And the processing should be logged
    And the servers should be enriched with metadata

  Scenario: Use profile with custom postprocessor configuration
    Given I have a profile with custom postprocessor settings
      | postprocessor | config_key | config_value |
      | geo_filter    | allowed_countries | US,CA,UK |
      | tag_filter    | include_tags | Premium,Fast |
      | latency_sort  | sort_order | asc |
    When I run "sb generate --profile myprofile.json --input subscription.txt"
    Then the GeoFilterPostProcessor should use allowed_countries ["US", "CA", "UK"]
    And the TagFilterPostProcessor should use include_tags ["Premium", "Fast"]
    And the LatencySortPostProcessor should use sort_order "asc"

  Scenario: Handle profile with missing Phase 3 configuration
    Given I have a profile without Phase 3 postprocessor configuration
    When I run "sb generate --profile myprofile.json --input subscription.txt"
    Then default postprocessor configuration should be used
    And the processing should complete successfully
    And a warning should be logged about missing Phase 3 config

  Scenario: Validate profile configuration before processing
    Given I have a profile with invalid postprocessor configuration
    When I run "sb generate --profile myprofile.json --input subscription.txt"
    Then the profile should be validated
    And invalid configuration should be reported
    And processing should stop with appropriate error message
```

## 23. Comprehensive Edge Case Handling

### Scenario: Обработка граничных случаев
```gherkin
Feature: Comprehensive Edge Case Handling
  As a system
  I want to handle edge cases gracefully
  So that the system remains stable under all conditions

  Background:
    Given I have a PostProcessorChain with error_strategy "continue"

  Scenario: Handle servers with missing latency data
    Given I have servers without latency_ms metadata
    And I have a LatencySortPostProcessor with fallback_latency 1000
    When I process the servers through the latency sorter
    Then fallback_latency should be used for servers without latency data
    And servers should be sorted with fallback values
    And the fallback usage should be logged

  Scenario: Handle servers with empty tags
    Given I have servers with empty or null tags
    And I have a TagFilterPostProcessor with require_tags false
    When I process the servers through the tag filter
    Then servers without tags should be included (fallback mode)
    And the fallback behavior should be logged

  Scenario: Handle servers with missing geographic data
    Given I have servers without country or geo metadata
    And I have a GeoFilterPostProcessor with fallback_mode "allow_all"
    When I process the servers through the geo filter
    Then servers without geographic data should be included
    And the fallback behavior should be logged

  Scenario: Handle enrichment timeout with partial data
    Given I have an EnrichmentMiddleware with max_enrichment_time 1 second
    And I have servers that take 2 seconds to enrich
    When I process the servers through the enrichment middleware
    Then enrichment should timeout after 1 second
    And servers should be returned with partial enrichment
    And the timeout should be logged
    And partial enrichment should be indicated in metadata

  Scenario: Handle chain with all processors failing
    Given I have a PostProcessorChain where all processors will fail
    And I have error_strategy "continue"
    When I process servers through the chain
    Then all processors should be logged as failed
    And the original servers should be returned
    And the failure should be logged with details

  Scenario: Handle memory exhaustion during processing
    Given I have a large number of servers that may exhaust memory
    And I have memory monitoring enabled
    When I process the servers through the chain
    Then memory usage should be monitored
    And if memory limit is reached, processing should be optimized
    And memory usage should be logged

  Scenario: Handle network timeouts during enrichment
    Given I have an EnrichmentMiddleware that makes network calls
    And the network calls may timeout
    When I process servers through the enrichment middleware
    Then network timeouts should be handled gracefully
    And servers should be returned with available enrichment
    And timeout errors should be logged

  Scenario: Handle invalid server data
    Given I have servers with invalid or corrupted data
    When I process the servers through the chain
    Then invalid servers should be filtered out or corrected
    And the validation errors should be logged
    And processing should continue with valid servers
```

## 24. Performance and Resource Management

### Scenario: Управление производительностью и ресурсами
```gherkin
Feature: Performance and Resource Management
  As a system administrator
  I want to monitor and manage performance and resources
  So that the system operates efficiently under all loads

  Background:
    Given I have a PostProcessorChain with performance monitoring enabled

  Scenario: Monitor processing performance under load
    Given I have 1000 servers to process
    And I have performance monitoring enabled
    When I process the servers through the chain
    Then processing time should be measured
    And memory usage should be tracked
    And CPU usage should be monitored
    And performance metrics should be logged
    And bottlenecks should be identified

  Scenario: Handle large server lists efficiently
    Given I have 10000 servers to process
    And I have memory optimization enabled
    When I process the servers through the chain
    Then memory usage should be optimized
    And processing should be batched if necessary
    And the system should not run out of memory
    And processing should complete successfully

  Scenario: Optimize parallel processing
    Given I have a PostProcessorChain with parallel execution
    And I have 4 CPU cores available
    When I process servers through the chain
    Then parallel workers should be limited to available cores
    And CPU usage should be optimized
    And parallel processing should improve performance

  Scenario: Handle resource cleanup
    Given I have middleware that uses external resources
    When I process servers through the middleware
    Then external resources should be properly cleaned up
    And memory should be freed after processing
    And file handles should be closed
    And network connections should be closed

  Scenario: Monitor chain execution efficiency
    Given I have a PostProcessorChain with multiple processors
    When I process servers through the chain
    Then each processor's performance should be measured
    And the slowest processor should be identified
    And performance recommendations should be generated
    And the metrics should be stored for analysis
```

## 25. Integration Testing Scenarios

### Scenario: Полное тестирование интеграции Phase 3
```gherkin
Feature: Complete Phase 3 Integration Testing
  As a quality assurance engineer
  I want to test the complete Phase 3 integration
  So that I can ensure all components work together correctly

  Background:
    Given I have a complete Phase 3 test environment
      | component           | status  | version |
      | BasePostProcessor   | ready   | 1.0     |
      | ProfileAware       | ready   | 1.0     |
      | Chainable          | ready   | 1.0     |
      | GeoFilter          | ready   | 1.0     |
      | TagFilter          | ready   | 1.0     |
      | LatencySort        | ready   | 1.0     |
      | PostProcessorChain | ready   | 1.0     |
      | BaseMiddleware     | ready   | 1.0     |
      | LoggingMiddleware  | ready   | 1.0     |
      | EnrichmentMiddleware| ready  | 1.0     |
      | SingboxExporter    | ready   | 1.0     |

  Scenario: End-to-end processing with real subscription data
    Given I have a real subscription file with 500 servers
    And I have a comprehensive profile with all Phase 3 features
    And I have a PostProcessorChain with all postprocessors
    And I have middleware for logging and enrichment
    When I process the subscription through the complete pipeline
    Then enrichment middleware should add metadata to all servers
    And logging middleware should log all processing events
    And geo filtering should filter servers by location
    And tag filtering should filter servers by tags
    And latency sorting should sort servers by performance
    And the final result should be optimized servers
    And all metadata should be collected and preserved
    And performance metrics should be available
    And the export should be valid sing-box configuration
    And the export should reflect all processing results

  Scenario: Stress testing with large datasets
    Given I have a subscription with 10000 servers
    And I have a profile with complex filtering rules
    And I have limited system resources (4GB RAM, 2 CPU cores)
    When I process the subscription through Phase 3 pipeline
    Then the system should handle the load without crashing
    And memory usage should stay within limits
    And processing should complete within reasonable time
    And all filtering and sorting should be applied correctly
    And the result should be consistent with smaller datasets

  Scenario: Error recovery and resilience testing
    Given I have a subscription with some corrupted server data
    And I have a profile that will cause some processors to fail
    And I have error handling enabled
    When I process the subscription through Phase 3 pipeline
    Then corrupted data should be handled gracefully
    And failed processors should be logged and skipped
    And processing should continue with valid data
    And partial results should be returned
    And error information should be preserved for debugging

  Scenario: Profile configuration validation testing
    Given I have various profile configurations (valid and invalid)
    When I attempt to process subscriptions with these profiles
    Then valid profiles should work correctly
    And invalid profiles should be rejected with clear error messages
    And default configurations should be used when appropriate
    And profile validation should prevent processing errors

  Scenario: Performance regression testing
    Given I have a baseline performance measurement
    And I have made changes to Phase 3 components
    When I run the same processing pipeline
    Then performance should not degrade significantly
    And all functionality should work as expected
    And performance metrics should be comparable to baseline
```

## 26. Validation and Quality Assurance

### Scenario: Валидация и обеспечение качества
```gherkin
Feature: Validation and Quality Assurance
  As a quality assurance engineer
  I want to validate Phase 3 components and outputs
  So that I can ensure high quality and reliability

  Background:
    Given I have validation tools and test data sets

  Scenario: Validate postprocessor output quality
    Given I have a set of test servers with known characteristics
    When I process them through each postprocessor individually
    Then the output should meet quality criteria
    And filtering should be accurate and complete
    And sorting should be correct and stable
    And metadata should be preserved and enhanced

  Scenario: Validate chain execution consistency
    Given I have a PostProcessorChain with multiple processors
    When I run the same input through the chain multiple times
    Then the results should be consistent
    And the execution order should be predictable
    And metadata should be consistent across runs

  Scenario: Validate export format compliance
    Given I have processed servers through Phase 3 pipeline
    When I export to sing-box format
    Then the export should be valid JSON
    And the export should conform to sing-box schema
    And the export should be loadable by sing-box
    And all server configurations should be valid

  Scenario: Validate profile configuration integrity
    Given I have various profile configurations
    When I load and apply these profiles
    Then valid profiles should load without errors
    And invalid profiles should be rejected with clear messages
    And profile settings should be applied correctly
    And default values should be used appropriately

  Scenario: Validate error handling effectiveness
    Given I have test scenarios that will trigger various errors
    When I run these scenarios through Phase 3 pipeline
    Then errors should be caught and handled appropriately
    And error messages should be clear and actionable
    And system stability should be maintained
    And partial results should be returned when possible

  Scenario: Validate performance benchmarks
    Given I have performance benchmarks for Phase 3 components
    When I run the benchmarks
    Then performance should meet or exceed benchmarks
    And resource usage should be within acceptable limits
    And scalability should be demonstrated
    And performance should be consistent across runs
```

## Заключение

Эти Gherkin сценарии обеспечивают **полное покрытие Phase 3 архитектуры**, включая:

✅ **Полное покрытие компонентов** (BasePostProcessor, ProfileAware, Chainable, все конкретные реализации)
✅ **Middleware система** (BaseMiddleware, ProfileAware, Chainable, Conditional, Transform, Logging, Enrichment)
✅ **Chain execution** (sequential, parallel, conditional с различными стратегиями)
✅ **Error handling** (continue, fail_fast, retry, graceful degradation)
✅ **Profile integration** (фильтры, middleware настройки, логирование)
✅ **Export integration** (sing-box формат, сохранение результатов обработки)
✅ **CLI integration** (профили, команды, валидация)
✅ **Edge cases** (отсутствующие данные, таймауты, ошибки, граничные условия)
✅ **Performance monitoring** (метрики, ресурсы, оптимизация)
✅ **Quality assurance** (валидация, тестирование, бенчмарки)

**Phase 3 полностью покрыта и готова к коммиту!** 🚀 