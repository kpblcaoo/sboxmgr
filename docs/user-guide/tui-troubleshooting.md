# TUI Troubleshooting Guide

## Common Issues and Solutions

This guide helps you resolve common issues with the SBoxMgr Text User Interface (TUI).

## Launch Issues

### TUI Won't Start

**Symptoms:**
- Command returns error immediately
- No interface appears
- Terminal shows error messages

**Solutions:**

1. **Check Installation**
   ```bash
   # Verify package is installed
   python -c "import sboxmgr"

   # Check if command exists
   which sboxctl
   ```

2. **Check Python Version**
   ```bash
   # Ensure Python 3.8+
   python --version
   ```

3. **Install Dependencies**
   ```bash
   # Install from source
   pip install -e .

   # Or install dependencies manually
   pip install textual
   ```

4. **Check Terminal Compatibility**
   ```bash
   # Ensure terminal supports TUI
   echo $TERM
   # Should show: xterm-256color, screen, or similar
   ```

### TUI Starts but Crashes

**Symptoms:**
- Interface appears briefly then exits
- Error messages in terminal
- No error handling

**Solutions:**

1. **Enable Debug Mode**
   ```bash
   python -m sboxmgr.cli.main tui --debug 2
   ```

2. **Check Logs**
   ```bash
   # Look for error messages in output
   python -m sboxmgr.cli.main tui --debug 3 2>&1 | tee tui-debug.log
   ```

3. **Reset Configuration**
   ```bash
   # Remove corrupted config
   rm ~/.config/sboxmgr/config.toml
   ```

## Navigation Issues

### Can't Navigate Between Screens

**Symptoms:**
- Arrow keys don't work
- Tab key doesn't move focus
- Stuck on one screen

**Solutions:**

1. **Check Terminal Type**
   ```bash
   # Ensure proper terminal
   export TERM=xterm-256color
   python -m sboxmgr.cli.main tui
   ```

2. **Use Alternative Keys**
   - Try `Tab` instead of arrows
   - Use `Enter` to select
   - Press `q` to go back

3. **Mouse Navigation**
   - Click directly on buttons/items
   - Use mouse wheel for scrolling

### Checkboxes Not Working

**Symptoms:**
- Can't toggle exclusions
- Space key doesn't work
- Mouse clicks don't register

**Solutions:**

1. **Keyboard Method**
   - Use `Space` key to toggle
   - Ensure focus is on checkbox
   - Try `Enter` key as alternative

2. **Mouse Method**
   - Click directly on checkbox
   - Try clicking on checkbox text
   - Use right-click if available

3. **Reset Focus**
   - Press `Tab` to cycle through controls
   - Use arrow keys to navigate
   - Press `Esc` to reset

## Data Issues

### Subscriptions Not Loading

**Symptoms:**
- Empty subscription list
- "No subscriptions" message
- Servers not appearing

**Solutions:**

1. **Check Subscription URLs**
   ```bash
   # Test URL manually
   curl -I "YOUR_SUBSCRIPTION_URL"
   ```

2. **Verify Network**
   ```bash
   # Check internet connection
   ping 8.8.8.8
   ```

3. **Check Debug Logs**
   ```bash
   python -m sboxmgr.cli.main tui --debug 2
   # Look for subscription processing errors
   ```

4. **Manual CLI Test**
   ```bash
   # Test with CLI first
   sboxctl list-servers -u "YOUR_URL"
   ```

### Exclusions Not Saving

**Symptoms:**
- Checkbox states reset on restart
- Exclusions disappear
- Changes not persisted

**Solutions:**

1. **Check Profile System**
   ```bash
   # Verify profile exists
   sboxctl config status

   # Check profile file
   cat ~/.config/sboxmgr/profiles/active.toml
   ```

2. **Manual Save**
   - Exit TUI properly (press 'q')
   - Don't use Ctrl+C to exit
   - Wait for save confirmation

3. **Check File Permissions**
   ```bash
   # Ensure write permissions
   ls -la ~/.config/sboxmgr/
   chmod 755 ~/.config/sboxmgr/
   ```

4. **Reset Profile**
   ```bash
   # Create new profile
   sboxctl config create test
   sboxctl config switch test
   ```

### Configuration Generation Fails

**Symptoms:**
- "Generate Configuration" fails
- No output file created
- Error messages

**Solutions:**

1. **Check Subscriptions**
   - Ensure at least one subscription is active
   - Verify servers are loaded
   - Check for valid server data

