---
skill_id: core-rules
trigger_keywords: ["启动", "会话", "项目结构", "代码规范", "沟通", "协作"]
dependencies: []
context_window: 所有开发会话的基础规范，必须首先加载
---

# Core Rules - 核心基础规范

**版本**: v2.0.0  
**日期**: 2026-02-03  
**状态**: 强制加载（所有会话）

---

## 1. 会话开启与长期记忆

### 1.1 启动前必须阅读的文件

每次开始新的开发会话（尤其是新实例）前，必须按顺序阅读并理解以下文件：

1. `CHANGELOG.md` - 版本变更记录
2. `UPGRADE.md` - 升级指南
3. `DOCS/ARCHITECTURE.md` - 架构文档（如存在）
4. `DOCS/WORKFLOW.md` - 工作流程（如存在）
5. `DOCS/DEV_NOTES.md` - 开发笔记
6. `skills/README.md` - Skill 系统说明
7. `skills/core-rules.md`（本文件）- 核心规范

**阅读后总结要求**（不超过 10 行）：
- 当前项目版本/状态  
- 已有的主要功能模块和数据流（截图 → OCR → 关键字匹配 → 入库 → Web 展示）  
- 当前迭代的开发目标（由用户在对话中给出）  

### 1.2 文档同步更新约定

每完成一轮重要改动（包括但不限于：新功能、新脚本、重大 bug 修复），必须同步：

1. **更新 `CHANGELOG.md`**：记录版本号 + 关键变更  
2. **更新 `DOCS/DEV_NOTES.md`**：记录当前迭代状态、TODO、已知问题  
3. **如有架构或流程变化**：更新  
   - `DOCS/ARCHITECTURE.md`（模块、数据流变更）  
   - `DOCS/WORKFLOW.md`（开发/测试流程变更）  

**目标**：下次会话只需读取这些文档，即可恢复完整上下文，无需重述历史对话。

### 1.3 记忆冲突解决机制

当新记忆与旧记忆冲突时（如："使用库 X" vs "移除库 X"），必须在 `DEV_NOTES.md` 中显式标注冲突解决决策：

```markdown
## 记忆冲突记录

**冲突日期**: 2026-02-03  
**冲突内容**: 
- 旧记忆 (2026-01-15): 使用 Pillow 进行截图处理（monitor.py）
- 新记忆 (2026-02-03): 使用 mss 库提升截图性能（monitor_v2.py）

**决策**: 保留两者，monitor.py 保持 Pillow（稳定版），monitor_v2.py 使用 mss（实验性）
**影响**: 截图保存格式从 PNG 变为 JPG，需在升级指南中说明
```

---

## 2. 项目结构与代码规范

### 2.1 目录与职责划分

- **`monitor.py`**  
  - 单源监控旧版本（截图 + OCR + 关键字 + SQLite）  
  - 始终保留，作为稳定回滚入口  

- **`monitor_v2.py`**  
  - 多源监控新版（统一 `ChatMessage` + `MessageSource` + 多窗口/多平台）  
  - 后续演进的主要入口脚本  

- **`core/`**  
  - 核心数据结构、公共逻辑（如 `ChatMessage`、统计工具等）  

- **`sources/`**  
  - `sources/base.py`：消息源接口/基类（`MessageSource` 等）  
  - `sources/wechat_screen.py`：微信桌面 OCR 源  
  - `sources/wechat_api.py`：微信客服/API 源（Webhook 等）  
  - `sources/window_screen.py`：通用窗口截图源  
  - 其它新消息源统一放在此目录下  

- **`web_app.py`**  
  - Flask Web 管理界面  
  - 功能：Dashboard、消息列表、关键字管理、截图预览、（将来）平台/源过滤等  

- **`DOCS/`**  
  - `ARCHITECTURE.md`：整体架构、模块、数据流（待创建）  
  - `WORKFLOW.md`：开发流程、启动方式、测试用例（待创建）  
  - `DEV_NOTES.md`：当前迭代记录、TODO、已知问题  
  - `ITERATIVE_BOARD.md`：迭代看板、需求管理  
  - `STEP_MANUAL.md`：步骤交付手册  
  - `LIST.md`：文档索引和规范

- **`skills/`** - 开发规范体系（已拆分原 RULES_FOR_OPENCODE.md）
  - `core-rules.md`：本文件 - 核心基础规范
  - `code-quality.md`：代码质量与类型规范
  - `version-control.md`：版本管理与回滚策略
  - `security-guardrails.md`：安全红线与敏感信息防护
  - `ai-traceability.md`：AI 代码溯源与审查
  - `checklist-templates.md`：检查清单与快速参考

新增功能时，应优先在上述既定位置扩展，不随意新增新的顶级脚本或散乱模块。

### 2.2 代码风格与最佳实践

- **命名规范**（PEP 8）：  
  - 函数/变量/模块：`snake_case`（小写 + 下划线）  
  - 类名：`PascalCase`（首字母大写的驼峰）  

