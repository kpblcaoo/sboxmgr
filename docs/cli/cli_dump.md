# SboxMgr CLI Commands Reference

This document contains all available CLI commands and their help outputs.

## 🔹 Main CLI Help

```

 Usage: python -m src.sboxmgr.cli.main [OPTIONS] COMMAND [ARGS]...

 Show help information


╭─ Options ───────────────────────────────────────────────────────────────────────────────────╮
│ --version             -V        Show version and exit                                       │
│ --yes                 -y        Skip confirmation prompts and use default values            │
│ --verbose             -v        Verbose output with additional details                      │
│ --install-completion            Install completion for the current shell.                   │
│ --show-completion               Show completion for the current shell, to copy it or        │
│                                 customize the installation.                                 │
│ --help                          Show this message and exit.                                 │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ──────────────────────────────────────────────────────────────────────────────────╮
│ lang              Manage CLI internationalization language settings.                        │
│ plugin-template   Generate a plugin template                                                │
│                   (fetcher/parser/validator/exporter/postprocessor/parsed_validator) with   │
│                   test and Google-style docstring.                                          │
│ tui               Launch Text User Interface (TUI) mode.                                    │
│ config            Configuration management commands                                         │
│ subscription      Manage subscriptions and servers                                          │
│ profile           Manage FullProfile configurations                                         │
│ export            Export configurations and profiles                                        │
│ policy            Policy management commands                                                │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯


```

## 🔹 Command: `sboxctl lang`

```

 Usage: python -m src.sboxmgr.cli.main lang [OPTIONS]

 Manage CLI internationalization language settings.

 Provides language management functionality including displaying current language, listing
 available languages, and persistently setting the preferred language for CLI output.
 The language priority is: 1. SBOXMGR_LANG environment variable 2. Configuration file setting
 (~/.sboxmgr/config.toml) 3. System locale (LANG) 4. Default (English)
 Args:     set_lang: Language code to set as default (e.g., 'en', 'ru', 'de').
 Raises:     typer.Exit: If specified language is not available or config write fails.

╭─ Options ───────────────────────────────────────────────────────────────────────────────────╮
│ --set   -s      TEXT  Set CLI language code (e.g., en, ru). [default: None]                 │
│ --help                Show this message and exit.                                           │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯


```

## 🔹 Command: `sboxctl test`

```
Error running command: Command '['/usr/bin/python', '-m', 'src.sboxmgr.cli.main', 'test', '--help']' returned non-zero exit status 2.
Usage: python -m src.sboxmgr.cli.main [OPTIONS] COMMAND [ARGS]...
Try 'python -m src.sboxmgr.cli.main --help' for help.
╭─ Error ─────────────────────────────────────────────────────────────────────────────────────╮
│ No such command 'test'.                                                                     │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯

```

## 🔹 Command: `sboxctl tui`

```

 Usage: python -m src.sboxmgr.cli.main tui [OPTIONS]

 Launch Text User Interface (TUI) mode.

 Opens an interactive text-based interface for managing subscriptions and generating
 configurations. The TUI provides a user-friendly way to interact with sboxmgr without
 memorizing CLI commands.
 Features: - Context-aware interface that adapts to your current setup - Step-by-step
 onboarding for new users - Visual server management with exclusion controls - Real-time
 validation and error handling - Keyboard shortcuts for efficient navigation
 Args:     debug: Debug level (0=off, 1=info, 2=verbose, 3=trace)     profile: Profile name to
 use (defaults to current profile)
 Examples:     sboxctl tui                    # Launch TUI with default settings     sboxctl
 tui --debug 1          # Launch with debug info     sboxctl tui --profile work     # Launch
 with specific profile

╭─ Options ───────────────────────────────────────────────────────────────────────────────────╮
│ --debug    -d      INTEGER RANGE [0<=x<=3]  Debug level (0-3) [default: 0]                  │
│ --profile  -p      TEXT                     Profile name to use [default: None]             │
│ --help                                      Show this message and exit.                     │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯


```

