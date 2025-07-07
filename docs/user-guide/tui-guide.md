# TUI (Text User Interface) Guide

## Overview

SBoxMgr provides a modern Text User Interface (TUI) that offers an intuitive, interactive way to manage your sing-box configurations, subscriptions, and server exclusions without needing to remember complex command-line arguments.

## Benefits of TUI

- **User-Friendly**: Intuitive interface with clear navigation
- **Interactive**: Real-time feedback and immediate results
- **Visual**: See your subscriptions, servers, and exclusions at a glance
- **Persistent**: Settings and exclusions are automatically saved
- **Accessible**: Works with keyboard and mouse navigation

## Getting Started

### Launching TUI

```bash
# Basic TUI launch
python -m sboxmgr.cli.main tui

# With debug logging
python -m sboxmgr.cli.main tui --debug 2

# From installed package
sboxctl tui
```

### First Run

When you first launch TUI, you'll see the welcome screen. From here you can:

1. **Add Subscriptions** - Start managing your proxy subscriptions
2. **View Help** - Learn about available features
3. **Exit** - Close the application

## Screen Navigation

### Welcome Screen
The main entry point showing:
- Application title and version
- Quick action buttons
- Help information

**Navigation:**
- Use arrow keys or Tab to move between buttons
- Press Enter to select
- Press 'q' or Ctrl+C to exit

### Subscription Management Screen
Manage your proxy subscriptions with an intuitive interface.

**Features:**
- View all subscriptions in a table format
- Add new subscriptions with the green "➕ Add New Subscription" button
- Edit existing subscriptions
- Remove subscriptions
- See subscription status and server counts

**Actions:**
- **Add Subscription**: Click the green button or press 'a'
- **Edit**: Select a subscription and press 'e'
- **Remove**: Select a subscription and press 'r'
- **Back**: Press 'b' or 'q' to return to welcome screen

**Adding a Subscription:**
1. Click "➕ Add New Subscription" or press 'a'
2. Enter the subscription URL
3. Optionally add a name/description
4. Press Enter to save
5. The subscription will be processed and servers loaded

### Server List Screen
View and manage servers from your subscriptions with exclusion controls.

**Features:**
- Display all servers from all subscriptions
- Checkbox controls for exclusions
- Server information (name, type, location)
- Real-time filtering and search
- Visual highlighting of excluded servers

**Navigation:**
- **Arrow Keys**: Navigate between servers
- **Space**: Toggle exclusion checkbox
- **Mouse Click**: Click checkboxes to toggle exclusions
- **Search**: Type to filter servers
- **Back**: Press 'b' or 'q' to return

**Managing Exclusions:**
- Check/uncheck boxes to exclude/include servers
- Excluded servers are highlighted in red
- Changes are automatically saved
- Exclusions persist between sessions

### Configuration Generation
Generate sing-box configuration files from your selected servers.

**Features:**
- Generate configuration with current settings
- View generation status and results
- Automatic profile integration
- Support for multiple subscriptions

**Process:**
1. Select "Generate Configuration" from welcome screen
2. TUI will process all subscriptions
3. Apply exclusions and filters
4. Generate configuration file
5. Show success/error status

## Keyboard Shortcuts

### Global Shortcuts
- **q** - Exit/Go back
- **h** - Show help
- **Ctrl+C** - Force exit

### Navigation
- **Arrow Keys** - Navigate between items
- **Tab** - Move between controls
- **Enter** - Select/Activate
- **Space** - Toggle checkboxes
- **Esc** - Cancel/Go back

### Subscription Management
- **a** - Add new subscription
- **e** - Edit selected subscription
- **r** - Remove selected subscription
- **s** - Show server list

### Server List
- **Space** - Toggle exclusion
- **s** - Search/filter servers
- **c** - Clear all exclusions
- **g** - Generate configuration

## Profile Integration

TUI automatically integrates with SBoxMgr's profile system:

- **Settings Persistence**: All changes are saved to your active profile
- **Configuration Loading**: TUI loads settings from your current profile
- **Multi-Profile Support**: Switch between different profiles
- **Automatic Saving**: Changes are saved immediately

## Tips and Best Practices

### Efficient Workflow
1. **Start with Subscriptions**: Add all your subscription URLs first
2. **Review Servers**: Check the server list to see what's available
3. **Set Exclusions**: Exclude servers you don't want to use
4. **Generate Config**: Create your final configuration
5. **Test**: Validate the generated configuration

### Performance Tips
- Use debug mode (`--debug 2`) for troubleshooting
- Close TUI properly to ensure settings are saved
- Large subscription lists may take time to load
- Exclusions are applied immediately for better performance

### Troubleshooting
- **Servers not loading**: Check subscription URL validity
- **Exclusions not saving**: Ensure proper exit from TUI
- **Configuration errors**: Check debug logs for details
- **Slow performance**: Consider excluding more servers

## Debug Mode

Enable debug mode for troubleshooting:

```bash
python -m sboxmgr.cli.main tui --debug 2
```

Debug mode provides:
- Detailed operation logs
- Subscription processing information
- Configuration generation details
- Error diagnostics

## Configuration Examples

### Basic Setup
```bash
# Launch TUI
sboxctl tui

# Add subscription via TUI
# Navigate to subscription management
# Click "Add New Subscription"
# Enter: https://example.com/subscription.json

# Set exclusions via server list
# Navigate to server list
# Check/uncheck servers as needed

# Generate configuration
# Return to welcome screen
# Select "Generate Configuration"
```

### Advanced Usage
```bash
# Launch with debug logging
sboxctl tui --debug 2

# Use with specific profile
export SBOXMGR_PROFILE=work
sboxctl tui

# Generate and test configuration
# After generating in TUI:
sing-box check -c config.json
```

## Integration with CLI

TUI and CLI work together seamlessly:

- **Settings Shared**: Both use the same profile system
- **Configurations Compatible**: Generated configs work with CLI
- **Exclusions Synchronized**: Exclusions set in TUI apply to CLI
- **Profiles Unified**: Profile changes affect both interfaces

## See Also

- [CLI Reference](cli-reference.md) - Command-line interface
- [Configuration Management](configs.md) - Profile and settings
- [Subscription Management](subscriptions.md) - Working with subscriptions
- [Troubleshooting](troubleshooting.md) - Common issues and solutions

---

**Last updated**: 2025-01-05
