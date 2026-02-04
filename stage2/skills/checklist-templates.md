---
skill_id: checklist-templates
trigger_keywords: ["检查清单", "checklist", "快速参考", "命令", "附录", "模板"]
dependencies: ["core-rules"]
context_window: 快速参考、检查清单、常用命令
---

# Checklist Templates - 检查清单与快速参考

**版本**: v2.0.0  
**日期**: 2026-02-03  
**状态**: 工具层（随时参考）

---

## 附录 A：检查清单（Checklist）

每次迭代结束、提交代码前，必须完成以下检查：

### A.1 代码质量检查
- [ ] 所有修改的文件通过 Pylance 类型检查（0 报错）
- [ ] AI 生成的代码包含 `[AI-GENERATED]` 标记头
- [ ] 高风险代码经过人工审查并标记 `[REVIEWED]`
- [ ] 无硬编码的绝对路径或敏感信息（运行 `health_check.py --security` 确认）

### A.2 文档同步检查
- [ ] `CHANGELOG.md` 已更新版本号和变更摘要
- [ ] `DEV_NOTES.md` 已更新当前迭代状态和待修复问题
- [ ] 若修改架构，`ARCHITECTURE.md` 已同步
- [ ] 新增配置项在文档中有说明（运行 `health_check.py --docs` 确认）

### A.3 功能验证检查
- [ ] `python health_check.py` 全部通过（数据库、Web 路由、消息源）
- [ ] 手动测试用例通过（参考 `WORKFLOW.md` 中的测试步骤）
- [ ] 回滚方案已验证（能从当前版本回退到上一稳定版）

### A.4 环境清理检查
- [ ] 删除调试用的临时文件（`*.tmp`, `test_*.py`, `debug_*.png`）
- [ ] 敏感数据未提交（检查 `git diff --cached` 中无真实密钥）
- [ ] `.typecheck_baseline.json` 已更新（如类型检查策略有变）

---

## 附录 B：快速参考卡（Quick Reference）

### 会话启动命令序列

```bash
# 1. 阅读文档（按顺序）
cat CHANGELOG.md UPGRADE.md DOCS/ARCHITECTURE.md DOCS/WORKFLOW.md DOCS/DEV_NOTES.md DOCS/RULES_FOR_OPENCODE.md

# 2. 环境检查
python scripts/pre_session_check.sh

# 3. 建立工作基线
python health_check.py --establish-baseline

# 4. 开始开发（按规则执行）
```

### 常见任务提示词模板

| 任务类型 | 提示词前缀模板 |
|---------|--------------|
| 新增功能 | "基于 [模块名] 的现有架构，在不破坏向后兼容的前提下，增加 [功能描述]。必须包含：1)类型注解 2)异常处理 3)单元测试 4)文档更新" |
| Bug 修复 | "分析 [问题描述]，修复位于 [文件] 的 Bug。要求：1)说明根因 2)提供最小复现测试 3)验证不引入回归问题" |
| 重构 | "重构 [模块] 以改善 [可读性/性能/可维护性]。约束：1)保持所有公开接口签名不变 2)提供性能对比数据 3)更新架构图" |

### 紧急回滚命令

```bash
# 软回滚（切换入口脚本）
python monitor.py  # 回退到稳定旧版

# 硬回滚（切换代码版本）
git stash  # 保存当前工作
git checkout v0.3.0  # 切换到上次稳定标签
python monitor.py
```

---

## 常用命令速查

### 健康检查

```bash
# 运行完整健康检查
python health_check.py

# 仅检查安全
python health_check.py --security

# 仅检查文档
python health_check.py --docs

# 建立类型检查基线
python health_check.py --establish-baseline
```

### 版本管理

```bash
# 查看所有版本标签
git tag

# 创建新标签
git tag -a v0.5.0 -m "版本描述"

# 切换到指定版本
git checkout v0.4.0

# 查看当前版本
git describe --tags
```

### 数据库操作

```bash
# 备份数据库
cp wechat_monitor.db wechat_monitor.db.backup.$(date +%Y%m%d)

# 导出 SQL
sqlite3 wechat_monitor.db .dump > backup.sql

# 从 SQL 恢复
sqlite3 wechat_monitor.db < backup.sql

# 查看表结构
sqlite3 wechat_monitor.db ".schema"

# 查看关键字
sqlite3 wechat_monitor.db "SELECT * FROM keywords;"
```

### 启动服务

```bash
# 旧版监控（稳定）
python monitor.py

# 新版监控（多源）
python monitor_v2.py

# Web 管理界面
python web_app.py

# 诊断工具
python diagnose_keywords.py
```

### 类型检查

```bash
# 安装 pyright
npm install -g pyright

# 运行类型检查
pyright

# 生成基线文件
pyright --outputjson > .typecheck_baseline.json
```

---

## 文件位置速查

| 文件/目录 | 用途 |
|----------|------|
| `monitor.py` | 单源监控旧版 |
| `monitor_v2.py` | 多源监控新版 |
| `web_app.py` | Web 管理界面 |
| `health_check.py` | 健康检查脚本 |
| `core/` | 核心数据结构 |
| `sources/` | 消息源实现 |
| `templates/` | HTML 模板 |
| `config.yaml` | 配置文件 |
| `wechat_monitor.db` | SQLite 数据库 |
| `CHANGELOG.md` | 版本变更记录 |
| `UPGRADE.md` | 升级指南 |
| `skills/` | Skill 文件目录 |

---

## 交叉引用

- 核心规则 → 参见 `core-rules.md`
- 代码质量 → 参见 `code-quality.md`
- 版本管理 → 参见 `version-control.md`
- 安全规范 → 参见 `security-guardrails.md`
- AI 溯源 → 参见 `ai-traceability.md`
