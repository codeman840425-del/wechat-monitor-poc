# Reference: Complete Skill System Documentation

> **Merged from**: `skills/` directory  
> **Source files**: README.md, core-rules.md, code-quality.md, version-control.md, security-guardrails.md, ai-traceability.md, checklist-templates.md  
> **Generated**: 2026-02-03

---

## Table of Contents

1. [Skill System Overview](#1-skill-system-overview)
2. [Core Rules](#2-core-rules)
3. [Code Quality](#3-code-quality)
4. [Version Control](#4-version-control)
5. [Security Guardrails](#5-security-guardrails)
6. [AI Traceability](#6-ai-traceability)
7. [Checklist Templates](#7-checklist-templates)

---

## 1. Skill System Overview

This project uses a modular skill system for organizing development norms. Skills are loaded based on task context using trigger keywords.

### Skill Categories

| Layer | Skills | Purpose |
|-------|--------|---------|
| **Foundation** | core-rules | Base rules for all sessions |
| **Quality** | code-quality | Type checking, testing standards |
| **Management** | version-control | Git workflows, rollback strategies |
| **Security** | security-guardrails | Security rules, data protection |
| **Compliance** | ai-traceability | AI code marking, review tracking |
| **Tools** | checklist-templates | Quick reference, checklists |

### Skill Metadata Format

Each skill file begins with YAML frontmatter:

```yaml
---
skill_id: unique-identifier
trigger_keywords: ["keyword1", "keyword2"]
dependencies: ["core-rules"]
context_window: Description of when to use this skill
---
```

---

## 2. Core Rules

### 2.1 Session Start Protocol

**MUST read in order** when starting new session:
1. `CHANGELOG.md` - Version history
2. `UPGRADE.md` - Upgrade guides
3. `DOCS/ARCHITECTURE.md` - Architecture
4. `DOCS/WORKFLOW.md` - Workflow
5. `DOCS/DEV_NOTES.md` - Current state
6. `skills/README.md` - Skill system
7. `skills/core-rules.md` - Core rules

**Post-reading summary** (max 10 lines):
- Current version/status
- Main modules and data flow
- Current iteration goal

### 2.2 Project Structure

| Path | Purpose |
|------|---------|
| `monitor.py` | Single-source monitoring (stable fallback) |
| `monitor_v2.py` | Multi-source monitoring (main entry) |
| `core/` | Core data structures (`ChatMessage`) |
| `sources/` | Message sources (base, wechat_screen, window_screen) |
| `web_app.py` | Flask Web management interface |
| `DOCS/` | Architecture, workflow, dev notes |
| `skills/` | Development norms (this system) |

### 2.3 Code Style

- **Functions/variables**: `snake_case`
- **Classes**: `PascalCase`
- **Type annotations**: Required for public interfaces
- **Avoid `Any`**: Use only when necessary, document in DEV_NOTES
- **Nullable types**: Use `Optional[...]`, explicit `is not None` checks

### 2.4 Flask Route Requirements

All routes must return `ResponseReturnValue`:
- Normal: `render_template(...)`, `jsonify(...)`, or string
- Error: `abort(...)` or `make_response(...)`
- **Never**: `None`, bare tuples `("error", 500)`, implicit None

### 2.5 Configuration Rules

- No hardcoded paths, keys, or sensitive parameters
- Use `config.yaml` or database for all configuration
- New config items must be documented in architecture/workflow docs
- Maintain backward compatibility

### 2.6 Documentation Sync

**After every significant change**:
1. Update `CHANGELOG.md` (version + changes)
2. Update `DOCS/DEV_NOTES.md` (iteration status, TODOs)
3. Update `DOCS/ARCHITECTURE.md` (if architecture changed)
4. Update `DOCS/WORKFLOW.md` (if process changed)

### 2.7 Memory Conflict Resolution

When new memory conflicts with old:

```markdown
## Memory Conflict Record

**Conflict Date**: 2026-02-03
**Conflict Content**:
- Old memory (2026-01-15): Description
- New memory (2026-02-03): Description
**Decision**: Resolution
**Impact**: Affected areas
```

### 2.8 Error Recording

All errors during development must be recorded in `DOCS/DEV_NOTES.md`:
- File + line number
- Error summary
- Impact scope (runtime vs static check)

**End-of-iteration cleanup**: Resolve accumulated issues, restore "healthy + 0 type errors" baseline.

---

## 3. Code Quality

### 3.1 Type Checking Requirements

**Target modules for Pylance 0 errors**:
- `monitor.py`
- `monitor_v2.py`
- `web_app.py`
- `core/` directory
- `sources/` directory

**Handling temporary type warnings**:
- Record in `DOCS/DEV_NOTES.md`: file, line, error, reason for deferral
- Use `# type: ignore` only with explicit comment explaining why

### 3.2 Health Check Requirements

`health_check.py` must verify:

1. **Database Check**
   - Connect to `wechat_monitor.db`
   - Verify tables exist (messages, keywords)
   - Check required fields

2. **Web Route Check**
   - Flask app initializes
   - Routes registered: `/`, `/messages`, `/keywords`, `/images/*`, `/api/webhook/*`

3. **Message Source Check**
   - Configured sources can initialize
   - Safe "dry-run" poll without real screenshot/database write

### 3.3 Type Annotation Examples

```python
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass

@dataclass
class ChatMessage:
    id: str
    platform: str
    content: str
    timestamp: datetime
    sender: Optional[str] = None
    metadata: Dict[str, any] = field(default_factory=dict)

def process_message(
    message: ChatMessage,
    keywords: List[str],
    case_sensitive: bool = False
) -> Optional[str]:
    """Process message, return matched keyword or None"""
    if not message.content:
        return None
    # Processing logic...
    return matched_keyword
```

### 3.4 Exception Handling Template

```python
def safe_operation() -> Optional[Result]:
    try:
        # Business logic
        return result
    except SpecificException as e:
        logger.error(f"Operation failed: {e}")
        ErrorTracker.record(e, context={"operation": "safe_operation"})
        return None
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        raise  # Or return safe default
```

### 3.5 Required Exception Handling

| Operation | Exception to Catch |
|-----------|-------------------|
| Database | `sqlite3.Error` |
| File operations | `IOError`, `FileNotFoundError` |
| Network | `requests.RequestException` |
| OCR | `pytesseract.TesseractError` |

---

## 4. Version Control

### 4.1 Git Tag Management

Tag stable versions:
- `v0.2.0`: Single-source + region selection
- `v0.3.0`: Web management interface
- `v0.4.0`: Multi-source architecture

### 4.2 Soft Rollback (Entry Script Level)

Keep old entry scripts for compatibility:
- `monitor.py`: Stable fallback for old structure
- `monitor_v2.py`: New multi-source main entry

Document in `UPGRADE.md`:
- Latest recommended script
- How to "soft rollback" to `monitor.py`

### 4.3 Hard Rollback (Code Version)

```bash
# View tags
git tag

# Rollback to specific version
git checkout v0.3.0
```

Document:
- Which entry script to use after rollback
- Database backup recommendation
- Handling of new config fields (old version ignores extras)

### 4.4 Upgrade Checklist

- [ ] Current version tagged
- [ ] Database backed up
- [ ] Config backed up
- [ ] Target version `UPGRADE.md` read
- [ ] Rollback plan confirmed

### 4.5 Semantic Versioning

- **MAJOR**: Incompatible API changes
- **MINOR**: Backward-compatible features
- **PATCH**: Backward-compatible fixes

Examples:
- `v0.4.0`: Multi-source monitoring (feature)
- `v0.4.1`: Screenshot bugfix (patch)
- `v1.0.0`: Official release (major)

---

## 5. Security Guardrails

### 5.1 Security Red Lines

**NEVER**:
1. Hardcode API keys, tokens, connection strings
2. Use absolute paths with real names (`C:\Users\RealName\`)
3. Include production data in AI context
4. Use `os.system()`, `subprocess.call()`, `eval()`, `exec()` without `[SECURITY_REVIEWED]`
5. Disable SSL verification (`verify=False`)

### 5.2 Secure Configuration Pattern

**Correct**:
```yaml
# config.yaml
api:
  app_id: ""  # From env: ${WECHAT_APP_ID}
  app_secret: ""  # From env: ${WECHAT_APP_SECRET}
```

```python
import os
app_id = os.environ.get('WECHAT_APP_ID')
if not app_id:
    raise ValueError("WECHAT_APP_ID not set")
```

**Incorrect** (NEVER):
```yaml
api:
  app_id: "wx1234567890abcdef"  # HARDCODED - FORBIDDEN
```

### 5.3 Security Scanning

Run before commit:
```bash
python health_check.py --security
```

Check for:
- Hardcoded secrets
- SQL injection risks (string concatenation)
- Path traversal risks
- Dangerous functions (eval, exec, os.system)

### 5.4 High-Risk Scenarios

| Risk Level | Scenario | Review Points |
|------------|----------|---------------|
| CRITICAL | Database schema changes | Migration scripts, backward compatibility |
| HIGH | Message source parsing | Exception handling, XSS prevention, encoding |
| HIGH | File system operations | Path validation, permissions, disk full |
| MEDIUM | Flask route changes | Input validation, CSRF protection |

### 5.5 Screenshot Privacy

Before storing OCR results:
- Blur sensitive patterns (ID: `\d{17}[\dXx]`, phone: `1[3-9]\d{9}`)
- Configure `privacy.mask_patterns` in `config.yaml`
- Add watermark (user + timestamp) to Web display

---

## 6. AI Traceability

### 6.1 Code Marking Requirements

All non-trivial AI code (>10 lines or core logic) must have structured header:

**Simple (10-30 lines)**:
```python
# [AI-GENERATED] Date: 2026-02-03 | Task: Description
def function_name():
    pass
```

**Complex (30+ lines or core logic)**:
```python
# [AI-GENERATED] Date: 2026-02-03 | PromptHash: abc123
# [CONTEXT] Task: Description | Issue: #42
# [REVIEWED] By: reviewer | Date: 2026-02-03 | Status: VERIFIED
# [DEPENDENCIES] Requires: file.py#L1-L10
# [SAFETY] Checked: SQL injection, path traversal, exceptions

class ComplexClass:
    pass
```

### 6.2 Field Definitions

| Field | Description |
|-------|-------------|
| `PromptHash` | First 8 chars of prompt hash for traceability |
| `REVIEWED` | Manual review marker (reviewer, date, status) |
| `SAFETY` | Self-check for common risks |
| `DEPENDENCIES` | Related code locations |

### 6.3 High-Risk Review Requirements

| Risk Level | Scenario | Required Review |
|------------|----------|-----------------|
| CRITICAL | Database schema changes | Migration, compatibility, rollback |
| HIGH | Message parsing | Exception handling, XSS, encoding |
| HIGH | File operations | Path validation, permissions |
| MEDIUM | Flask routes | Input validation, response format |

### 6.4 AI Contribution Tracking

Record in `CHANGELOG.md` under `### AI Contributions`:

```markdown
### AI Contributions
- **Feature Name** (`file.py`): AI-generated, verified
- **Optimization** (`module.py`): AI-generated, needs manual tuning
```

### 6.5 Pre-Merge Checklist

- [ ] All AI code has `[AI-GENERATED]` marker
- [ ] High-risk code has `[REVIEWED]` marker
- [ ] Security code has `[SECURITY_REVIEWED]` marker
- [ ] Dependencies documented (`[DEPENDENCIES]`)

---

## 7. Checklist Templates

### 7.1 Pre-Commit Checklist

**Code Quality**:
- [ ] All modified files pass Pylance (0 errors)
- [ ] AI code has `[AI-GENERATED]` marker
- [ ] High-risk code has `[REVIEWED]` marker
- [ ] No hardcoded secrets (`health_check.py --security`)

**Documentation**:
- [ ] `CHANGELOG.md` updated (version, changes)
- [ ] `DEV_NOTES.md` updated (status, TODOs)
- [ ] Architecture docs updated (if changed)
- [ ] New config items documented

**Verification**:
- [ ] `python health_check.py` passes (DB, Web, sources)
- [ ] Manual test cases pass
- [ ] Rollback verified

**Cleanup**:
- [ ] Delete temp files (`*.tmp`, `test_*.py`, `debug_*.png`)
- [ ] No secrets in `git diff --cached`
- [ ] Type check baseline updated (if policy changed)

### 7.2 Session Start Commands

```bash
# 1. Read documentation
cat CHANGELOG.md UPGRADE.md DOCS/ARCHITECTURE.md DOCS/WORKFLOW.md DOCS/DEV_NOTES.md skills/README.md

# 2. Environment check
python scripts/pre_session_check.sh

# 3. Establish baseline
python health_check.py --establish-baseline
```

### 7.3 Emergency Rollback

```bash
# Soft rollback (switch script)
python monitor.py  # Use stable old version

# Hard rollback (switch version)
git stash
git checkout v0.3.0
python monitor.py
```

### 7.4 Common Tasks

| Task | Prompt Template |
|------|-----------------|
| Add feature | "Based on [module], add [feature]. Must: 1) Type annotations 2) Exception handling 3) Tests 4) Docs" |
| Fix bug | "Analyze [issue], fix [file]. Must: 1) Root cause 2) Repro test 3) No regression" |
| Refactor | "Refactor [module] for [goal]. Constraints: 1) Keep interfaces 2) Performance data 3) Update diagrams" |

### 7.5 Quick Commands

```bash
# Health check
python health_check.py
python health_check.py --security
python health_check.py --docs

# Version management
git tag
git tag -a v0.5.0 -m "Description"
git checkout v0.4.0

# Database
sqlite3 wechat_monitor.db .dump > backup.sql
sqlite3 wechat_monitor.db ".schema"

# Services
python monitor_v2.py  # Monitoring
python web_app.py     # Web interface
```

### 7.6 File Location Quick Reference

| File | Purpose |
|------|---------|
| `monitor.py` | Single-source monitoring (stable) |
| `monitor_v2.py` | Multi-source monitoring (main) |
| `web_app.py` | Web management |
| `health_check.py` | Health check script |
| `core/` | Core data structures |
| `sources/` | Message sources |
| `config.yaml` | Configuration |
| `CHANGELOG.md` | Version history |
| `UPGRADE.md` | Upgrade guides |
| `skills/` | Skill files |

---

**End of Reference Documentation**
