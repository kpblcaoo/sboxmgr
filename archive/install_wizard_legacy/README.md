# 📁 Legacy Installation Wizard (ARCHIVED)

## ⚠️ Security Notice
This installation wizard has been **ARCHIVED** due to significant security vulnerabilities and is no longer part of the active codebase.

## 🔒 Security Issues Identified
- **subprocess vulnerabilities**: Multiple unsafe subprocess calls
- **shell=True usage**: Dangerous shell execution in subprocess.run()
- **Privilege escalation**: sudo operations without proper validation
- **Path traversal risks**: Insufficient path validation
- **High code complexity**: E-37 complexity rating making security audit difficult

## 📅 Archive Information
- **Archived on**: 2025-06-25
- **Original location**: `src/install/`
- **Reason**: Security risk elimination during refactor/cleanup
- **Branch**: refactor/cleanup
- **Security checklist**: SEC-LEGACY-01 ✅ COMPLETED

## 🔄 Future Plans
The installation functionality will be reimplemented as a secure TUI (Text User Interface) in a future version with:
- ✅ No subprocess shell=True usage
- ✅ Proper input validation and sanitization
- ✅ Reduced code complexity
- ✅ Comprehensive security testing
- ✅ Principle of least privilege

## 📋 Files Archived
- `wizard.py` - Main installation wizard (399 LOC, E-37 complexity)

## 🔗 Related Documentation
- `docs/security.md` - Updated threat model
- `docs/sec_checklist.md` - Security checklist with SEC-LEGACY items
- `plans/tests/CODE_QUALITY_AUDIT.md` - Code quality analysis results

## ⚡ Migration Notes
If you need installation functionality:
1. Use manual installation procedures from documentation
2. Wait for the secure TUI implementation
3. **DO NOT** use this archived wizard in production

---
*This archive is maintained for reference and security research purposes only.* 