## 🔹 Command: `sboxctl config`

```

 Usage: python -m src.sboxmgr.cli.main config [OPTIONS] COMMAND [ARGS]...

 Configuration management commands


╭─ Options ───────────────────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                                 │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ──────────────────────────────────────────────────────────────────────────────────╮
│ list       List available configurations.                                                   │
│ create     Create a new configuration.                                                      │
│ apply      Apply a configuration.                                                           │
│ validate   Validate a configuration file.                                                   │
│ migrate    Migrate configuration from JSON to TOML format.                                  │
│ switch     Switch to a different configuration.                                             │
│ edit       Edit a configuration file.                                                       │
│ status     Show current active configuration status.                                        │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯


```

### 🔸 Subcommand: `sboxctl config list`

```

 Usage: python -m src.sboxmgr.cli.main config list [OPTIONS]

 List available configurations.


╭─ Options ───────────────────────────────────────────────────────────────────────────────────╮
│ --format           TEXT  Output format: table, json [default: table]                        │
│ --directory        TEXT  Config directory [default: None]                                   │
│ --help                   Show this message and exit.                                        │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯


```

---

### 🔸 Subcommand: `sboxctl config create`

```

 Usage: python -m src.sboxmgr.cli.main config create [OPTIONS] NAME

 Create a new configuration.


╭─ Arguments ─────────────────────────────────────────────────────────────────────────────────╮
│ *    name      TEXT  Configuration name [default: None] [required]                          │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ───────────────────────────────────────────────────────────────────────────────────╮
│ --description        TEXT  Configuration description [default: None]                        │
│ --format             TEXT  Output format: toml, json [default: toml]                        │
│ --directory          TEXT  Config directory [default: None]                                 │
│ --help                     Show this message and exit.                                      │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯


```

---

### 🔸 Subcommand: `sboxctl config apply`

```

 Usage: python -m src.sboxmgr.cli.main config apply [OPTIONS] CONFIG_FILE

 Apply a configuration.


╭─ Arguments ─────────────────────────────────────────────────────────────────────────────────╮
│ *    config_file      TEXT  Configuration file path [default: None] [required]              │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ───────────────────────────────────────────────────────────────────────────────────╮
│ --dry-run          Validate without applying                                                │
│ --help             Show this message and exit.                                              │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯


```

---

### 🔸 Subcommand: `sboxctl config validate`

```

 Usage: python -m src.sboxmgr.cli.main config validate [OPTIONS] CONFIG_FILE

 Validate a configuration file.


╭─ Arguments ─────────────────────────────────────────────────────────────────────────────────╮
│ *    config_file      TEXT  Configuration file path [default: None] [required]              │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ───────────────────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                                 │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯


```

---

### 🔸 Subcommand: `sboxctl config migrate`

```

 Usage: python -m src.sboxmgr.cli.main config migrate [OPTIONS] SOURCE

 Migrate configuration from JSON to TOML format.


╭─ Arguments ─────────────────────────────────────────────────────────────────────────────────╮
│ *    source      TEXT  Source configuration file (JSON) [default: None] [required]          │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ───────────────────────────────────────────────────────────────────────────────────╮
│ --target        TEXT  Target file path (TOML) [default: None]                               │
│ --format        TEXT  Target format: toml [default: toml]                                   │
│ --help                Show this message and exit.                                           │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯


```

---

### 🔸 Subcommand: `sboxctl config switch`

```

 Usage: python -m src.sboxmgr.cli.main config switch [OPTIONS] CONFIG_NAME

 Switch to a different configuration.


╭─ Arguments ─────────────────────────────────────────────────────────────────────────────────╮
│ *    config_name      TEXT  Configuration name to switch to [default: None] [required]      │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ───────────────────────────────────────────────────────────────────────────────────╮
│ --directory        TEXT  Config directory [default: None]                                   │
│ --help                   Show this message and exit.                                        │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯


```

---

### 🔸 Subcommand: `sboxctl config edit`

