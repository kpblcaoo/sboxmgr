# Decision List: Refactoring & Atomization Plan for update-singbox

## 1. Building the Atomization Map
- Use struct.json and module indices to analyze functions, relationships, duplication, and group by areas of responsibility.
- Group functions by meaning (exclusions, selection, state, utils, etc.), build a directory tree based on real relationships.

## 2. Proposed Directory Structure and Modules
```
src/
  main.py (ex-update_singbox.py, only CLI)
  install/
    wizard.py (ex-install_wizard.py)
    venv.py (working with virtual environment)
    systemd.py (working with systemd)
  singbox/
    config/
      fetch.py
      generate.py
      protocol.py
      template.py (if needed)
    server/
      management.py (or split into exclusions.py, selection.py, state.py)
    service/
      manage.py
    utils/
      file.py
      id.py
      temp.py
  logging/
    setup.py
  modules/ (keep as alias for backward compatibility, or remove)
tests/
docs/
```
- Each submodule is a separate area of responsibility, easily testable and extensible.
- Common functions (e.g., handle_temp_file, generate_server_id) go into utils/.
- CLI is only the entry point, all business logic is in modules.

## 3. Decision List (atomization and reorganization)
| №  | Action                                                                 | Confidence | Justification/methodology                                                                                   |
|----|--------------------------------------------------------------------------|------------|--------------------------------------------------------------------------------------------------------|
| 1  | Move all source code to `src/` and split by areas of responsibility  | 98%        | Structure and relationships are visible from struct.json, easy to automate                                         |
| 2  | Extract common functions to `utils/`                                         | 100%       | Clear candidates: handle_temp_file, generate_server_id, get_file_hash                                   |
| 3  | Split server_management into submodules: exclusions, selection, state    | 95%        | Functions are clearly grouped by meaning, relationships are minimal                                                 |
| 4  | Move systemd, venv, file copying to install/           | 95%        | Functions install_wizard are easily extracted by callgraph                                                   |
| 5  | Keep main.py only for CLI, move all business logic to modules      | 100%       | Best practice, easy to implement                                                                       |
| 6  | Unify CLI language (English)                                      | 100%       | Simple string fix                                                                                   |
| 7  | Support both formats for --exclude (comma and space)              | 95%        | Can be implemented with a custom action for argparse                                                           |
| 8  | Extract outbounds/excluded_ips preparation to a helper                       | 100%       | Duplication is visible by callgraph                                                                        |
| 9  | Fix shadowing of remove_exclusions                                    | 100%       | Simple name replacement                                                                                   |
| 10 | Log the absence of $excluded_servers                                  | 100%       | Easy to implement with a flag in the function                                                                 |
| 11 | Consolidate exclusions/selection logic                              | 90%        | Possible edge-cases, but function structure is transparent                                                    |
| 12 | Update changelog and documentation                                        | 100%       | Simple fix                                                                                         |
| 13 | Add type hints                                                      | 98%        | All parameters and return values are visible in the index                                                  |
| 14 | Ensure test coverage for new/refactored functions                  | 95%        | Easy to build a coverage map from the function map                                                          |
| 15 | Regularly update struct.json and index after changes                 | 100%       | For structure control and automation                                                                 |

---

## 4. How to Use Index for Automation
- Automatically find utils function candidates (by docstring, callgraph, repetition).
- Group functions by areas of responsibility (e.g., all functions working with exclusions into one module).
- Build a dependency map to minimize coupling between modules.
- Generate documentation and test coverage map.
- Control regressions by function and module hashes.

---

## 5. Process Instructions
- Each major refactoring step requires updating struct.json and the module index (`llmstruct parse ...`).
- Stop and ask the user to update the index after each significant change in structure or functions.
- Only proceed to the next step after updating the index.
- This approach ensures that the entire process can be done step by step, with user involvement at key control points.
