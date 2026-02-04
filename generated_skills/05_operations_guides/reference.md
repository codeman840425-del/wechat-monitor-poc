# Reference: Operations, Deployment, and Production Configuration

> **Merged from**: `HEALTH_CHECK.md`, `生产配置建议.md`  
> **Focus**: Operations procedures, deployment guides, production config  > **Generated**: 2026-02-03

---

## Table of Contents

1. [Health Check System](#1-health-check-system)
2. [Production Deployment](#2-production-deployment)
3. [Configuration Reference](#3-configuration-reference)
4. [Performance Optimization](#4-performance-optimization)
5. [Troubleshooting Guide](#5-troubleshooting-guide)
6. [Maintenance Procedures](#6-maintenance-procedures)

---

## 1. Health Check System

### 1.1 Overview

The health check system (`health_check.py`) validates system state before and during operation.

### 1.2 Running Health Checks

**Basic Check**:
```bash
python health_check.py
```

**Security Scan**:
```bash
python health_check.py --security
```

**Documentation Check**:
```bash
python health_check.py --docs
```

**Establish Baseline**:
```bash
python health_check.py --establish-baseline
```

### 1.3 Check Components

#### Type Check

**Scope**:
- `monitor.py`
- `monitor_v2.py`
- `web_app.py`
- `core/` directory
- `sources/` directory

**Tools**:
- Primary: `pyright` (if installed)
- Fallback: Basic import/syntax checks

**Target**: 0 errors on critical modules

**Known Type Warnings** (documented, non-blocking):
| File | Line | Issue | Impact |
|------|------|-------|--------|
| `sources/wechat_screen.py` | 112 | window_element may be None | Runtime checked |
| `sources/wechat_screen.py` | 118 | window_element may be None | Runtime checked |
| `sources/window_screen.py` | 46 | class_name_patterns type | Runtime normal |
| `monitor.py` | 1396 | heartbeat attribute | Runtime normal |

#### Code Quality Check

**Validations**:
- Syntax errors in Python files
- Critical file existence
- Import validation
- Basic code structure

#### Config File Check

**Requirements**:
- `config.yaml` exists
- Valid YAML format
- Required fields present:
  - `database.db_path`
  - `monitor.interval`
  - `ocr.lang`

**Directory Checks**:
- Screenshot directory exists and writable
- Log directory writable

#### Database Check

**Connection**:
- Connect to `wechat_monitor.db`
- Verify file permissions

**Schema Validation**:
```sql
-- Required tables
SELECT name FROM sqlite_master WHERE type='table';
-- Expected: messages, keywords, monitor_status

-- Required fields in messages
PRAGMA table_info(messages);
-- Expected: id, window_title, message_text, matched_keyword, screenshot_path, created_at

-- Required fields in keywords
PRAGMA table_info(keywords);
-- Expected: id, word, enabled, created_at
```

#### Web Application Check

**Import Test**:
```python
from web_app import app
```

**Route Validation**:
- `/` - Dashboard
- `/messages` - Message list
- `/keywords` - Keyword management
- `/images/<path>` - Screenshot serving
- `/api/webhook/wechat/<source>` - Webhook receiver

**Template Check**:
- `templates/base.html` exists
- `templates/dashboard.html` exists
- `templates/messages.html` exists
- `templates/keywords.html` exists

#### Message Source Check

**Core Modules**:
```python
from core.message import ChatMessage
from sources.base import BaseMessageSource
from sources.wechat_screen import WeChatScreenSource
```

**Safe Poll Test**:
- Initialize sources without entering infinite loops
- Dry-run capability verification

### 1.4 Health Check Output Format

**Status Indicators**:
```
[OK]   Check Name: Description    # Passed
[WARN] Check Name: Description    # Warning, can continue
[ERR]  Check Name: Description    # Error, should fix
```

**Summary**:
```
Summary: X passed, Y warnings, Z errors
```

### 1.5 Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All passed or warnings only |
| 1 | Errors found |

### 1.6 Extending Health Checks

**Adding New Check**:

```python
def _check_new_feature(self):
    print("[X/6] Checking new feature...")
    
    try:
        # Check logic
        from my_module import my_function
        result = my_function()
        
        if result:
            self.results.append(CheckResult(
                name="New Feature",
                status="OK",
                message="New feature check passed"
            ))
        else:
            self.results.append(CheckResult(
                name="New Feature",
                status="WARNING",
                message="New feature not configured"
            ))
    except Exception as e:
        self.results.append(CheckResult(
            name="New Feature",
            status="ERROR",
            message=f"New feature check failed: {e}"
        ))
```

**In run_all_checks()**:
```python
def run_all_checks(self):
    print("=== Health Check ===")
    self._check_type_checking()      # 1/6
    self._check_code_quality()       # 2/6
    self._check_config_file()        # 3/6
    self._check_database()           # 4/6
    self._check_web_app()            # 5/6
    self._check_message_source()     # 6/6
    self._check_new_feature()        # 7/6 (new)
    # ...
```

---

## 2. Production Deployment

### 2.1 Pre-Deployment Checklist

**Code**:
- [ ] Version tagged in git
- [ ] All tests pass
- [ ] No uncommitted changes (or documented)

**Configuration**:
- [ ] Production config validated
- [ ] Environment variables set
- [ ] No hardcoded secrets

**Data**:
- [ ] Database backed up
- [ ] Screenshot directory exists
- [ ] Log directory writable

**System**:
- [ ] Python 3.9+ installed
- [ ] Dependencies installed
- [ ] Tesseract-OCR installed with Chinese language

### 2.2 Deployment Steps

**Step 1: Backup**
```bash
# Git tag
git tag -a production-$(date +%Y%m%d) -m "Production deployment"

# Database backup
cp wechat_monitor.db wechat_monitor.db.production.$(date +%Y%m%d)

# Config backup
cp config.yaml config.yaml.backup
```

**Step 2: Update Code**
```bash
# Pull latest
git pull

# Or checkout specific version
git checkout v0.5.0
```

**Step 3: Install Dependencies**
```bash
pip install -r requirements.txt
```

**Step 4: Validate**
```bash
python health_check.py
```

**Step 5: Configure**
```bash
# Edit production config
nano config.yaml

# Set environment variables
export WECHAT_API_KEY="..."
```

**Step 6: Start Services**

**Option A: Foreground (testing)**:
```bash
# Terminal 1
python monitor_v2.py

# Terminal 2
python web_app.py
```

**Option B: Background (production)**:
```bash
# Using nohup
nohup python monitor_v2.py > monitor.log 2>&1 &
echo $! > monitor.pid

nohup python web_app.py > webapp.log 2>&1 &
echo $! > webapp.pid
```

**Option C: Windows Service**:
```powershell
# Using NSSM (Non-Sucking Service Manager)
nssm install WeChatMonitor "C:\Python39\python.exe" "C:\app\monitor_v2.py"
nssm start WeChatMonitor
```

### 2.3 Post-Deployment Verification

**Health Check**:
```bash
python health_check.py
```

**Service Check**:
```bash
# Check processes
ps aux | grep python

# Check ports
netstat -an | grep 5000  # Web interface

# Check logs
tail -20 monitor.log
tail -20 webapp.log
```

**Functional Test**:
1. Access web interface: http://localhost:5000
2. Check dashboard loads
3. Test message list
4. Test keyword management
5. Send test message, verify capture

### 2.4 Rollback Procedure

**Quick Rollback**:
```bash
# Stop services
kill $(cat monitor.pid)
kill $(cat webapp.pid)

# Restore database
cp wechat_monitor.db.production.YYYYMMDD wechat_monitor.db

# Restore code
git checkout v0.4.0

# Restart
python monitor_v2.py
```

---

## 3. Configuration Reference

### 3.1 Complete Production Config

```yaml
# ==================== Database ====================
database:
  db_path: "./wechat_monitor.db"
  data_retention_days: 90        # Keep 90 days of messages
  enable_vacuum: true            # Auto-vacuum for performance

# ==================== Monitoring ====================
monitor:
  interval: 10                   # Poll every 10 seconds
  target_window_title: ""        # Empty = manual selection
  
  screenshot:
    save_screenshots: true
    save_directory: "./screenshots"
    retention_days: 30           # Keep 30 days of screenshots
    quality: 85                  # JPEG quality (0-100)

# ==================== OCR ====================
ocr:
  tesseract_cmd: ""              # Empty = use system PATH
  lang: "chi_sim+eng"           # Chinese + English
  config: "--oem 3 --psm 6"     # Tesseract configuration
  
  preprocess:
    enabled: true
    scale: 2.0                   # Scale factor for better OCR
    contrast: false              # Disable contrast adjustment
    sharpen: false               # Disable sharpening
  
  chat_area:
    left_crop: 0.28              # Crop 28% from left
    top_crop: 0.09               # Crop 9% from top
    right_crop: 0.03             # Crop 3% from right
    bottom_crop: 0.14            # Crop 14% from bottom

# ==================== Keywords ====================
keywords:
  list:
    # Transaction keywords
    - "付款"
    - "支付"
    - "转账"
    - "退款"
    - "打款"
    
    # Order keywords
    - "订单"
    - "下单"
    - "发货"
    - "物流"
    
    # Complaint keywords
    - "投诉"
    - "问题"
    - "异常"
    - "纠纷"
    
    # Price keywords
    - "价格"
    - "报价"
    - "费用"
    - "金额"
    
    # Business keywords
    - "合同"
    - "发票"
    - "售后"
    - "紧急"
  
  match_mode: "contain"          # Options: contain, exact, fuzzy
  case_sensitive: false
  fuzzy_threshold: 0.7           # For fuzzy mode

# ==================== Logging ====================
logging:
  level: "INFO"                  # DEBUG, INFO, WARNING, ERROR
  log_file: "./monitor.log"
  console_output: true
  max_size_mb: 50                # Rotate when 50MB
  backup_count: 5                # Keep 5 backups

# ==================== Web Interface ====================
web:
  host: "127.0.0.1"              # Bind address
  port: 5000                     # Port
  debug: false                   # Never true in production

# ==================== Notification ====================
notification:
  enabled: true
  
  rules:
    - name: "Critical Alerts"
      keywords: ["投诉", "纠纷", "索赔"]
      channels: ["dingtalk", "email"]
      priority: "CRITICAL"
      cooldown: 300                # 5 minutes
    
    - name: "Refund Alerts"
      keywords: ["退款", "退钱", "退货"]
      channels: ["wecom"]
      priority: "HIGH"
      cooldown: 60
    
    - name: "Order Notifications"
      keywords: ["订单", "下单", "购买"]
      channels: ["desktop"]
      priority: "NORMAL"
      cooldown: 0
  
  channels:
    dingtalk:
      enabled: false
      webhook_url: "https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN"
      secret: ""
    
    wecom:
      enabled: false
      webhook_url: "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY"
    
    email:
      enabled: false
      smtp_server: "smtp.qq.com"
      smtp_port: 587
      username: ""
      password: ""
      to_addresses: []
    
    desktop:
      enabled: true
      duration: 5
    
    file:
      enabled: true
      path: "./notifications.log"
    
    console:
      enabled: true

# ==================== Advanced ====================
advanced:
  deduplication:
    enabled: true
    time_window: 120               # Seconds
    similarity_threshold: 0.85     # Hash similarity
  
  performance:
    screenshot_quality: 85
    ocr_timeout: 15                # Seconds
    max_messages_per_scan: 100
```

### 3.2 Config Value Ranges

| Parameter | Min | Max | Default | Recommended |
|-----------|-----|-----|---------|-------------|
| monitor.interval | 1 | 3600 | 5 | 10 |
| screenshot.retention_days | 1 | 365 | 7 | 30 |
| database.data_retention_days | 1 | 3650 | 30 | 90 |
| ocr.preprocess.scale | 1.0 | 4.0 | 2.0 | 2.0 |
| keywords.fuzzy_threshold | 0.0 | 1.0 | 0.7 | 0.7 |
| logging.max_size_mb | 1 | 500 | 50 | 50 |

### 3.3 Environment Variables

**Security-sensitive values** (do not hardcode):

```bash
# WeChat API (if used)
export WECHAT_APP_ID=""
export WECHAT_APP_SECRET=""
export WECHAT_TOKEN=""

# DingTalk
export DINGTALK_WEBHOOK=""
export DINGTALK_SECRET=""

# Email
export SMTP_USERNAME=""
export SMTP_PASSWORD=""
```

**In config.yaml**:
```yaml
api:
  app_id: ""  # Uses WECHAT_APP_ID env var
```

---

## 4. Performance Optimization

### 4.1 CPU Optimization

**High CPU Usage Solutions**:

1. **Increase poll interval**:
   ```yaml
   monitor:
     interval: 30  # Seconds
   ```

2. **Limit messages per scan**:
   ```yaml
   advanced:
     performance:
       max_messages_per_scan: 50
   ```

3. **Optimize OCR**:
   ```yaml
   ocr:
     preprocess:
       scale: 1.5  # Reduce from 2.0
   ```

4. **Enable deduplication**:
   ```yaml
   advanced:
     deduplication:
       enabled: true
       similarity_threshold: 0.90  # Higher = skip more
   ```

### 4.2 Memory Optimization

**Reducing Memory Usage**:

1. **Don't keep screenshots in memory**:
   ```python
   # Process and release immediately
   img = capture_screenshot()
   text = ocr_image(img)
   del img  # Explicitly release
   ```

2. **Batch database operations**:
   ```python
   # Instead of individual inserts
   batch_insert(messages, batch_size=100)
   ```

3. **Limit query results**:
   ```sql
   -- Use LIMIT
   SELECT * FROM messages ORDER BY id DESC LIMIT 100;
   ```

### 4.3 Disk Optimization

**Reducing Disk Usage**:

1. **Don't save screenshots**:
   ```yaml
   monitor:
     screenshot:
       save_screenshots: false
   ```

2. **Reduce retention**:
   ```yaml
   monitor:
     screenshot:
       retention_days: 7
   
   database:
     data_retention_days: 30
   ```

3. **Compress old screenshots**:
   ```bash
   # Find and compress screenshots older than 7 days
   find screenshots/ -name "*.png" -mtime +7 -exec gzip {} \;
   ```

4. **Database vacuum**:
   ```bash
   sqlite3 wechat_monitor.db "VACUUM;"
   ```

### 4.4 Database Optimization

**Indexes**:
```sql
-- Essential indexes
CREATE INDEX idx_messages_time ON messages(created_at);
CREATE INDEX idx_messages_keyword ON messages(matched_keyword);
CREATE INDEX idx_messages_window ON messages(window_title);
```

**Query Optimization**:
```sql
-- Fast recent messages
SELECT * FROM messages 
WHERE created_at > datetime('now', '-1 day')
ORDER BY created_at DESC
LIMIT 100;

-- Fast keyword stats
SELECT matched_keyword, COUNT(*) 
FROM messages 
WHERE created_at > datetime('now', '-7 days')
GROUP BY matched_keyword;
```

**Maintenance**:
```bash
# Weekly vacuum
sqlite3 wechat_monitor.db "VACUUM;"

# Analyze for query planner
sqlite3 wechat_monitor.db "ANALYZE;"
```

---

## 5. Troubleshooting Guide

### 5.1 WeChat Window Issues

#### Problem: No Windows Found

**Symptoms**:
```
No WeChat windows found
```

**Diagnosis**:
```bash
# Check WeChat process
ps aux | grep WeChat

# Check window handles
python -c "
import uiautomation
windows = uiautomation.GetRootControl().GetChildren()
for w in windows:
    if '微信' in w.Name:
        print(f'{w.Name}: {w.Handle}')
"
```

**Solutions**:
1. Ensure WeChat is running and logged in
2. Use Windows desktop version (not web)
3. Remove `target_window_title` to manually select
4. Run as administrator (if permission issues)

#### Problem: Window Becomes Unavailable

**Symptoms**:
```
Window not available, skipping capture
```

**Causes**:
- Window minimized
- Window closed
- WeChat logged out

**Solutions**:
1. Keep window visible (not minimized)
2. Disable screen lock
3. Check WeChat login status

### 5.2 OCR Issues

#### Problem: OCR Not Working

**Symptoms**:
```
OCR failed: tesseract is not installed
```

**Diagnosis**:
```bash
# Check Tesseract
tesseract --version

# Check language packs
ls "C:\Program Files\Tesseract-OCR\tessdata\chi_sim.traineddata"
```

**Solutions**:
1. Install Tesseract-OCR
2. Install Chinese language pack
3. Add to PATH or specify in config
4. Restart terminal/session

#### Problem: Poor Recognition Rate

**Diagnosis**:
```bash
# Check screenshot quality
ls screenshots/
# View latest screenshot

# Manual OCR test
python -c "
from PIL import Image
import pytesseract
img = Image.open('screenshots/latest.png')
print(pytesseract.image_to_string(img, lang='chi_sim'))
"
```

**Solutions**:
1. Adjust crop region (`ocr.chat_area`)
2. Increase scale factor (but slower)
3. Ensure window is fully visible
4. Check Tesseract version (5.x recommended)

### 5.3 Database Issues

#### Problem: Database Locked

**Symptoms**:
```
sqlite3.OperationalError: database is locked
```

**Causes**:
- Multiple processes accessing DB
- Previous crash left lock

**Solutions**:
```bash
# Check for lock file
ls wechat_monitor.db-journal
ls wechat_monitor.db-wal

# Kill other processes
lsof wechat_monitor.db

# If corrupted, restore from backup
cp wechat_monitor.db.backup wechat_monitor.db
```

#### Problem: Disk Full

**Diagnosis**:
```bash
df -h
du -sh screenshots/
du -sh wechat_monitor.db
```

**Solutions**:
1. Clean old screenshots
2. Reduce retention days
3. Vacuum database
4. Move to larger disk

### 5.4 Keyword Matching Issues

#### Problem: No Matches

**Diagnosis**:
```bash
# Check keywords in database
sqlite3 wechat_monitor.db "SELECT * FROM keywords;"

# Check monitor using correct keywords
python diagnose_keywords.py

# Test match manually
python -c "
from database import DatabaseManager
from monitor_v2 import KeywordFilter
db = DatabaseManager('./wechat_monitor.db')
keywords = db.get_keywords_from_db(enabled_only=True)
kf = KeywordFilter(keywords)
print(kf.check('测试退款消息'))
"
```

**Solutions**:
1. Verify keywords in database
2. Check keywords enabled
3. Test match mode (contain vs exact)
4. Add more keyword variations

### 5.5 Web Interface Issues

#### Problem: Cannot Access

**Diagnosis**:
```bash
# Check if running
ps aux | grep web_app

# Check port
netstat -an | grep 5000

# Check firewall
iptables -L | grep 5000
```

**Solutions**:
1. Start web_app: `python web_app.py`
2. Check port not in use: `lsof -i :5000`
3. Check firewall rules
4. Try different port: `python web_app.py --port 5001`

#### Problem: Template Not Found

**Symptoms**:
```
jinja2.exceptions.TemplateNotFound: dashboard.html
```

**Solutions**:
```bash
# Check templates exist
ls templates/

# Re-clone if missing
git checkout -- templates/
```

---

## 6. Maintenance Procedures

### 6.1 Daily Checks

**Automated**:
```bash
# Health check
python health_check.py

# Check disk space
df -h

# Check logs for errors
grep ERROR monitor.log | tail -5
```

**Manual**:
- [ ] Services running
- [ ] Web interface accessible
- [ ] Recent messages captured
- [ ] No error alerts

### 6.2 Weekly Maintenance

**Database**:
```bash
# Check size
ls -lh wechat_monitor.db

# Count records
sqlite3 wechat_monitor.db "SELECT COUNT(*) FROM messages;"

# Check for old data
sqlite3 wechat_monitor.db "SELECT COUNT(*) FROM messages WHERE created_at < datetime('now', '-30 days');"
```

**Screenshots**:
```bash
# Count screenshots
ls screenshots/ | wc -l

# Check size
du -sh screenshots/

# Clean old screenshots (if retention enabled)
# Automatic via config
```

**Logs**:
```bash
# Rotate if large
ls -lh monitor.log

# Archive old logs
tar czf logs-$(date +%Y%m%d).tar.gz monitor.log.*
```

### 6.3 Monthly Maintenance

**Database Optimization**:
```bash
# Vacuum
sqlite3 wechat_monitor.db "VACUUM;"

# Analyze
sqlite3 wechat_monitor.db "ANALYZE;"

# Integrity check
sqlite3 wechat_monitor.db "PRAGMA integrity_check;"
```

**Full Backup**:
```bash
# Database
sqlite3 wechat_monitor.db .dump > backup-$(date +%Y%m).sql

# Screenshots
tar czf screenshots-$(date +%Y%m).tar.gz screenshots/

# Config
cp config.yaml config-$(date +%Y%m).yaml
```

**Review**:
- [ ] Check error logs for patterns
- [ ] Review keyword effectiveness
- [ ] Verify backup procedures
- [ ] Update documentation

### 6.4 Automation Scripts

**Daily Health Check** (cron):
```bash
#!/bin/bash
# /etc/cron.daily/wechat-monitor-health

cd /path/to/project
python health_check.py > /var/log/wechat-monitor-health.log 2>&1

if [ $? -ne 0 ]; then
    echo "Health check failed" | mail -s "WeChat Monitor Alert" admin@example.com
fi
```

**Weekly Report**:
```bash
#!/bin/bash
# weekly-report.sh

DB="wechat_monitor.db"
REPORT="weekly-report-$(date +%Y%m%d).txt"

echo "Weekly Report - $(date)" > $REPORT
echo "========================" >> $REPORT

echo "Messages this week:" >> $REPORT
sqlite3 $DB "SELECT COUNT(*) FROM messages WHERE created_at > datetime('now', '-7 days');" >> $REPORT

echo "Top keywords:" >> $REPORT
sqlite3 $DB "SELECT matched_keyword, COUNT(*) FROM messages WHERE created_at > datetime('now', '-7 days') GROUP BY matched_keyword ORDER BY COUNT(*) DESC LIMIT 5;" >> $REPORT

echo "Database size:" >> $REPORT
ls -lh $DB >> $REPORT

cat $REPORT | mail -s "Weekly WeChat Monitor Report" admin@example.com
```

---

**End of Reference Documentation**
