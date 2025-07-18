Feature: Power User Optimization Scenarios
  As an experienced user of sboxmgr CLI
  I want to use power user features
  So that I can work efficiently and automate tasks

  Background:
    Given I have sboxmgr CLI installed
    And I am an experienced user
    And I have active configuration "production"

  Scenario: Use global yes flag
    Given I want to delete configuration without confirmation
    When I run "sboxctl --yes config delete old-config"
    Then the command should execute immediately
    And I should not see confirmation prompts
    When I run "sboxctl --yes exclusions clear"
    Then the command should execute immediately
    And I should not see confirmation prompts

  Scenario: Use global verbose flag
    Given I want detailed output
    When I run "sboxctl --verbose subscription list"
    Then I should see detailed server information
    And I should see policy evaluation details
    And I should see network request details
    When I run "sboxctl --verbose config list"
    Then I should see detailed configuration information
    And I should see file paths and timestamps

  Scenario: Use default configuration
    Given I have active configuration "production"
    When I run "sboxctl export generate"
    Then the command should use default URL from active config
    And the command should use default inbound types from active config
    And I should see "Using active configuration: production"
    When I run "sboxctl subscription list"
    Then the command should use default URL from active config

  Scenario: Use JSON output for automation
    Given I want to parse output with scripts
    When I run "sboxctl subscription list --format json"
    Then I should see valid JSON output
    And the output should contain "status" field
    And the output should contain "data" field
    And the output should contain server array
    When I run "sboxctl config list --format json"
    Then I should see valid JSON output
    And the output should contain configuration array
    When I run "sboxctl policy list --format json"
    Then I should see valid JSON output
    And the output should contain policy array

  Scenario: Use update command alias
    Given I want to update configuration and reload
    When I run "sboxctl update"
    Then the command should export configuration
    And the command should reload sing-box service
    And I should see "Configuration updated and reloaded"
    When I run "sboxctl update --dry-run"
    Then the command should only validate configuration
    And I should see "Configuration validated successfully"

  Scenario: Use diagnose command
    Given I want to check system health
    When I run "sboxctl diagnose"
    Then I should see subscription connectivity check
    And I should see configuration validation
    And I should see network connectivity check
    And I should see overall health status
    When I run "sboxctl diagnose subscription"
    Then I should see detailed subscription diagnostics
    When I run "sboxctl diagnose config"
    Then I should see detailed configuration diagnostics
    When I run "sboxctl diagnose network"
    Then I should see detailed network diagnostics

  Scenario: Use batch operations
    Given I want to perform multiple operations
    When I run "sboxctl policy enable GeoPolicy,ProtocolPolicy"
    Then both policies should be enabled
    And I should see success message for each policy
    When I run "sboxctl exclusions add 1,2,3 --reason 'Slow nodes'"
    Then multiple servers should be excluded
    And I should see success message for each server

  Scenario: Use client profile for complex configuration
    Given I have a client profile file "complex-profile.json"
    When I run "sboxctl export generate --client-profile complex-profile.json"
    Then the command should use profile configuration
    And I should not need to specify individual inbound parameters
    And the output should match profile settings

  Scenario: Use version command
    Given I want to check version information
    When I run "sboxctl --version"
    Then I should see sboxmgr version
    And I should see Python version
    And I should see sing-box version
    And the command should exit immediately
    When I run "sboxctl version"
    Then I should see detailed version information
    And I should see active configuration
    And I should see system information

  Scenario: Use exit codes for automation
    Given I want to check command success in scripts
    When I run "sboxctl subscription list"
    Then the command should exit with code 0
    When I run "sboxctl subscription list --url invalid-url"
    Then the command should exit with code 4 (network error)
    When I run "sboxctl config apply non-existent-config"
    Then the command should exit with code 6 (not found)
    When I run "sboxctl export generate --url invalid-url"
    Then the command should exit with code 2 (validation error)

  Scenario: Use non-interactive mode
    Given I am running in CI/CD environment
    When I run "sboxctl export generate --url https://example.com/sub"
    Then the command should not show interactive prompts
    And the command should use default values
    And the command should exit with appropriate code if validation fails

  Scenario: Use bash completion
    Given I have bash completion installed
    When I type "sboxctl " and press Tab
    Then I should see available commands
    When I type "sboxctl subscription " and press Tab
    Then I should see subscription subcommands
    When I type "sboxctl export " and press Tab
    Then I should see export subcommands
