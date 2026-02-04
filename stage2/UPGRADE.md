# 升级指南

本文档说明如何从一个版本升级到另一个版本，以及如何回滚到之前的稳定版本。

---

## 查看当前版本

```bash
# 查看 Git Tag
git tag

# 查看当前分支/提交
git branch
git log --oneline -5
```

---

## 从 0.1.x 升级到 0.2.x（区域选择功能）

### 升级步骤

1. **更新代码**
   ```bash
   git pull
   # 或切换到 v0.2.0 tag
   git checkout v0.2.0
   ```

2. **安装依赖**（无新增依赖）

3. **更新配置文件**
   - 在 `config.yaml` 中添加区域选择相关配置：
   ```yaml
   monitor:
     capture_region: []  # 空数组表示首次启动时手动选择
     always_reselect_region: false
     force_reselect_region: false
   ```

4. **启动监控**
   ```bash
   python monitor.py
   ```
   - 首次启动会弹出区域选择窗口
   - 选择完成后会自动保存到配置

### 回滚方法

如需回滚到 v0.1.0：
```bash
git checkout v0.1.0
python monitor.py
```

---

## 从 0.2.x 升级到 0.3.x（Web 管理界面）

### 升级步骤

1. **更新代码**
   ```bash
   git checkout v0.3.0
   ```

2. **安装新依赖**
   ```bash
   pip install -r requirements.txt
   ```
   - 新增依赖：Flask

3. **数据库自动升级**
   - 首次启动 `web_app.py` 或 `monitor.py` 时会自动创建新表
   - 无需手动操作

4. **启动 Web 管理界面**
   ```bash
   python web_app.py
   ```

5. **访问 Web 界面**
   - Dashboard: http://127.0.0.1:5000/
   - 消息列表: http://127.0.0.1:5000/messages
   - 关键字管理: http://127.0.0.1:5000/keywords

6. **迁移关键字（重要）**
   - 通过 Web 界面的 `/keywords` 页面重新添加关键字
   - 或者运行初始化脚本将 config.yaml 中的关键字导入数据库

### 回滚方法

**软回滚**（推荐）：继续使用旧版监控脚本
```bash
# 保持当前代码版本，但使用旧版监控
python monitor.py
```

**硬回滚**（切换到旧版本）：
```bash
git checkout v0.2.0
python monitor.py
```

**注意**：回滚后 Web 管理界面不可用

---

## 从 0.3.x 升级到 0.4.x（多源监控架构）

### 升级步骤

1. **更新代码**
   ```bash
   git checkout v0.4.0
   ```

2. **检查关键字迁移**
   ```bash
   python diagnose_keywords.py
   ```
   - 确认数据库中的关键字列表正确
   - 如有缺失，通过 Web 界面 `/keywords` 补充

3. **更新截图区域配置（重要）**
   
   **配置格式变化**：
   - 旧版：`capture_region: [left, top, right, bottom]`（绝对坐标）
   - 新版：`capture_region: [offset_x, offset_y, width, height]`（偏移+宽高）
   
   **迁移方法**：
   - 删除 `config.yaml` 中的 `capture_region` 配置
   - 运行新版监控，重新选择区域：
   ```bash
   python monitor_v2.py
   ```
   - 或者在配置中手动计算：
     - 旧值：`[100, 100, 500, 400]`（left=100, top=100, right=500, bottom=400）
     - 新值：`[100, 100, 400, 300]`（offset_x=100, offset_y=100, width=400, height=300）

4. **启动新版监控**
   ```bash
   python monitor_v2.py
   ```
   - 观察启动日志中的"从数据库加载 X 个关键字"
   - 确认"关键字过滤器初始化完成"显示的关键字列表正确

### 回滚方法

**软回滚**（推荐）：切换回旧版监控脚本
```bash
# 保持当前代码版本，但使用旧版监控
python monitor.py
```
- 旧版仍然可用，但无法使用多源监控功能
- 关键字会从数据库加载（与新版兼容）

