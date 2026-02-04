---
title: 开发工作流程文档
category: 项目管理
version: v1.0.0
date: 2026-02-03
status: 活跃
related_files: [health_check.py, monitor_v2.py, web_app.py]
---

# 开发工作流程文档

**项目**: wechat-monitor-poc  
**版本**: v0.4.0  
**最后更新**: 2026-02-03

---

## 1. 开发环境准备

### 1.1 环境要求

- **Python**: 3.9 或更高版本
- **操作系统**: Windows 10/11（当前版本依赖 Win32 API）
- **内存**: 建议 4GB 以上
- **磁盘**: 建议 1GB 可用空间（用于数据库和截图）

### 1.2 安装步骤

```bash
# 1. 克隆/进入项目目录
cd F:\opencode\wechat-monitor-poc\stage2

# 2. 创建虚拟环境（推荐）
python -m venv venv
venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 安装 Tesseract-OCR（Windows）
# 下载地址: https://github.com/UB-Mannheim/tesseract/wiki
# 安装时勾选中文语言包

# 5. 验证安装
python health_check.py
```

### 1.3 配置文件

复制配置模板（如需要）：

```bash
# config.yaml 已存在，按需修改
cp config.yaml config.yaml.backup
```

关键配置项：
- `database.db_path`: 数据库路径
- `monitor.interval`: 监控间隔（秒）
- `keywords.list`: 监控关键字列表

---

## 2. 标准开发流程

### 2.1 新功能开发流程

```
1. 阅读文档
   ├── CHANGELOG.md（了解版本历史）
   ├── DOCS/ARCHITECTURE.md（了解架构）
   ├── DOCS/DEV_NOTES.md（了解当前状态）
   └── skills/core-rules.md（了解规范）

2. 需求分析
   ├── 明确功能目标
   ├── 确定影响范围
   └── 评估技术方案

3. 编码实现
   ├── 遵循代码规范（skills/code-quality.md）
   ├── 添加类型注解
   └── 添加 AI-GENERATED 标记（如适用）

4. 本地测试
   ├── 运行 health_check.py
   ├── 功能测试（见第3节）
   └── 边界情况测试

5. 文档更新
   ├── 更新 CHANGELOG.md
   ├── 更新 DOCS/DEV_NOTES.md
   └── 更新相关 Skill 文档（如需要）

6. 提交代码
   ├── git add
   ├── git commit（遵循提交规范）
   └── git tag（如发布版本）
```

### 2.2 代码提交规范

**提交信息格式**:
```
[type]: [subject]

[body]

[footer]
```

**类型 (type)**:
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式（不影响功能）
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具相关

**示例**:
```
feat: 添加钉钉消息源支持

- 实现 DingTalkSource 类
- 支持钉钉群消息监控
- 更新配置文档

Closes #123
```

---

## 3. 测试流程

### 3.1 健康检查（必做）

```bash
python health_check.py
```

**预期结果**:
```
[OK] 类型检查: OK
[OK] 代码质量: OK
[OK] 配置文件: OK
[OK] 数据库: OK
[OK] Web 应用: OK
[OK] 消息源: OK

总结: 6 项通过, 0 项警告, 0 项错误
```

### 3.2 功能测试用例

#### 测试 1：监控服务启动

**目的**: 验证监控服务能正常启动

**步骤**:
```bash
# 1. 启动监控
python monitor_v2.py
```

**预期输出**:
```
============================================================
多源监控服务启动
============================================================
消息源数量: 1
  - 微信桌面 (平台: wechat_win)
============================================================
按 Ctrl+C 停止服务
```

**验证点**:
- [ ] 服务启动无报错
- [ ] 正确识别微信窗口
- [ ] 显示监控关键字列表

#### 测试 2：关键字匹配

**目的**: 验证关键字匹配功能正常

**步骤**:
1. 确保监控服务运行中
2. 在被监控的微信窗口发送测试消息：
   ```
   客户要求退款，请处理
   ```
3. 观察控制台输出

**预期输出**:
```
✓ 匹配到关键字 '退款': 客户要求退款，请处理...
  已写入数据库，ID: 1
```

**验证点**:
- [ ] 正确识别关键字"退款"
- [ ] 消息写入数据库
- [ ] 控制台显示匹配日志

#### 测试 3：Web 界面访问

**目的**: 验证 Web 管理界面正常

**步骤**:
```bash
# 1. 启动 Web 服务
python web_app.py

# 2. 浏览器访问
open http://127.0.0.1:5000
```