- **类型注解**：  
  - 所有新函数和新类的公开接口必须提供类型注解。  
  - 避免滥用 `Any`，只有在无法精确定义类型且有明确理由时才使用，并在 `DEV_NOTES` 中记录。  
  - 对可能为 `None` 的变量使用 `Optional[...]`，并在使用前做显式 `is not None` 检查。

- **Flask 路由返回**：  
  - 所有路由函数必须返回 Flask 支持的 `ResponseReturnValue`：  
    - 正常分支：`render_template(...)`、`jsonify(...)` 或字符串  
    - 错误分支：统一使用 `abort(...)` 或 `make_response(...)`  
  - 禁止返回 `None` 或裸 tuple（如 `("error", 500)`），禁止存在"隐式返回 None"的路径。

- **AI 代码标记**（详见 ai-traceability.md）：  
  所有 AI 生成的非 trivial 代码（超过 10 行或涉及核心业务逻辑）必须包含结构化注释头。

### 2.3 配置与常量

- 禁止在代码中硬编码路径、秘钥、敏感参数和行为开关。  
- 所有配置统一由配置文件（如 `config.yaml`）或数据库管理。  
- 引入新配置项时必须：  
  - 在 `ARCHITECTURE.md` / `WORKFLOW.md` 里说明用途、默认值和对旧版本的影响；  
  - 以"向后兼容"为原则设计（新增字段，不随意更改已有字段的含义）。

---

## 5. 与用户协作的沟通约定

### 5.1 任务定义与设计沟通

在进行任何非 trivially 小的改动前，先输出简短设计方案，包括：

- 计划修改的文件/模块列表；
- 数据流、接口会发生哪些变化（例如新增 `ChatMessage` 字段、改变消息源初始化方式）；
- 是否影响配置文件或数据库结构。

**未经用户确认，不进行大规模重构**或与当前任务无关的"顺手改进"，除非是明显的 bug 修复或安全问题。

### 5.2 错误记录与收尾清理

开发过程中遇到暂时无法立刻修复的错误（包括类型错误、运行时异常、LSP 限制等）时：

- 不要直接忽视或只在终端显示；
- 需要在 `DOCS/DEV_NOTES.md` 中维护一个"待修复问题"列表，内容包括：
  - 文件 + 行号
  - 报错信息摘要
  - 当前影响范围（是否影响运行，还是仅静态检查告警）

**每个迭代结束前，进行一次集中"收尾"阶段**：
- 尽量清理这些积累的问题；
- 再次运行类型检查和健康检查，恢复到"健康状态 + 0 类型报错"的基线。

---

## 6. 标准启动提示（供用户在新会话中使用）

每次新建会话、准备继续开发此项目时，用户可以粘贴以下提示作为开场：

```text
这是 wechat-monitor-poc 项目。
请你在开始任何分析和修改之前，按顺序阅读以下文件：
1）CHANGELOG.md - 版本变更记录
2）UPGRADE.md - 升级指南
3）DOCS/DEV_NOTES.md - 开发笔记（当前状态）
4）DOCS/LIST.md - 文档索引和规范
5）skills/README.md - Skill 系统说明
6）skills/core-rules.md - 核心基础规范（本文件）

阅读后，用不超过 10 行总结当前项目状态和本轮开发目标的理解，并严格遵守 skills/ 目录下的协作与开发规范。
```

### 6.1 环境自检命令（补充）

在正式开发前，执行以下环境验证：

```bash
#!/bin/bash
# scripts/pre_session_check.sh

echo "=== OpenCode 会话启动前检查 ==="

# 1. Python 版本检查
python -c "import sys; assert sys.version_info >= (3, 9), 'Python 3.9+ required'"

# 2. 核心依赖版本快照
python -c "
import flask, PIL, pytesseract, sqlite3
print(f'Environment OK: Flask {flask.__version__}, Pillow {PIL.__version__}')
"

# 3. 类型检查基线对比
if [ -f .typecheck_baseline.json ]; then
    echo "类型检查基线存在，当前错误数应 ≤ 基线数（目标：0）"
else
    echo "未找到类型检查基线，将在首次检查后建立"
fi

# 4. 文档同步状态检查
if grep -r "TODO" *.py 2>/dev/null | grep -v "DEV_NOTES.md"; then
    echo "警告: 代码中存在未登记的 TODO，请同步到 DEV_NOTES.md"
fi

echo "=== 检查完成 ==="
```

---

## 交叉引用

- 类型检查详细规范 → 参见 `code-quality.md` 第 3 章
- 版本管理策略 → 参见 `version-control.md` 第 4 章
- 安全红线 → 参见 `security-guardrails.md` 第 9 章
- 健康检查 → 参见 `production-health.md` 第 10 章
- 黄金提示词 → 参见 `golden-prompts.md` 第 7 章
