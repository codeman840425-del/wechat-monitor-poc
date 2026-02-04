# Reference: Development Workflow and Collaboration Standards

> **Merged from**: `DEV_PROTOCOL.md`, `WORKFLOW.md`  
> **Focus**: Development processes, workflows, error handling, testing  
> **Generated**: 2026-02-03

---

## Table of Contents

1. [Three-File Collaboration System](#1-three-file-collaboration-system)
2. [Development Workflow](#2-development-workflow)
3. [Error Handling Protocols](#3-error-handling-protocols)
4. [Self-Fix SOP](#4-self-fix-sop)
5. [Testing Procedures](#5-testing-procedures)
6. [Code Standards](#6-code-standards)
7. [Prohibited Actions](#7-prohibited-actions)

---

## 1. Three-File Collaboration System

### 1.1 System Overview

The project uses a **three-file + protocol** system for development transparency:

```
┌─────────────────────────────────────────────────────────────┐
│              DEVELOPMENT COLLABORATION SYSTEM                │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ITERATIVE_BOARD.md (Master Board)                          │
│  ├── Requirements management                                 │
│  ├── Step breakdown and roadmap                             │
│  ├── Multi-round iteration history                          │
│  └── Update: On requirement/status changes                  │
│                                                              │
│  ERROR_LOG.md (Error Archive)                               │
│  ├── All errors during development                          │
│  ├── Fix records and workarounds                            │
│  └── Update: Immediately when error occurs                  │
│                                                              │
│  STEP_MANUAL.md (Delivery Manual)                           │
│  ├── Test guide for current step                            │
│  ├── Acceptance criteria                                    │
│  └── Update: After self-fix, before delivery                │
│                                                              │
│  DEV_PROTOCOL.md (This Document)                            │
│  ├── Development process standards                          │
│  ├── Error capture protocols                                │
│  └── Update: Process improvements                           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Golden Rule

> **"No update to STEP_MANUAL.md = not complete. No ERROR_LOG.md entry = development negligence."**

---

## 2. Development Workflow

### 2.1 Complete Development Process (Step 0-4)

#### Step 0: Requirement Reception

**Actions**:
1. User provides requirement
2. Update `ITERATIVE_BOARD.md`:
   - Fill "Original Requirement" (paste user's words)
   - Fill "Clarified" (AI's understanding)
   - Break down into steps (3-7 steps)
3. Output step roadmap
4. Wait for user confirmation

**Template - ITERATIVE_BOARD.md**:
```markdown
## Current Requirement
**Original**: [User's original request]
**Clarified**: [AI's specific understanding]
**Status**: [analyzing/developing/testing/blocked/complete]
**Created**: [YYYY-MM-DD]
**Last Updated**: [YYYY-MM-DD]

## Step Roadmap (Overview)
- [ ] Step 1: [Name] | Deliver: [files] | Status: [pending/progress/ready/complete]
- [ ] Step 2: [Name] | Deliver: [files] | Status: [pending/progress/ready/complete]

**Current**: Step [X] - [current action]
```

#### Step 1: Development Phase (Coding + Error Capture)

**Actions**:
1. Write code
2. After each function/file: Use `dev_test` wrapper
3. **On ANY error**: Immediately record to `ERROR_LOG.md`
4. Continue development (don't stop for errors, record first)

**Error Recording Requirements**:
- SyntaxError → Record immediately
- ImportError → Record immediately
- NameError → Record immediately
- Runtime exception → Record immediately
- Type checking error → Record if checked
- Logic error (unexpected result) → Record

#### Step 2: Self-Fix Phase (Mandatory Before Delivery)

**Trigger**: After completing step coding

**Actions**:
1. Execute "Self-Fix SOP" (Phase 1-3)
2. Ensure all P0/P1 errors fixed or marked "needs user"
3. Generate self-fix report

**Do NOT proceed to Step 3 until self-fix complete**.

#### Step 3: Delivery Phase

**Actions**:
1. Update `ITERATIVE_BOARD.md`:
   - Mark current step "ready for test"
   - Update "Last Updated" timestamp

2. Write/Update `STEP_MANUAL.md`:
   - Test guide (Section 3)
   - Known issues (Section 4)
   - Self-fix report (in Section 4)

3. Output standard delivery message:

```text
✅ Step [X] development complete

📋 Iteration Board: ITERATIVE_BOARD.md (view overall progress)
📄 Error Log: ERROR_LOG.md (see development issues)
📖 Delivery Manual: STEP_MANUAL.md (how to test this step)

⛔ I am now paused, waiting for your test.

Please follow Section 3 of STEP_MANUAL.md for testing,
then tell me the results after filling out Section 5.
```

#### Step 4: Test Feedback Processing

**Actions**:
1. User provides test results
2. Update `ITERATIVE_BOARD.md`:
   - Append to "Iteration History" (Round N)
   - Record ERROR_LOG stats
   - Record user feedback
   - Record fix plan

3. Decision:
   - **If test failed**: Return to Step 1 (fix iteration)
   - **If test passed**: Mark step "complete", start Step 0 (next step)

### 2.2 Daily Development Routine

**First Conversation of Day**:
1. Read `ITERATIVE_BOARD.md`
2. Summarize current state in 3 sentences:
   - Current version/status
   - Active step and goal
   - Any blockers

**During Development**:
1. Write code
2. Use `dev_test` wrapper for testing
3. Record errors immediately
4. Continue to next part

**End of Development Session**:
1. Run self-fix SOP
2. Update STEP_MANUAL.md
3. Deliver with standard message

---

## 3. Error Handling Protocols

### 3.1 Mandatory Error Recording Scenarios

**Must Record Immediately**:

| Error Type | Example | Record To |
|-----------|---------|-----------|
| SyntaxError | `def func(:` | ERROR_LOG.md |
| ImportError | `ModuleNotFoundError` | ERROR_LOG.md |
| NameError | `undefined_variable` | ERROR_LOG.md |
| Runtime Exception | Crash, unhandled exception | ERROR_LOG.md |
| Type Checking | Pylance/pyright errors | ERROR_LOG.md |
| Logic Error | Wrong result, no exception | ERROR_LOG.md |

### 3.2 Error Log Template

```markdown
### Error #{auto-number} - {timestamp}
**Location**: [file.py:line_number]
**Type**: [SyntaxError/ImportError/NameError/TypeError/RuntimeError/LogicError]
**Error Message**:
```
[Complete traceback, last 5 lines minimum]
```
**Trigger Scenario**: [What AI was doing, e.g., "testing message parse function"]
**Root Cause Analysis**: [Why it happened, e.g., "forgot to import datetime"]
**Workaround**: [How bypassed, e.g., "temporarily wrapped in try-except"]
**Fix Status**: [pending/fixing/fixed/needs user/abandoned]
```

### 3.3 Error Classification

#### P0 - Critical (Blockers)
- **Types**: SyntaxError, ImportError, NameError
- **Priority**: Must fix immediately
- **Impact**: Code cannot run

#### P1 - Type Errors (High Priority)
- **Types**: TypeError, AttributeError
- **Priority**: Fix before delivery
- **Impact**: Runtime failures

#### P2 - Runtime Errors (Medium Priority)
- **Types**: ValueError, KeyError, IndexError
- **Priority**: Add defensive code
- **Impact**: Specific scenario failures

#### P3 - Logic Errors (Low Priority)
- **Types**: Wrong results, unexpected behavior
- **Priority**: Analyze, mark "needs user"
- **Impact**: Results don't match expectations

### 3.4 Error Wrapper Code

**dev_test Function**:

```python
import traceback
from datetime import datetime

def dev_test(test_name, func, *args, **kwargs):
    """Development test wrapper with automatic error recording"""
    try:
        result = func(*args, **kwargs)
        print(f"✅ {test_name} passed")
        return result
    except Exception as e:
        error_info = {
            "timestamp": datetime.now().isoformat(),
            "test_name": test_name,
            "error_type": type(e).__name__,
            "error_msg": str(e),
            "traceback": traceback.format_exc()[-500:],  # Last 500 chars
            "file": getattr(func, '__code__', None) and func.__code__.co_filename or "unknown",
            "line": getattr(func, '__code__', None) and func.__code__.co_firstlineno or 0,
        }
        
        print(f"\n❌ {test_name} failed")
        print(f"Error Type: {error_info['error_type']}")
        print(f"Error Message: {error_info['error_msg']}")
        print(f"Location: {error_info['file']}:{error_info['line']}")
        print("⚠️  MUST record to ERROR_LOG.md immediately\n")
        
        return None  # Indicate failure without stopping flow
```

**Usage**:
```python
# WRONG (not allowed)
result = parse_message(data)  # Silent failure

# CORRECT (required)
result = dev_test("message parse test", parse_message, data)
if result is None:
    # Error recorded, continue or mark blocked
    pass
```

---

## 4. Self-Fix SOP

### 4.1 Trigger

Execute after completing step coding, **BEFORE** writing `STEP_MANUAL.md`.

### 4.2 Phase 1: Error Analysis (5 minutes)

**Actions**:
1. Read all "pending" errors from `ERROR_LOG.md`
2. Classify each error (P0/P1/P2/P3)
3. Count by category:
   - P0-Critical: [N] errors
   - P1-Type: [N] errors
   - P2-Runtime: [N] errors
   - P3-Logic: [N] errors

**Classification Guide**:
```python
if error_type in ['SyntaxError', 'ImportError', 'NameError']:
    priority = 'P0-Critical'
elif error_type in ['TypeError', 'AttributeError']:
    priority = 'P1-Type'
elif error_type in ['ValueError', 'KeyError', 'IndexError']:
    priority = 'P2-Runtime'
else:
    priority = 'P3-Logic'
```

### 4.3 Phase 2: Auto-Fix (by Priority)

**For Each P0/P1 Error**:

1. **Diagnose**: Use traceback to locate exact line
2. **Fix** based on error type:

| Error Type | Fix Action |
|-----------|-----------|
| ImportError | Add missing import or install dependency |
| SyntaxError | Fix syntax issue |
| TypeError | Add type check or conversion |
| AttributeError | Check object initialization |

3. **Verify**: Re-run with `dev_test`
4. **Record**: Update `ERROR_LOG.md` status

**Fix Failure Handling**:
- If 3 attempts fail → Mark "needs user intervention"
- Record all attempted solutions in `ERROR_LOG.md`

### 4.4 Phase 3: Generate Fix Report

**In STEP_MANUAL.md Section 4**:

```markdown
## 4. Known Issues (From ERROR_LOG)

**Self-Fix Report**:
- Total errors found: [X]
- Auto-fixed successfully: [Y] (success rate [Z]%)
- Pending user confirmation: [N] (see below)

**Auto-Fixed** (no attention needed):
- ✅ Error #1: Import missing - Added import statement
- ✅ Error #2: Type mismatch - Added type conversion

**To Watch** (note during testing):
1. [Error #3]: May occur in [scenario], record if seen

**Needs User Intervention** (cannot auto-fix):
1. [Error #5]: Requires [resource/environment], cannot simulate
   - Attempted: [list of solutions tried]
   - Next: Need user to provide [resource]
```

---

## 5. Testing Procedures

### 5.1 Development Environment Setup

**Requirements**:
- Python 3.9+
- Windows 10/11 (Win32 API dependency)
- 4GB+ RAM
- 1GB+ disk space

**Installation**:
```bash
cd F:\opencode\wechat-monitor-poc\stage2
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Install Tesseract-OCR (Windows)
# Download: https://github.com/UB-Mannheim/tesseract/wiki
# Select Chinese language pack during install
```

**Verification**:
```bash
python health_check.py
```

Expected:
```
[OK] Type check: OK
[OK] Code quality: OK
[OK] Config file: OK
[OK] Database: OK
[OK] Web app: OK
[OK] Message source: OK

Summary: 6 passed, 0 warnings, 0 errors
```

### 5.2 Standard Test Cases

#### Test 1: Monitor Service Startup

**Purpose**: Verify service starts correctly

**Steps**:
```bash
python monitor_v2.py
```

**Expected Output**:
```
============================================================
Multi-Source Monitoring Service Started
============================================================
Message sources: 1
  - WeChat Desktop (platform: wechat_win)
============================================================
Press Ctrl+C to stop
```

**Verify**:
- [ ] Service starts without error
- [ ] WeChat window detected
- [ ] Keyword list displayed

#### Test 2: Keyword Matching

**Purpose**: Verify keyword detection

**Steps**:
1. Start monitor service
2. Send test message in monitored window: "客户要求退款，请处理"
3. Wait 5-10 seconds
4. Check console output

**Expected Output**:
```
✓ Matched keyword '退款': 客户要求退款，请处理...
  Written to database, ID: 1
```

**Verify**:
- [ ] Keyword "退款" detected
- [ ] Message saved to database
- [ ] Match log displayed

#### Test 3: Web Interface

**Purpose**: Verify web management

**Steps**:
```bash
python web_app.py
```

Open browser: http://127.0.0.1:5000

**Verify**:
- [ ] Dashboard shows statistics
- [ ] /messages shows message list
- [ ] /keywords allows keyword management

#### Test 4: Database Query

**Purpose**: Verify data storage

**Steps**:
```bash
python query.py recent 10
```

**Expected**:
```
+----+--------------+-----------+----------------------+---------------------+
| ID | Window       | Keyword   | Content              | Time                |
+====+==============+===========+======================+=====================+
|  1 | ...          | 退款      | 客户要求退款...      | 2026-02-03 10:30:15 |
+----+--------------+-----------+----------------------+---------------------+
```

### 5.3 Edge Case Testing

| Test Item | Operation | Expected |
|-----------|-----------|----------|
| Empty message | Send empty content | Not stored or marked empty |
| Long message | Send 1000 char message | Stored, web display truncated |
| Special chars | Send emoji, symbols | Stored correctly, no garbled text |
| Multi-keyword | Message with multiple keywords | Match first or all |
| Window closed | Close WeChat during monitoring | Prompt window unavailable, no crash |

### 5.4 Debugging Commands

**Log Monitoring**:
```bash
# Real-time log
tail -f monitor.log

# Error only
grep "ERROR" monitor.log

# Keyword matches
grep "Matched keyword" monitor.log
```

**Database Debugging**:
```bash
# SQLite CLI
sqlite3 wechat_monitor.db

# Common commands
.tables                  # Show tables
.schema messages         # Show messages schema
SELECT * FROM messages;  # View all messages
SELECT COUNT(*) FROM messages;  # Count
```

**Screenshot Debugging**:
```bash
# List screenshots
ls screenshots/

# Manual OCR test
python -c "
from PIL import Image
import pytesseract
img = Image.open('screenshots/xxx.png')
text = pytesseract.image_to_string(img, lang='chi_sim')
print(text)
"
```

---

## 6. Code Standards

### 6.1 Pre-Save Self-Check

**Before saving any file**:

```markdown
**File**: [path]
**Check Time**: [time]
- [ ] Import test: `python -c "import [module]"` passes
- [ ] Syntax check: `python -m py_compile [file]` passes
- [ ] Type check: `pyright [file]` (if configured)
- [ ] Runtime test: Core function callable without exception

**Errors Found**: [list or "none"]
**Recorded to ERROR_LOG**: [yes/no, number]
```

### 6.2 Exception Handling Template

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

### 6.3 Required Exception Types

| Operation | Catch Exception |
|-----------|----------------|
| Database | `sqlite3.Error` |
| File ops | `IOError`, `FileNotFoundError` |
| Network | `requests.RequestException` |
| OCR | `pytesseract.TesseractError` |

---

## 7. Prohibited Actions (Red Lines)

### 7.1 Never Do These

| # | Prohibition | Why |
|---|-------------|-----|
| 1 | Encounter error without recording to ERROR_LOG.md | Transparency violation |
| 2 | Deliver without self-fix | Quality violation |
| 3 | Say "test it" without STEP_MANUAL.md | Incomplete delivery |
| 4 | Write "vaguely remember an error" in ERROR_LOG.md | Insufficient info |
| 5 | Overwrite fixed error records | History lost |
| 6 | Use `as any` or `@ts-ignore` | Type safety violation |
| 7 | Hardcode secrets or paths | Security violation |
| 8 | Delete failing tests to "pass" | Integrity violation |

### 7.2 Commit Standards

**Never commit unless explicitly requested**.

**If committing**:
- Check for secrets in diff
- Follow commit message format: `[type]: description`
- Types: feat, fix, docs, style, refactor, test, chore

---

**End of Reference Documentation**