**验证点**:
- [ ] Dashboard 显示统计数据
- [ ] /messages 显示消息列表
- [ ] /keywords 可管理关键字

#### 测试 4：数据库查询

**目的**: 验证数据正确存储

**步骤**:
```bash
# 查询最近10条消息
python query.py recent 10

# 或直接使用 sqlite3
sqlite3 wechat_monitor.db "SELECT * FROM messages ORDER BY id DESC LIMIT 5;"
```

**预期结果**:
- 显示刚才的测试消息
- 关键字字段为"退款"
- 时间戳为当前时间

### 3.3 边界情况测试

| 测试项 | 操作 | 预期结果 |
|-------|------|---------|
| 空消息 | 发送空内容 | 不存储或标记为空 |
| 超长消息 | 发送1000字消息 | 正常存储，Web显示截断 |
| 特殊字符 | 发送 emoji、符号 | 正常存储，不乱码 |
| 多关键字 | 消息含多个关键字 | 匹配第一个或全部 |
| 窗口关闭 | 监控中关闭微信窗口 | 提示窗口不可用，不崩溃 |

---

## 4. 调试技巧

### 4.1 日志查看

```bash
# 实时监控日志
tail -f monitor.log

# 查看错误日志
grep "ERROR" monitor.log

# 查看关键字匹配记录
grep "匹配到关键字" monitor.log
```

### 4.2 数据库调试

```bash
# 进入 SQLite 命令行
sqlite3 wechat_monitor.db

# 常用命令
.tables                  # 查看所有表
.schema messages         # 查看 messages 表结构
SELECT * FROM messages;  # 查看所有消息
SELECT COUNT(*) FROM messages;  # 统计消息数
```

### 4.3 截图调试

```bash
# 查看截图目录
ls screenshots/

# 手动测试 OCR
python -c "
from PIL import Image
import pytesseract
img = Image.open('screenshots/xxx.png')
text = pytesseract.image_to_string(img, lang='chi_sim')
print(text)
"
```

---

## 5. 发布流程

### 5.1 版本发布检查清单

- [ ] 所有测试用例通过
- [ ] `health_check.py` 无错误
- [ ] `CHANGELOG.md` 已更新
- [ ] `UPGRADE.md` 已更新（如有破坏性变更）
- [ ] 版本号已更新（`monitor_v2.py` 等文件）
- [ ] Git Tag 已创建

### 5.2 发布步骤

```bash
# 1. 确保所有测试通过
python health_check.py

# 2. 更新版本号（如需要）
# 编辑 monitor_v2.py 等文件中的版本信息

# 3. 更新 CHANGELOG.md
# 添加新版本记录

# 4. 提交代码
git add .
git commit -m "release: v0.x.x"

# 5. 打 Tag
git tag -a v0.x.x -m "版本说明"

# 6. 推送
git push
git push --tags
```

---

## 6. 故障排查

### 6.1 常见问题速查

| 问题 | 排查步骤 | 解决方案 |
|-----|---------|---------|
| 找不到微信窗口 | 1. 确认微信已登录<br>2. 检查窗口标题配置 | 不配置 `target_window_title`，手动选择 |
| OCR 识别失败 | 1. 检查 Tesseract 安装<br>2. 检查语言包 | 安装中文语言包，配置 `tesseract_cmd` |
| 数据库锁定 | 1. 检查是否有其他进程占用<br>2. 检查权限 | 关闭其他实例，检查文件权限 |
| Web 界面无法访问 | 1. 检查端口占用<br>2. 检查防火墙 | 更换端口，关闭防火墙测试 |
| 关键字不匹配 | 1. 检查截图是否清晰<br>2. 手动测试 OCR | 调整截图区域，优化 OCR 配置 |

### 6.2 紧急回滚

```bash
# 软回滚（切换入口脚本）
python monitor.py  # 使用旧版

# 硬回滚（切换代码版本）
git stash
git checkout v0.x.x
python monitor.py
```

---

## 7. 相关文档

- [ARCHITECTURE.md](ARCHITECTURE.md) - 系统架构说明
- [DEV_NOTES.md](DEV_NOTES.md) - 开发笔记、决策记录
- [UPGRADE.md](../UPGRADE.md) - 版本升级指南
- [CHANGELOG.md](../CHANGELOG.md) - 版本变更记录
- [HEALTH_CHECK.md](../HEALTH_CHECK.md) - 健康检查说明
- [skills/README.md](../skills/README.md) - 开发规范体系

---

**维护者**: AI Assistant  
**最后更新**: 2026-02-03
