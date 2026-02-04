# Project Guides - Versioning Standards

---
skill_id: project-guides
trigger_keywords: ["changelog", "upgrade", "version", "release"]
dependencies: ["skill-system"]
---

## Semantic Versioning
**Format**: `MAJOR.MINOR.PATCH`
- **MAJOR**: Breaking API changes
- **MINOR**: Features (backward-compatible)
- **PATCH**: Fixes (backward-compatible)

## CHANGELOG.md Format
```markdown
## [X.Y.Z] - YYYY-MM-DD

### Added
- **Feature** (file.py) - Description

### Breaking Changes
- **Change**: Old → New → Migration

### Git Tag
```bash
git tag -a vX.Y.Z -m "Description"
```
```

## UPGRADE.md Format
```markdown
## From X.Y.Z to A.B.C

### Prerequisites
- [ ] Backup DB: `cp wechat_monitor.db wechat_monitor.db.backup`
- [ ] Tag current: `git tag -a backup-$(date +%Y%m%d)`

### Steps
1. `git checkout vA.B.C`
2. `pip install -r requirements.txt`
3. [Migration steps]
4. `python health_check.py`

### Rollback
**Soft**: `python monitor.py` (old entry)
**Hard**: `git checkout vX.Y.Z && python monitor.py`
```

## Compatibility Matrix Template
| Version | monitor.py | monitor_v2.py | DB Changes | Config Changes |
|---------|-----------|--------------|-----------|---------------|
| v0.5.0 | ✅ | ✅ | +notifications | +notification |
| v0.4.0 | ✅ | ✅ | keywords | capture_region |

## Version Commands
```bash
git tag                          # List tags
git tag -a v0.5.0 -m "Desc"     # Create tag
git checkout v0.4.0             # Switch version
git describe --tags             # Current version
```

## See reference.md For
- Full CHANGELOG templates
- Complete upgrade procedures
- Version compatibility details
- Breaking change examples