```

 Usage: python -m src.sboxmgr.cli.main config edit [OPTIONS] CONFIG_NAME

 Edit a configuration file.


╭─ Arguments ─────────────────────────────────────────────────────────────────────────────────╮
│ *    config_name      TEXT  Configuration name to edit [default: None] [required]           │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ───────────────────────────────────────────────────────────────────────────────────╮
│ --editor           TEXT  Editor command [default: None]                                     │
│ --directory        TEXT  Config directory [default: None]                                   │
│ --help                   Show this message and exit.                                        │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯


```

---

### 🔸 Subcommand: `sboxctl config status`

```

 Usage: python -m src.sboxmgr.cli.main config status [OPTIONS]

 Show current active configuration status.


╭─ Options ───────────────────────────────────────────────────────────────────────────────────╮
│ --directory        TEXT  Config directory [default: None]                                   │
│ --help                   Show this message and exit.                                        │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯


```

---

## 🔹 Command: `sboxctl subscription`

```

 Usage: python -m src.sboxmgr.cli.main subscription [OPTIONS] COMMAND [ARGS]...

 Manage subscriptions and servers


╭─ Options ───────────────────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                                 │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ──────────────────────────────────────────────────────────────────────────────────╮
│ list         List all available servers from subscription.                                  │
│ exclusions   Manage server exclusions                                                       │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯


```

### 🔸 Subcommand: `sboxctl subscription list`

```

 Usage: python -m src.sboxmgr.cli.main subscription list [OPTIONS]

 List all available servers from subscription.


╭─ Options ───────────────────────────────────────────────────────────────────────────────────╮
│ *  --url             -u      TEXT     Subscription URL to list servers from                 │
│                                       [env var: SBOXMGR_URL, SINGBOX_URL, TEST_URL]         │
│                                       [default: None]                                       │
│                                       [required]                                            │
│    --debug           -d      INTEGER  Debug verbosity level (0-2) [default: 0]              │
│    --user-agent              TEXT     Override User-Agent for subscription fetcher          │
│                                       (default: ClashMeta/1.0)                              │
│                                       [default: ClashMeta/1.0]                              │
│    --no-user-agent                    Do not send User-Agent header at all                  │
│    --format                  TEXT     Force specific format: auto, base64, json, uri_list,  │
│                                       clash                                                 │
│                                       [default: None]                                       │
│    --policy-details  -P               Show policy evaluation details for each server        │
│    --output-format           TEXT     Output format: table, json [default: table]           │
│    --help                             Show this message and exit.                           │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯


```

---

### 🔸 Subcommand: `sboxctl subscription exclusions`

```

 Usage: python -m src.sboxmgr.cli.main subscription exclusions
            [OPTIONS] COMMAND [ARGS]...

 Manage server exclusions


╭─ Options ───────────────────────────────────────────────────────────────────────────────────╮
│ --url    -u      TEXT     Config subscription URL                                           │
│                           [env var: SBOXMGR_URL, SINGBOX_URL, TEST_URL]                     │
│                           [default: None]                                                   │
│ --debug  -d      INTEGER  Debug level: 0=min, 1=info, 2=debug [default: 0]                  │
│ --yes    -y               Skip confirmation prompts                                         │
│ --help                    Show this message and exit.                                       │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ──────────────────────────────────────────────────────────────────────────────────╮
│ list           List current exclusions.                                                     │
│ add            Add servers to exclusions.                                                   │
│ remove         Remove servers from exclusions.                                              │
│ list-servers   List all available servers with their exclusion status.                      │
│ clear          Clear all exclusions.                                                        │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯


```

---

## 🔹 Command: `sboxctl profile`