2. **Check Exclusions**
   - Ensure not all servers are excluded
   - Review exclusion settings
   - Reset exclusions if needed

3. **Debug Generation**
   ```bash
   # Use CLI to test generation
   sboxctl export -u "YOUR_URL" --index 1 --dry-run
   ```

4. **Check Output Directory**
   ```bash
   # Verify write permissions
   ls -la ~/.config/sboxmgr/
   mkdir -p ~/.config/sboxmgr/output
   ```

## Performance Issues

### Slow Loading

**Symptoms:**
- Long delays when adding subscriptions
- Slow server list loading
- Interface freezes

**Solutions:**

1. **Reduce Server Count**
   - Exclude more servers
   - Use smaller subscriptions
   - Filter by location

2. **Check Network**
   ```bash
   # Test subscription URL speed
   time curl "YOUR_SUBSCRIPTION_URL"
   ```

3. **Use Debug Mode**
   ```bash
   # Monitor processing
   python -m sboxmgr.cli.main tui --debug 2
   ```

4. **Optimize Settings**
   - Disable unnecessary features
   - Use local caching
   - Reduce update frequency

### High Memory Usage

**Symptoms:**
- System becomes slow
- High memory consumption
- Out of memory errors

**Solutions:**

1. **Limit Server Count**
   - Exclude more servers
   - Use smaller subscriptions
   - Process subscriptions separately

2. **Restart TUI**
   ```bash
   # Exit and restart
   # Clear memory
   ```

3. **Check System Resources**
   ```bash
   # Monitor memory usage
   htop
   free -h
   ```

## Display Issues

### Text Not Visible

**Symptoms:**
- Blank screen
- Text appears as boxes
- Colors not displaying

**Solutions:**

1. **Check Terminal Colors**
   ```bash
   # Test color support
   echo -e "\033[31mRed\033[0m \033[32mGreen\033[0m \033[34mBlue\033[0m"
   ```

2. **Set Terminal Type**
   ```bash
   export TERM=xterm-256color
   python -m sboxmgr.cli.main tui
   ```

3. **Use Different Terminal**
   ```bash
   # Try different terminal emulator
   gnome-terminal
   # or
   konsole
   ```

### Layout Problems

**Symptoms:**
- Text overlapping
- Buttons not aligned
- Screen too small

**Solutions:**

1. **Resize Terminal**
   - Make terminal window larger
   - Minimum 80x24 characters
   - Preferred 120x30

2. **Check Terminal Size**
   ```bash
   # Verify terminal dimensions
   echo $COLUMNS x $LINES
   ```

3. **Use Full Screen**
   - Press F11 for full screen
   - Maximize terminal window

## Debug Mode Usage

### Enabling Debug Mode

```bash
# Basic debug
python -m sboxmgr.cli.main tui --debug 1

# Detailed debug
python -m sboxmgr.cli.main tui --debug 2

# Full debug with logs
python -m sboxmgr.cli.main tui --debug 3 2>&1 | tee tui-debug.log
```

### Understanding Debug Output

**Level 1**: Basic operation info
**Level 2**: Detailed processing info
**Level 3**: Full debug with file operations

**Common Debug Messages:**
- `[DEBUG] Loading subscriptions` - Normal operation
- `[ERROR] Failed to load subscription` - Network/URL issue
- `[WARNING] No servers found` - Empty subscription
- `[INFO] Configuration generated` - Success

## Getting Help

### Collect Information

Before seeking help, collect:

1. **System Information**
   ```bash
   uname -a
   python --version
   echo $TERM
   ```

2. **Debug Logs**
   ```bash
   python -m sboxmgr.cli.main tui --debug 3 2>&1 | tee debug.log
   ```

3. **Configuration Files**
   ```bash
   cat ~/.config/sboxmgr/config.toml
   cat ~/.config/sboxmgr/profiles/active.toml
   ```

### Report Issues

When reporting issues, include:

- System information
- Debug logs
- Steps to reproduce
- Expected vs actual behavior
- Configuration files (remove sensitive data)

## See Also

- [TUI Guide](tui-guide.md) - Complete TUI documentation
- [CLI Reference](cli-reference.md) - Command-line interface
- [Troubleshooting](troubleshooting.md) - General troubleshooting
- [Configuration Management](configs.md) - Profile and settings

---

**Last updated**: 2025-01-05
