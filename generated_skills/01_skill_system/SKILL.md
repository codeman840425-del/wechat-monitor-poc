# Skill System - Core AI Development Norms

---
skill_id: skill-system
trigger_keywords: ["skill", "norms", "rules", "development standards"]
dependencies: []
---

## Quick Load Guide
| Task | Load |
|------|------|
| Start new session | This skill |
| Type checking | `code-quality` in reference |
| Git operations | `version-control` in reference |
| Security review | `security-guardrails` in reference |
| Pre-commit | `checklist-templates` in reference |

## Core Rules (Read First)
1. **Session Start**: Read CHANGELOG → UPGRADE → ARCHITECTURE → WORKFLOW → DEV_NOTES → skills/ → this file
2. **Doc Sync**: Update CHANGELOG + DEV_NOTES after every significant change
3. **Type Safety**: Target Pylance 0 errors on critical modules
4. **Security**: No hardcoded secrets, no `eval/exec`, verify SSL
5. **Versioning**: Use SemVer, tag stable versions

## Project Structure
- `monitor.py`: Stable fallback
- `monitor_v2.py`: Main entry
- `core/`: Data structures
- `sources/`: Message sources
- `web_app.py`: Flask interface
- `skills/`: This system

## Code Standards
- Naming: `snake_case` functions, `PascalCase` classes
- Types: Required for public interfaces, avoid `Any`
- Flask: Must return `ResponseReturnValue`, never `None`
- Config: No hardcoding, use `config.yaml`

## AI Code Marking
**Simple** (<30 lines):
```python
# [AI-GENERATED] Date: 2026-02-03 | Task: Description
def func(): pass
```

**Complex** (30+ lines):
```python
# [AI-GENERATED] Date: 2026-02-03 | PromptHash: abc123
# [REVIEWED] By: name | Date: 2026-02-03 | Status: VERIFIED
# [SAFETY] Checked: SQL injection, path traversal
```

## Security Red Lines
- Never: Hardcoded keys, absolute paths with usernames, production data in AI context
- Never: `eval()`, `exec()`, `os.system()` without `[SECURITY_REVIEWED]`
- Never: `verify=False` in SSL

## Essential Commands
```bash
python health_check.py      # Verify system
pyright                     # Type check
git tag -a v0.5.0 -m "msg"  # Tag version
git checkout v0.4.0         # Rollback
```

## See reference.md For
- Complete skill hierarchy
- Detailed code patterns
- Exception handling templates
- Full checklists
- Cross-references