```

 Usage: python -m src.sboxmgr.cli.main profile [OPTIONS] COMMAND [ARGS]...

 Manage FullProfile configurations


╭─ Options ───────────────────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                                 │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ──────────────────────────────────────────────────────────────────────────────────╮
│ list         List available profiles.                                                       │
│ show         Show profile contents.                                                         │
│ new          Create a new profile.                                                          │
│ edit         Edit profile in external editor.                                               │
│ validate     Validate profile configuration.                                                │
│ set-active   Set active profile.                                                            │
│ delete       Delete profile.                                                                │
│ import       Import profile from file.                                                      │
│ export       Export profile to file.                                                        │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯


```

### 🔸 Subcommand: `sboxctl profile list`

```

 Usage: python -m src.sboxmgr.cli.main profile list [OPTIONS]

 List available profiles.

 Shows all available FullProfile configurations with their status and details. Profiles are
 stored in ~/.config/sboxmgr/profiles/ directory.
 Examples:     sboxctl profile list     sboxctl profile list --show-active     sboxctl profile
 list --json --show-details

╭─ Options ───────────────────────────────────────────────────────────────────────────────────╮
│ --json                    Output in JSON format                                             │
│ --show-active             Show active profile                                               │
│ --show-details            Show profile details                                              │
│ --verbose       -v        Verbose output                                                    │
│ --help                    Show this message and exit.                                       │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯


```

---

### 🔸 Subcommand: `sboxctl profile show`

```

 Usage: python -m src.sboxmgr.cli.main profile show [OPTIONS] NAME

 Show profile contents.

 Displays the contents of a FullProfile configuration in the specified format. The profile can
 be validated before display.
 Examples:     sboxctl profile show home     sboxctl profile show work --format yaml
 sboxctl profile show test --validate --compact

╭─ Arguments ─────────────────────────────────────────────────────────────────────────────────╮
│ *    name      TEXT  Profile name to show [default: None] [required]                        │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ───────────────────────────────────────────────────────────────────────────────────╮
│ --format            TEXT  Output format (yaml, toml, json) [default: toml]                  │
│ --compact                 Compact output                                                    │
│ --validate                Validate profile before showing                                   │
│ --verbose   -v            Verbose output                                                    │
│ --help                    Show this message and exit.                                       │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯


```

---

### 🔸 Subcommand: `sboxctl profile new`

```

 Usage: python -m src.sboxmgr.cli.main profile new [OPTIONS] NAME

 Create a new profile.

 Creates a new FullProfile configuration with optional template. The profile will be saved to
 ~/.config/sboxmgr/profiles/ directory.
 Examples:     sboxctl profile new my-profile     sboxctl profile new work-vpn --template vpn
 --description "Work VPN"     sboxctl profile new test --template basic --edit

╭─ Arguments ─────────────────────────────────────────────────────────────────────────────────╮
│ *    name      TEXT  Profile name [default: None] [required]                                │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ───────────────────────────────────────────────────────────────────────────────────╮
│ --description          TEXT  Profile description [default: None]                            │
│ --template             TEXT  Template to use (basic, vpn, server, development, minimal)     │
│                              [default: None]                                                │
│ --format               TEXT  File format (toml, yaml) [default: toml]                       │
│ --edit                       Open in editor after creation                                  │
│ --verbose      -v            Verbose output                                                 │
│ --help                       Show this message and exit.                                    │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯


```

---

### 🔸 Subcommand: `sboxctl profile edit`

```

 Usage: python -m src.sboxmgr.cli.main profile edit [OPTIONS] NAME

 Edit profile in external editor.

 Opens the profile in the specified editor (or $EDITOR).
 Examples:     sboxctl profile edit home     sboxctl profile edit work --editor code
 --validate

╭─ Arguments ─────────────────────────────────────────────────────────────────────────────────╮
│ *    name      TEXT  Profile name to edit [default: None] [required]                        │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ───────────────────────────────────────────────────────────────────────────────────╮
│ --editor            TEXT  Editor to use [default: None]                                     │
│ --validate                Validate after editing                                            │
│ --backup                  Create backup before editing                                      │
│ --verbose   -v            Verbose output                                                    │
│ --help                    Show this message and exit.                                       │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯


```

---

### 🔸 Subcommand: `sboxctl profile validate`

