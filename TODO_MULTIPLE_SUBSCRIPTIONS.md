# TODO: Multiple Subscriptions Support

## Current Issue
TUI currently uses a temporary workaround to support multiple subscriptions in config generation, bypassing the orchestrator and using export_manager directly.

## Problem
- `orchestrator.export_configuration()` only accepts a single `source_url`
- TUI logic diverges from CLI logic
- Core architecture doesn't properly support multiple subscriptions

## Temporary Solution
In `src/sboxmgr/tui/state/tui_state.py`, method `generate_config()`:
- Collects servers from all subscriptions manually
- Uses `orchestrator.export_manager.export()` directly instead of `orchestrator.export_configuration()`
- Marked with `# TEMPORARY SOLUTION` comment

## Proper Fix Required

### 1. Update Orchestrator
- Modify `orchestrator.export_configuration()` to accept multiple subscriptions
- Add new method like `export_configuration_multi()` or extend existing method
- Ensure proper error handling for multiple subscriptions

### 2. Update CLI
- CLI should also support multiple subscriptions
- Update CLI commands to handle multiple subscription URLs
- Ensure consistent behavior between TUI and CLI

### 3. Update Core Architecture
- Consider if subscription management should be refactored
- Ensure profile system properly handles multiple subscriptions
- Update interfaces if needed

## Files to Update
- `src/sboxmgr/core/orchestrator.py` - Add multiple subscription support
- `src/sboxmgr/cli/` - Update CLI commands
- `src/sboxmgr/tui/state/tui_state.py` - Remove temporary workaround
- Tests - Add tests for multiple subscription scenarios

## Priority
Medium - Current workaround works but creates architectural inconsistency

## Notes
- Current TUI implementation works correctly for multiple subscriptions
- CLI may have similar issues that need to be addressed
- This is a core architectural improvement, not just a TUI fix
