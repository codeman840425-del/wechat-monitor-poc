# Reference: CHANGELOG and UPGRADE Documentation Standards

> **Merged from**: `CHANGELOG.md`, `UPGRADE.md`  
> **Focus**: Format conventions, versioning rules, writing patterns  
> **Generated**: 2026-02-03

---

## Table of Contents

1. [CHANGELOG.md Standards](#1-changelogmd-standards)
2. [UPGRADE.md Standards](#2-upgrademd-standards)
3. [Versioning Rules](#3-versioning-rules)
4. [Format Templates](#4-format-templates)
5. [Writing Examples](#5-writing-examples)

---

## 1. CHANGELOG.md Standards

### 1.1 Document Header

```markdown
# Changelog

Format based on [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/),
versioning follows [Semantic Versioning](https://semver.org/lang/zh-CN/).

## [Unreleased]
```

### 1.2 Version Entry Structure

```markdown
## [X.Y.Z] - YYYY-MM-DD

### Added
- New features

### Changed
- Changes to existing functionality

### Deprecated
- Soon-to-be removed features

### Removed
- Removed features

### Fixed
- Bug fixes

### Security
- Security improvements
```

### 1.3 Feature Entry Format

**Basic feature**:
```markdown
- **Feature Name** (file.py) - Brief description
```

**Complex feature with sub-items**:
```markdown
- **Feature Name** (module.py)
  - Sub-feature 1 with details
  - Sub-feature 2 with details
  - Configuration: `config_key: value`
```

### 1.4 Breaking Changes Format

```markdown
### Breaking Changes
- **Change Description**: What changed
  - Old behavior/format: Description
  - New behavior/format: Description
  - Migration: How to migrate existing data/config
```

### 1.5 Git Tag Documentation

```markdown
### Git Tag
```bash
git tag -a vX.Y.Z -m "Version description"
```
```

### 1.6 Version Compatibility Matrix

```markdown
## Version Compatibility Matrix

| Version | Entry Script | web_app.py | Database Changes | Config Changes |
|---------|-------------|-----------|------------------|----------------|
| v0.4.0 | monitor_v2.py | ✅ | None | capture_region format |
| v0.3.0 | monitor.py | ✅ | keywords table | None |
| v0.2.0 | monitor.py | ❌ | messages table | capture_region added |
| v0.1.0 | monitor.py | ❌ | Initial schema | Base config |

## Compatibility Notes

- v0.1.0 → v0.2.0: Fully compatible, update config.yaml only
- v0.2.0 → v0.3.0: Auto database upgrade
- v0.3.0 → v0.4.0: Reconfigure capture_region (format change)
```

---

## 2. UPGRADE.md Standards

### 2.1 Document Structure

```markdown
# Upgrade Guide

## View Current Version
```bash
git tag
git branch
git log --oneline -5
```

## From X.Y.Z to A.B.C (Feature Name)

### Upgrade Steps

1. **Update Code**
   ```bash
   git checkout vA.B.C
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Migrate Data/Config** (if needed)
   - Specific migration steps

4. **Verify**
   ```bash
   python health_check.py
   ```

### Breaking Changes
- List of incompatible changes
- Migration instructions

### Rollback Procedure
[Soft/Hard rollback instructions]
```

### 2.2 Version-Specific Upgrade Sections

**Format**:
```markdown
## From 0.3.x to 0.4.x (Multi-Source Architecture)

### Upgrade Steps

1. **Step Name**
   ```bash
   # Commands
   ```
   - Expected output
   - Verification method

2. **Configuration Migration**
   **Old format**: `[left, top, right, bottom]` (absolute)
   **New format**: `[offset_x, offset_y, width, height]` (relative)
   **Migration**:
   ```bash
   # Delete and re-select
   python monitor_v2.py
   # Or calculate: width = right - left
   ```

### Rollback Options
| Current | Target | Method | Notes |
|---------|--------|--------|-------|
| v0.4.0 | v0.3.0 | Soft: `python monitor.py` | capture_region differs |
| v0.4.0 | v0.3.0 | Hard: `git checkout v0.3.0` | Full rollback |
```

### 2.3 Rollback Documentation

**Quick Rollback Section**:
```markdown
## Rollback to Previous Version

### Quick Rollback
```bash
# View available versions
git tag

# Checkout target
git checkout v0.3.0

# Restore database (if needed)
cp backup.db wechat_monitor.db

# Start service
python monitor.py
```

### Version-Specific Notes
| Current | Target | Recommended | Notes |
|---------|--------|-------------|-------|
| v0.4.0 | v0.3.0 | Soft | Entry script only |
| v0.4.0 | v0.2.0 | Hard | DB structure incompatible |
| v0.3.0 | v0.2.0 | Hard | Web interface unavailable |
```

### 2.4 Database Backup/Restore

```markdown
### Database Backup and Recovery

**Backup**:
```bash
# Direct file copy
cp wechat_monitor.db wechat_monitor.db.backup.$(date +%Y%m%d)

# SQL export
sqlite3 wechat_monitor.db .dump > backup.sql
```

**Restore**:
```bash
# Direct file restore
cp wechat_monitor.db.backup.YYYYMMDD wechat_monitor.db

# SQL import
sqlite3 wechat_monitor.db < backup.sql
```
```

---

## 3. Versioning Rules

### 3.1 Semantic Versioning (SemVer)

**Format**: `MAJOR.MINOR.PATCH` (e.g., `v0.4.1`)

| Component | Increment When | Example |
|-----------|----------------|---------|
| **MAJOR** | Incompatible API changes | `v0.4.0` → `v1.0.0` |
| **MINOR** | Backward-compatible features | `v0.3.0` → `v0.4.0` |
| **PATCH** | Backward-compatible fixes | `v0.4.0` → `v0.4.1` |

### 3.2 Version Examples

| Version | Type | Description |
|---------|------|-------------|
| `v0.4.0` | MINOR | Multi-source monitoring (feature) |
| `v0.4.1` | PATCH | Screenshot calculation fix |
| `v0.5.0` | MINOR | Real-time notification system |
| `v1.0.0` | MAJOR | Official stable release |

### 3.3 Pre-Release Checklist

Before tagging a version:

- [ ] Version number updated in code files
- [ ] `CHANGELOG.md` updated with new version section
- [ ] Breaking changes documented with migration steps
- [ ] Git tag created: `git tag -a vX.Y.Z -m "Description"`
- [ ] All tests pass: `python health_check.py`
- [ ] `UPGRADE.md` updated (if breaking changes exist)

### 3.4 Version Tagging Commands

```bash
# Create annotated tag
git tag -a v0.5.0 -m "Multi-source monitoring + notifications"

# Push tags to remote
git push --tags

# View all tags
git tag

# View current version
git describe --tags

# Checkout specific version
git checkout v0.4.0
```

---

## 4. Format Templates

### 4.1 CHANGELOG Entry Template

```markdown
## [X.Y.Z] - YYYY-MM-DD

### Added
- **Feature Name** (primary_file.py)
  - Sub-feature 1: Description
  - Sub-feature 2: Description
  - Configuration: New config options

### Changed
- **Module**: Description of change
  - Before: Old behavior
  - After: New behavior

### Fixed
- **Bug Description**: Root cause and fix
  - Issue: What was wrong
  - Fix: How it was resolved

### Breaking Changes
- **Change**: What breaks
  - Migration: How to adapt

### Git Tag
```bash
git tag -a vX.Y.Z -m "Version description"
```
```

### 4.2 UPGRADE Section Template

```markdown
## From X.Y.Z to A.B.C (Feature Summary)

### Prerequisites
- [ ] Current version backed up: `git tag -a backup-$(date +%Y%m%d)`
- [ ] Database backed up: `cp wechat_monitor.db wechat_monitor.db.backup`
- [ ] Read target version CHANGELOG

### Upgrade Steps

1. **Update Code**
   ```bash
   git fetch --tags
   git checkout vA.B.C
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Migrate Configuration/Data**
   - Step 1: Description
   - Step 2: Description

4. **Verify Installation**
   ```bash
   python health_check.py
   ```

### Breaking Changes
| Change | Impact | Migration |
|--------|--------|-----------|
| Change 1 | Description | Migration steps |
| Change 2 | Description | Migration steps |

### Rollback Procedure
**Soft rollback** (use old entry):
```bash
python monitor.py  # Old entry script
```

**Hard rollback** (switch version):
```bash
git checkout vX.Y.Z
cp wechat_monitor.db.backup wechat_monitor.db
python monitor.py
```
```

---

## 5. Writing Examples

### 5.1 Good Feature Descriptions

**Example 1 - New Feature**:
```markdown
### Added
- **Real-time Notification System** (notification_system.py, websocket_manager.py)
  - Async notification architecture based on asyncio
  - Support for 6 notification channels:
    - DingTalk robot (DingTalkChannel)
    - WeCom robot (WeComChannel)
    - Email (EmailChannel)
    - Desktop notification (DesktopChannel)
    - File log (FileChannel)
    - Console (ConsoleChannel)
  - Notification rule engine: Route by keyword to different channels
  - Cooldown mechanism: Prevent spam notifications
  - Async sending: Non-blocking to monitoring flow
```

**Example 2 - Breaking Change**:
```markdown
### Breaking Changes
- **capture_region format changed**: Absolute coordinates → Offset + dimensions
  - Old format: `[left, top, right, bottom]` (relative to window)
  - New format: `[offset_x, offset_y, width, height]` (offset + size)
  - Migration:
    - Delete config and re-select: `python monitor_v2.py`
    - Or manually calculate: `width = right - left`, `height = bottom - top`
  - Example: `[100, 100, 500, 400]` → `[100, 100, 400, 300]`
```

**Example 3 - Bug Fix**:
```markdown
### Fixed
- **Screenshot region calculation**: Fixed relative coordinate error
  - Issue: `right < left` calculation error in region selection
  - Fix: Corrected coordinate calculation logic in `monitor_v2.py`
  - Added safety checks for region bounds
```

### 5.2 Good Upgrade Instructions

**Example - Configuration Migration**:
```markdown
### Upgrade Steps

3. **Update screenshot region configuration (IMPORTANT)**

   **Configuration format change**:
   - Old: `capture_region: [left, top, right, bottom]` (absolute coordinates)
   - New: `capture_region: [offset_x, offset_y, width, height]` (offset + dimensions)
   
   **Migration methods**:
   
   Option 1 - Re-select (Recommended):
   ```bash
   # Delete old config
   # Edit config.yaml, remove capture_region line
   
   # Run monitor to re-select
   python monitor_v2.py
   ```
   
   Option 2 - Manual conversion:
   ```yaml
   # Old value: [100, 100, 500, 400] (left=100, top=100, right=500, bottom=400)
   # New value: [100, 100, 400, 300] (offset_x=100, offset_y=100, width=400, height=300)
   
   capture_region: [100, 100, 400, 300]
   ```
```

### 5.3 Version Compatibility Matrix

```markdown
## Compatibility Matrix

| Version | monitor.py | monitor_v2.py | web_app.py | Database Schema | Config Format |
|---------|-----------|--------------|-----------|----------------|---------------|
| v0.5.0 | ✅ | ✅ | ✅ | +notifications | +notification block |
| v0.4.0 | ✅ | ✅ | ✅ | keywords table | capture_region v2 |
| v0.3.0 | ✅ | ❌ | ✅ | keywords table | capture_region v1 |
| v0.2.0 | ✅ | ❌ | ❌ | messages only | +capture_region |
| v0.1.0 | ✅ | ❌ | ❌ | messages only | base |

**Legend**:
- ✅ Supported
- ❌ Not available
- `+` Added in this version
```

---

## 6. Quick Reference

### Common Git Commands

```bash
# Create version tag
git tag -a v0.5.0 -m "Real-time notification system"

# Push tags
git push origin v0.5.0
git push --tags

# List tags
git tag -l "v0.4*"

# Delete tag (if needed)
git tag -d v0.5.0
git push origin :refs/tags/v0.5.0

# Checkout version
git checkout v0.4.0

# Create branch from tag
git checkout -b hotfix-v0.4.1 v0.4.0
```

### Database Commands

```bash
# Backup
cp wechat_monitor.db wechat_monitor.db.backup.$(date +%Y%m%d)

# Export
sqlite3 wechat_monitor.db .dump > wechat_monitor_$(date +%Y%m%d).sql

# Import
sqlite3 wechat_monitor.db < backup.sql

# Check tables
sqlite3 wechat_monitor.db ".tables"

# Check schema
sqlite3 wechat_monitor.db ".schema messages"
```

---

**End of Reference Documentation**
