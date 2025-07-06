# CLI Security: update-singbox

## Implemented Measures

- **Plugin generator sandboxing**: template generation is allowed only in permitted directories, with no code execution.
- **Class name and docstring validation**: the generator checks class names and docstrings for correctness, preventing injections and conflicts.
- **File generation restrictions**: important files cannot be overwritten, generation is allowed only in src/sboxmgr/subscription/<type>s/.
- **UX for errors**: all generation and CLI command errors are user-friendly, without exposing stacktraces or secrets.
- **Edge-case tests**: automated tests for invalid names, conflicts, and template errors.
- **Recommendations**: do not run the generator as root, review templates before use, avoid unique/secret strings in docstrings.

## SEC validation for inbounds (v1.5.0)
- All inbounds are validated via pydantic (V2):
    - bind only to 127.0.0.1 or ::1 (or private network)
    - ports only 1024-65535
    - external bind (0.0.0.0) raises an error
- Edge tests cover profile errors, unsafe values, port conflicts, SEC validation
- Example:
```python
InboundProfile(type="socks", listen="0.0.0.0", port=10808)  # ValueError
InboundProfile(type="socks", listen="127.0.0.1", port=80)   # ValueError
```

## TODO / Future
- Sandboxing for all CLI commands (env restrictions, chroot, seccomp)
- Validation of all user paths and parameters
- Integration with sec_checklist.md and edge_cases.md
- Automated CLI security audit

_See also: sec_checklist.md, edge_cases.md, README.md_
