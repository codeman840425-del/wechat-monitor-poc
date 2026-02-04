# Operations Guides - Deployment & Monitoring

---
skill_id: operations-guides
trigger_keywords: ["deployment", "operations", "health check", "production"]
dependencies: ["skill-system"]
---

## Health Check
```bash
python health_check.py
python health_check.py --security
```
Components: Type → Code quality → Config → Database → Web app → Source

## Deployment

**Pre-Deploy**: `python health_check.py` passes, DB backed up, Secrets in env vars

**Deploy**:
```bash
git tag -a production-$(date +%Y%m%d) -m "Deploy"
cp wechat_monitor.db wechat_monitor.db.backup
git checkout v0.5.0
pip install -r requirements.txt
python health_check.py
python monitor_v2.py &
python web_app.py &
```

## Key Config
```yaml
monitor:
  interval: 10
  screenshot:
    retention_days: 30

database:
  data_retention_days: 90

ocr:
  lang: "chi_sim+eng"
  preprocess:
    scale: 2.0

logging:
  level: "INFO"
```

## Troubleshooting

| Issue | Check | Fix |
|-------|-------|-----|
| Window not found | WeChat running? | Start WeChat |
| OCR fails | Tesseract installed? | Install + chi_sim |
| No matches | Screenshots clear? | Adjust region |
| DB locked | Other process? | Kill process |

## Maintenance

Daily: `tail -f monitor.log`

Weekly: `sqlite3 wechat_monitor.db "SELECT COUNT(*) FROM messages;"`

Monthly: `sqlite3 wechat_monitor.db "VACUUM;"`

## Rollback
```bash
# Soft
python monitor.py

# Hard
git checkout v0.4.0
cp wechat_monitor.db.backup wechat_monitor.db
python monitor.py
```

## See reference.md For
Complete production config, database optimization, security operations
