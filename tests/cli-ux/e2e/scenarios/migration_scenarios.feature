Feature: CLI Migration Scenarios
  As a user of sboxmgr CLI
  I want to migrate from old command structure to new one
  So that I can use improved UX while maintaining backward compatibility

  Background:
    Given I have sboxmgr CLI installed
    And I am familiar with old command structure

  Scenario: Migrate from list-servers to subscription list
    Given I have a subscription URL "https://example.com/subscription"
    When I run "sboxctl list-servers --url https://example.com/subscription"
    Then I should see a deprecation warning
    And the command should work as before
    And I should see server list output
    When I run "sboxctl subscription list --url https://example.com/subscription"
    Then the command should work without warnings
    And I should see the same server list output

  Scenario: Migrate from exclusions to subscription exclusions
    Given I have existing exclusions configured
    When I run "sboxctl exclusions"
    Then I should see a deprecation warning
    And the command should work as before
    When I run "sboxctl subscription exclusions list"
    Then the command should work without warnings
    And I should see the same exclusions output

  Scenario: Migrate from export to export generate
    Given I have a subscription URL "https://example.com/subscription"
    When I run "sboxctl export --url https://example.com/subscription --output config.json"
    Then I should see a deprecation warning
    And the command should work as before
    When I run "sboxctl export generate --url https://example.com/subscription --output config.json"
    Then the command should work without warnings
    And I should see the same output

  Scenario: Use new wizard command
    Given I am a new user
    When I run "sboxctl wizard"
    Then I should see interactive setup wizard
    And I should be prompted for subscription URL
    And I should be prompted for inbound types
    And I should be prompted for configuration options
    When I complete the wizard
    Then a configuration should be created
    And I should see success message

  Scenario: Use new diagnose command
    Given I have sboxmgr configured
    When I run "sboxctl diagnose"
    Then I should see system health check
    And I should see subscription status
    And I should see configuration status
    And I should see network connectivity status

  Scenario: Use global flags
    Given I want to skip confirmations
    When I run "sboxctl --yes config delete old-config"
    Then the command should execute without confirmation prompts
    When I run "sboxctl --verbose subscription list"
    Then I should see detailed output
    When I run "sboxctl --version"
    Then I should see version information
    And the command should exit immediately

  Scenario: Use JSON output format
    Given I want machine-readable output
    When I run "sboxctl subscription list --format json"
    Then I should see valid JSON output
    And the output should contain server data
    When I run "sboxctl config list --format json"
    Then I should see valid JSON output
    And the output should contain configuration data
    When I run "sboxctl policy list --format json"
    Then I should see valid JSON output
    And the output should contain policy data

  Scenario: Interactive prompts in non-TTY environment
    Given I am running in a non-interactive environment
    When I run "sboxctl export" without required parameters
    Then I should see an error message
    And the error should explain required parameters
    And the command should not hang waiting for input

  Scenario: Help text improvements
    When I run "sboxctl --help"
    Then I should see organized command groups
    And I should see clear descriptions
    When I run "sboxctl subscription --help"
    Then I should see subscription subcommands
    And I should see clear descriptions for each subcommand
    When I run "sboxctl export --help"
    Then I should see export subcommands
    And I should see organized option groups
