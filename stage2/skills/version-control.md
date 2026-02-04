---
skill_id: version-control
trigger_keywords: ["版本", "Git", "tag", "回滚", "升级", "checkout", "changelog"]
dependencies: ["core-rules"]
context_window: 版本管理、回滚策略、升级流程
---

# Version Control - 版本管理与回滚策略

**版本**: v2.0.0  
**日期**: 2026-02-03  
**状态**: 基础层（版本管理任务时加载）

---

## 4. 版本管理与回滚策略

### 4.1 Git Tag 与版本号管理

- 对每个达到"稳定、可日常使用"状态的版本打 Git Tag，例如：  
  - `v0.2.0`：单源监控 + 区域选择稳定版  
  - `v0.3.0`：加入 Web 管理界面的稳定版  
  - `v0.4.0`：多源监控架构稳定版  

- 在 `CHANGELOG.md` 中维护：  
  - 版本号（Tag）  
  - 发布日期（可选）  
  - 主要变更列表  
  - 是否包含破坏性变更（配置/数据库结构变更等）

### 4.2 软回滚（入口脚本级别）

- 永远保留旧入口脚本：  
  - `monitor.py`：作为兼容旧结构的稳定方案；  
  - `monitor_v2.py`：作为多源架构的新版主入口。  

- 在 `UPGRADE.md` 中明确写出：  
  - 最新版本推荐使用的脚本（例如：`monitor_v2.py`）；  
  - 遇到问题时如何"先换回 `monitor.py`"进行软回滚。  

### 4.3 硬回滚（切换代码版本）

在 `UPGRADE.md` 中提供回滚示例命令：

```bash
# 查看所有版本标签
git tag

# 回滚到指定稳定版本
git checkout v0.3.0
```

**文档中必须说明**：
- 回滚后应使用哪个入口脚本（如 `python monitor.py`）；
- 回滚前是否建议备份数据库（例如通过 `sqlite3 wechat_monitor.db .dump`）；
- 回滚版本对新配置/新字段的处理（通常旧版会忽略多余配置字段）。

---

## 版本升级流程

### 升级前检查清单

- [ ] 当前版本已打 Tag 备份
- [ ] 数据库已备份
- [ ] 配置文件已备份
- [ ] 已阅读目标版本的 UPGRADE.md
- [ ] 已确认回滚方案

### 标准升级步骤

```bash
# 1. 备份当前版本
git tag -a production-backup-$(date +%Y%m%d) -m "升级前备份"
cp wechat_monitor.db wechat_monitor.db.backup.$(date +%Y%m%d)

# 2. 查看可用版本
git tag

# 3. 切换到新版本
git checkout v0.4.0

# 4. 安装新依赖（如有）
pip install -r requirements.txt

# 5. 运行健康检查
python health_check.py

# 6. 如检查通过，启动服务
python monitor_v2.py
```

### 版本兼容性矩阵

| 版本 | monitor.py | monitor_v2.py | web_app.py | 数据库变更 |
|------|-----------|--------------|-----------|-----------|
| v0.1.0 | ✅ | ❌ | ❌ | 初始版本 |
| v0.2.0 | ✅ | ❌ | ❌ | 无 |
| v0.3.0 | ✅ | ❌ | ✅ | 新增 keywords 表 |
| v0.4.0 | ✅ | ✅ | ✅ | capture_region 格式变化 |

---

## 回滚操作指南

### 软回滚（推荐）

当新版本出现问题，但不想切换代码版本时：

```bash
# 停止当前服务
Ctrl+C

# 使用旧版入口脚本
python monitor.py
```

**适用场景**：
- 配置兼容性问题
- 新功能不稳定，需要快速恢复服务
- 数据库结构未变更

### 硬回滚

当需要完全回到旧版本时：

```bash
# 1. 停止服务
Ctrl+C

# 2. 保存当前工作（如有未提交修改）
git stash

# 3. 切换到旧版本
git checkout v0.3.0

# 4. 恢复数据库（如需要）
cp wechat_monitor.db.backup.20250203 wechat_monitor.db

# 5. 启动旧版服务
python monitor.py
```

**适用场景**：
- 数据库结构变更导致不兼容
- 配置文件格式变化
- 需要完全回到旧版本环境

---

## 版本号规范

本项目使用 [Semantic Versioning](https://semver.org/lang/zh-CN/)：

- **MAJOR**（主版本号）：不兼容的 API 修改
- **MINOR**（次版本号）：向下兼容的功能性新增
- **PATCH**（修订号）：向下兼容的问题修正

**示例**：
- `v0.4.0`：新增多源监控架构（功能性新增）
- `v0.4.1`：修复截图区域计算 bug（问题修正）
- `v1.0.0`：正式发布，API 稳定（主版本发布）

---

## 交叉引用

- 项目结构 → 参见 `core-rules.md` 第 2 章
- 代码质量 → 参见 `code-quality.md` 第 3 章
- 安全规范 → 参见 `security-guardrails.md` 第 9 章
- 健康检查 → 参见 `production-health.md` 第 10 章
- 检查清单 → 参见 `checklist-templates.md` 附录 A
