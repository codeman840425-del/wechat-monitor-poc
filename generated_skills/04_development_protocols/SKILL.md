# Development Protocols - Workflow Standards

---
skill_id: development-protocols
trigger_keywords: ["development process", "workflow", "collaboration", "protocol"]
dependencies: ["skill-system"]
---

## Three-File System
| File | Purpose | Update When |
|------|---------|-------------|
| `ITERATIVE_BOARD.md` | Requirements, roadmap, history | Status changes |
| `ERROR_LOG.md` | Errors, fixes, workarounds | Error occurs |
| `STEP_MANUAL.md` | Test guide, acceptance criteria | Step complete |

**Rule**: No STEP_MANUAL.md update = not complete. No ERROR_LOG.md entry = negligence.

## Development Process (Step 0-4)

**Step 0**: Receive requirement → Update ITERATIVE_BOARD → Break into steps → Wait confirm

**Step 1**: Code + Use `dev_test()` wrapper → Record ALL errors to ERROR_LOG.md immediately

**Step 2**: Self-fix (mandatory before delivery)
- P0 (Syntax/Import/Name): Must fix
- P1 (Type): Must fix
- P2 (Runtime): Add guards
- P3 (Logic): Mark "needs user"

**Step 3**: Update ITERATIVE_BOARD → Write STEP_MANUAL.md → Output delivery message

**Step 4**: Process feedback → If fail, return to Step 1

## Error Recording
```markdown
### Error #{n} - {timestamp}
**Location**: file.py:line
**Type**: SyntaxError|ImportError|...
**Message**: ```traceback```
**Status**: pending|fixed|needs user
```

## dev_test Wrapper
```python
def dev_test(name, func, *args, **kwargs):
    try: return func(*args, **kwargs)
    except Exception as e:
        # Auto-prints error
        return None  # Continue flow
```

## Naming Conventions
- Docs: `UPPERCASE.md` (README, CHANGELOG)
- Skills: `lowercase.md` (core-rules)
- Dirs: `DOCS/`, `skills/`

## Doc Metadata
```yaml
---
title: Name
category: [项目入口|开发规范|项目管理]
version: v1.0.0
date: 2026-02-03
status: [活跃|归档|草稿]
---
```

## See reference.md For
- Complete ITERATIVE_BOARD template
- Full STEP_MANUAL template
- Self-fix SOP details
- Test procedures