```

 Usage: python -m src.sboxmgr.cli.main profile validate [OPTIONS] NAME

 Validate profile configuration.

 Validates a FullProfile configuration and reports any issues.
 Examples:     sboxctl profile validate home     sboxctl profile validate work --strict
 --show-errors

╭─ Arguments ─────────────────────────────────────────────────────────────────────────────────╮
│ *    name      TEXT  Profile name to validate [default: None] [required]                    │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ───────────────────────────────────────────────────────────────────────────────────╮
│ --strict                 Strict validation                                                  │
│ --show-errors            Show detailed errors                                               │
│ --fix                    Try to fix errors                                                  │
│ --verbose      -v        Verbose output                                                     │
│ --help                   Show this message and exit.                                        │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯


```

---

### 🔸 Subcommand: `sboxctl profile delete`

```

 Usage: python -m src.sboxmgr.cli.main profile delete [OPTIONS] NAME

 Delete profile.

 Deletes a FullProfile configuration from the system.
 Examples:     sboxctl profile delete test     sboxctl profile delete old-profile --force
 --backup

╭─ Arguments ─────────────────────────────────────────────────────────────────────────────────╮
│ *    name      TEXT  Profile name to delete [default: None] [required]                      │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ───────────────────────────────────────────────────────────────────────────────────╮
│ --force              Force deletion without confirmation                                    │
│ --backup             Create backup before deletion                                          │
│ --verbose  -v        Verbose output                                                         │
│ --help               Show this message and exit.                                            │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯


```

---

### 🔸 Subcommand: `sboxctl profile import`

```

 Usage: python -m src.sboxmgr.cli.main profile import [OPTIONS] FILE_PATH

 Import profile from file.

 Imports a FullProfile configuration from a file.
 Examples:     sboxctl profile import my-profile.toml     sboxctl profile import config.yaml
 --name imported-profile --validate

╭─ Arguments ─────────────────────────────────────────────────────────────────────────────────╮
│ *    file_path      TEXT  Profile file to import [default: None] [required]                 │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ───────────────────────────────────────────────────────────────────────────────────╮
│ --name               TEXT  Profile name (default: from file) [default: None]                │
│ --overwrite                Overwrite existing profile                                       │
│ --validate                 Validate after import                                            │
│ --verbose    -v            Verbose output                                                   │
│ --help                     Show this message and exit.                                      │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯


```

---

### 🔸 Subcommand: `sboxctl profile export`

```

 Usage: python -m src.sboxmgr.cli.main profile export [OPTIONS] NAME

 Export profile to file.

 Exports a FullProfile configuration to a file in the specified format.
 Examples:     sboxctl profile export home     sboxctl profile export work --out
 work-config.yaml --format yaml

╭─ Arguments ─────────────────────────────────────────────────────────────────────────────────╮
│ *    name      TEXT  Profile name to export [default: None] [required]                      │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ───────────────────────────────────────────────────────────────────────────────────╮
│ --out                       TEXT  Output file path [default: None]                          │
│ --format                    TEXT  Export format (toml, yaml, json) [default: toml]          │
│ --include-metadata                Include metadata                                          │
│ --verbose           -v            Verbose output                                            │
│ --help                            Show this message and exit.                               │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯


```

---

## 🔹 Command: `sboxctl export`

```

 Usage: python -m src.sboxmgr.cli.main export [OPTIONS] COMMAND [ARGS]...

 Export configurations and profiles


╭─ Options ───────────────────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                                 │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ──────────────────────────────────────────────────────────────────────────────────╮
│ generate   Generate ClientConfig from FullProfile.                                          │
│ validate   Validate configuration file.                                                     │
│ dry-run    Test configuration generation without saving.                                    │
│ profile    Export optimized FullProfile configuration.                                      │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯


```

### 🔸 Subcommand: `sboxctl export generate`

