Feature: Interactive Wizard Scenarios
  As a new user of sboxmgr CLI
  I want to use an interactive wizard
  So that I can set up sboxmgr without knowing all the commands

  Background:
    Given I have sboxmgr CLI installed
    And I am a new user

  Scenario: Complete wizard setup
    Given I run "sboxctl wizard setup"
    When I am prompted for subscription URL
    Then I should see "Enter subscription URL:"
    And I should see helpful description
    When I enter "https://example.com/subscription"
    And I am prompted for inbound types
    Then I should see "Select inbound types:"
    And I should see options "[1] TUN (VPN-like), [2] SOCKS proxy, [3] HTTP proxy, [4] None"
    When I select "1,2"
    And I am prompted for TUN configuration
    Then I should see "TUN network address:"
    When I enter "10.0.0.1/24"
    And I am prompted for SOCKS configuration
    Then I should see "SOCKS port:"
    When I enter "1080"
    And I am prompted for output configuration
    Then I should see "Output format:"
    And I should see options "[1] JSON, [2] TOML"
    When I select "1"
    And I am prompted for output file
    Then I should see "Output file:"
    When I enter "config.json"
    Then I should see configuration summary
    And I should see "Configuration saved successfully"
    And a configuration file should be created

  Scenario: Wizard with default values
    Given I run "sboxctl wizard setup"
    When I am prompted for subscription URL
    And I press Enter without input
    Then I should see error message
    And I should be prompted again
    When I enter "https://example.com/subscription"
    And I am prompted for inbound types
    And I press Enter without input
    Then default value "tun" should be selected
    And I should continue to next step

  Scenario: Wizard quick start
    Given I run "sboxctl wizard quick-start"
    When I am prompted for subscription URL
    Then I should see simplified prompts
    When I enter "https://example.com/subscription"
    Then default configuration should be applied
    And I should see "Quick setup completed"
    And a basic configuration should be created

  Scenario: Cancel wizard
    Given I run "sboxctl wizard setup"
    When I am prompted for subscription URL
    And I enter "cancel"
    Then the wizard should exit
    And no configuration should be created
    And I should see "Wizard cancelled"

  Scenario: Wizard validation
    Given I run "sboxctl wizard setup"
    When I am prompted for subscription URL
    And I enter "invalid-url"
    Then I should see validation error
    And I should be prompted again
    When I am prompted for port
    And I enter "99999"
    Then I should see validation error
    And I should be prompted again

  Scenario: Wizard in non-interactive environment
    Given I am running in a non-interactive environment
    When I run "sboxctl wizard setup"
    Then I should see error message
    And the error should explain that wizard requires interactive terminal
    And the command should exit with error code

  Scenario: Wizard help
    Given I run "sboxctl wizard --help"
    Then I should see wizard subcommands
    And I should see "setup" subcommand
    And I should see "quick-start" subcommand
    And I should see descriptions for each subcommand

  Scenario: Wizard with existing configuration
    Given I have existing configuration
    When I run "sboxctl wizard setup"
    Then I should see warning about existing configuration
    And I should be asked if I want to overwrite
    When I choose to overwrite
    Then the wizard should continue
    When I choose not to overwrite
    Then the wizard should exit
    And existing configuration should be preserved