**硬回滚**（切换到 v0.3.0）：
```bash
git checkout v0.3.0
python monitor.py
# 或启动 Web 界面
python web_app.py
```

**注意**：
- 如果已使用新版的 `capture_region` 格式，回滚后需要重新配置区域
- 数据库中的关键字在两个版本间兼容

---

## 回滚到上一稳定版本

### 快速回滚命令

```bash
# 1. 查看可用版本
git tag

# 2. 回滚到指定版本（例如 v0.3.0）
git checkout v0.3.0

# 3. 使用旧版监控脚本
python monitor.py
```

### 各版本回滚建议

| 当前版本 | 回滚目标 | 推荐方式 | 注意事项 |
|---------|---------|---------|---------|
| v0.4.0 | v0.3.0 | 软回滚：`python monitor.py` | capture_region 格式可能需要调整 |
| v0.4.0 | v0.2.0 | 硬回滚：`git checkout v0.2.0` | 数据库表结构不兼容，需备份数据 |
| v0.3.0 | v0.2.0 | 硬回滚：`git checkout v0.2.0` | Web 界面不可用 |
| v0.3.0 | v0.1.0 | 硬回滚：`git checkout v0.1.0` | 数据库结构不兼容 |

### 数据库备份与恢复

**备份数据库**：
```bash
# 方式1：直接复制文件
cp wechat_monitor.db wechat_monitor.db.backup.$(date +%Y%m%d)

# 方式2：导出 SQL
sqlite3 wechat_monitor.db .dump > backup.sql
```

**恢复数据库**：
```bash
# 方式1：直接恢复文件
cp wechat_monitor.db.backup.20250203 wechat_monitor.db

# 方式2：从 SQL 导入
sqlite3 wechat_monitor.db < backup.sql
```

---

## 版本兼容性矩阵

| 功能 | v0.1.0 | v0.2.0 | v0.3.0 | v0.4.0 |
|------|--------|--------|--------|--------|
| monitor.py | ✅ | ✅ | ✅ | ✅ |
| monitor_v2.py | ❌ | ❌ | ❌ | ✅ |
| web_app.py | ❌ | ❌ | ✅ | ✅ |
| 数据库 keywords 表 | ❌ | ❌ | ✅ | ✅ |
| 多源监控 | ❌ | ❌ | ❌ | ✅ |
| 区域选择 | ❌ | ✅ | ✅ | ✅ |

---

## 故障排查

### 升级后关键字丢失

```bash
# 检查数据库中的关键字
python diagnose_keywords.py

# 如果为空，从配置文件导入
python -c "
from web_app import init_default_keywords
init_default_keywords()
"
```

### 升级后截图失败

```bash
# 检查 capture_region 配置
python -c "
import yaml
with open('config.yaml') as f:
    config = yaml.safe_load(f)
    print(config['monitor']['capture_region'])
"

# 如果格式不对，删除后重新运行监控程序
```

### 回滚后数据库错误

```bash
# 检查数据库版本
sqlite3 wechat_monitor.db "SELECT name FROM sqlite_master WHERE type='table';"

# 如果缺少表，需要恢复备份或重新初始化
```

---

## 推荐升级路径

对于生产环境，建议按以下路径升级：

1. **备份当前版本**
   ```bash
   git tag -a production-backup-$(date +%Y%m%d) -m "生产环境备份"
   cp wechat_monitor.db wechat_monitor.db.production
   ```

2. **在测试环境验证新版本**
   ```bash
   git checkout v0.4.0
   python monitor_v2.py
   ```

3. **确认无误后升级生产环境**
   ```bash
   git checkout v0.4.0
   cp wechat_monitor.db.production wechat_monitor.db
   python monitor_v2.py
   ```

4. **保留回滚能力**
   - 至少保留最近 2 个版本的备份
   - 记录当前使用的版本号