```

 Usage: python -m src.sboxmgr.cli.main export generate [OPTIONS] PROFILE_NAME

 Generate ClientConfig from FullProfile.

 Generates a machine-readable ClientConfig from a user-friendly FullProfile. This command
 adapts the existing export functionality to work with the new two-layer architecture.
 Examples:     sboxctl export generate home     sboxctl export generate work --output
 work-config.json --out-format json     sboxctl export generate home --url
 https://example.com/subscription

╭─ Arguments ─────────────────────────────────────────────────────────────────────────────────╮
│ *    profile_name      TEXT  Profile name to generate config from [default: None]           │
│                              [required]                                                     │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ───────────────────────────────────────────────────────────────────────────────────╮
│ --url             -u      TEXT  Subscription URL (overrides profile URL) [default: None]    │
│ --output                  TEXT  Output file path [default: config.json]                     │
│ --out-format              TEXT  Output format: json, toml, auto [default: json]             │
│ --target                  TEXT  Target format: singbox, clash [default: singbox]            │
│ --backup                        Create backup before overwriting existing file (creates     │
│                                 <output>.bak)                                               │
│ --user-agent              TEXT  Override User-Agent for subscription fetcher                │
│                                 [default: None]                                             │
│ --no-user-agent                 Do not send User-Agent header                               │
│ --postprocessors          TEXT  Comma-separated list of postprocessors                      │
│                                 (geo_filter,tag_filter,latency_sort)                        │
│                                 [default: None]                                             │
│ --middleware              TEXT  Comma-separated list of middleware (logging,enrichment)     │
│                                 [default: None]                                             │
│ --verbose         -v            Verbose output                                              │
│ --help                          Show this message and exit.                                 │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯


```

---

### 🔸 Subcommand: `sboxctl export validate`

```

 Usage: python -m src.sboxmgr.cli.main export validate [OPTIONS] CONFIG_FILE

 Validate configuration file.

 Validates a configuration file for syntax and semantic correctness. This command adapts the
 existing validation functionality to work with the new two-layer architecture.
 Examples:     sboxctl export validate config.json     sboxctl export validate config.toml
 --against-profile home     sboxctl export validate config.json --agent-check

╭─ Arguments ─────────────────────────────────────────────────────────────────────────────────╮
│ *    config_file      TEXT  Configuration file to validate [default: None] [required]       │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ───────────────────────────────────────────────────────────────────────────────────╮
│ --against-profile          TEXT  Profile name to validate against [default: None]           │
│ --as                       TEXT  Override format detection (json, toml) [default: None]     │
│ --agent-check                    Check configuration via sboxagent                          │
│ --verbose          -v            Verbose output                                             │
│ --help                           Show this message and exit.                                │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯


```

---

### 🔸 Subcommand: `sboxctl export profile`

```

 Usage: python -m src.sboxmgr.cli.main export profile [OPTIONS] PROFILE_NAME

 Export optimized FullProfile configuration.

 Exports a FullProfile configuration optimized for sharing or deployment. This command adapts
 the existing profile export functionality to work with the new two-layer architecture.
 Examples:     sboxctl export profile home     sboxctl export profile work --output
 work-deploy.toml --out-format toml     sboxctl export profile home --postprocessors
 geo_filter,tag_filter

╭─ Arguments ─────────────────────────────────────────────────────────────────────────────────╮
│ *    profile_name      TEXT  Profile name to export [default: None] [required]              │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ───────────────────────────────────────────────────────────────────────────────────╮
│ --output                    TEXT  Output file path [default: None]                          │
│ --out-format                TEXT  Export format: toml, yaml, json [default: toml]           │
│ --optimize                        Optimize profile for export                               │
│ --no-optimize                     Disable profile optimization                              │
│ --include-metadata                Include metadata in export                                │
│ --postprocessors            TEXT  Comma-separated list of postprocessors to add             │
│                                   [default: None]                                           │
│ --middleware                TEXT  Comma-separated list of middleware to add [default: None] │
│ --verbose           -v            Verbose output                                            │
│ --help                            Show this message and exit.                               │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯


```

---

## 🔹 Command: `sboxctl policy`

```

 Usage: python -m src.sboxmgr.cli.main policy [OPTIONS] COMMAND [ARGS]...

 Policy management commands


╭─ Options ───────────────────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                                 │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ──────────────────────────────────────────────────────────────────────────────────╮
│ list      List all registered policies, optionally filtered by group or severity.           │
│ test      Test policies with given context using evaluate_all() for comprehensive results.  │
│ audit     Audit multiple servers against all policies.                                      │
│ enable    Enable one or more policies.                                                      │
│ disable   Disable one or more policies.                                                     │
│ info      Show policy system information and examples.                                      │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯


```

### 🔸 Subcommand: `sboxctl policy list`

```

 Usage: python -m src.sboxmgr.cli.main policy list [OPTIONS]

 List all registered policies, optionally filtered by group or severity.


╭─ Options ───────────────────────────────────────────────────────────────────────────────────╮
│ --group                TEXT  Filter by policy group [default: None]                         │
│ --severity             TEXT  Filter by severity level [default: None]                       │
│ --enabled     --all          Show only enabled policies [default: enabled]                  │
│ --help                       Show this message and exit.                                    │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯


```

---

### 🔸 Subcommand: `sboxctl policy test`

```

 Usage: python -m src.sboxmgr.cli.main policy test [OPTIONS]

 Test policies with given context using evaluate_all() for comprehensive results.


╭─ Options ───────────────────────────────────────────────────────────────────────────────────╮
│ --profile                      TEXT  Profile to test [default: None]                        │
│ --server                       TEXT  Server to test (JSON file or inline JSON)              │
│                                      [default: None]                                        │
│ --user                         TEXT  User to test [default: None]                           │
│ --warnings    --no-warnings          Show warning results [default: warnings]               │
│ --info        --no-info              Show info results [default: no-info]                   │
│ --detailed                           Show detailed evaluation results                       │
│ --help                               Show this message and exit.                            │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯


```

---

### 🔸 Subcommand: `sboxctl policy audit`

```

 Usage: python -m src.sboxmgr.cli.main policy audit [OPTIONS]

 Audit multiple servers against all policies.


╭─ Options ───────────────────────────────────────────────────────────────────────────────────╮
│ --profile        TEXT  Profile to audit [default: None]                                     │
│ --servers        TEXT  File with list of servers to audit [default: None]                   │
│ --output         TEXT  Output file for audit results [default: None]                        │
│ --format         TEXT  Output format: json, text [default: json]                            │
│ --help                 Show this message and exit.                                          │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯


```

---

### 🔸 Subcommand: `sboxctl policy enable`

```

 Usage: python -m src.sboxmgr.cli.main policy enable [OPTIONS] POLICY_NAMES

 Enable one or more policies.


╭─ Arguments ─────────────────────────────────────────────────────────────────────────────────╮
│ *    policy_names      TEXT  Names of policies to enable (space-separated) [default: None]  │
│                              [required]                                                     │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ───────────────────────────────────────────────────────────────────────────────────╮
│ --all           Enable all policies                                                         │
│ --help          Show this message and exit.                                                 │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯


```

---

### 🔸 Subcommand: `sboxctl policy disable`

```

 Usage: python -m src.sboxmgr.cli.main policy disable [OPTIONS] POLICY_NAMES

 Disable one or more policies.


╭─ Arguments ─────────────────────────────────────────────────────────────────────────────────╮
│ *    policy_names      TEXT  Names of policies to disable (space-separated) [default: None] │
│                              [required]                                                     │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ───────────────────────────────────────────────────────────────────────────────────╮
│ --all           Disable all policies                                                        │
│ --help          Show this message and exit.                                                 │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯


```

---

### 🔸 Subcommand: `sboxctl policy info`

```

 Usage: python -m src.sboxmgr.cli.main policy info [OPTIONS]

 Show policy system information and examples.


╭─ Options ───────────────────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                                 │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯


```

---
