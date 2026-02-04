# OpenCode Skills 目录

本项目将开发规范按功能域拆分为多个独立的 Skill 文件，支持根据任务类型选择性加载。

## Skill 文件列表

### 基础层（必加载）

| Skill ID | 文件名 | 用途 | 触发关键词 |
|---------|--------|------|-----------|
| `core-rules` | `core-rules.md` | 核心基础规范 | 启动、会话、项目结构、代码规范 |
| `code-quality` | `code-quality.md` | 代码质量与类型规范 | 类型检查、Pylance、测试、质量 |
| `version-control` | `version-control.md` | 版本管理与回滚策略 | 版本、Git、tag、回滚、升级 |

### 安全与合规层（安全任务时加载）

| Skill ID | 文件名 | 用途 | 触发关键词 |
|---------|--------|------|-----------|
| `security-guardrails` | `security-guardrails.md` | 安全红线与敏感信息防护 | 安全、密码、密钥、token、硬编码、SQL注入 |
| `ai-traceability` | `ai-traceability.md` | AI 代码溯源与审查 | AI生成、代码标记、审查、溯源 |

### 工具层（随时参考）

| Skill ID | 文件名 | 用途 | 触发关键词 |
|---------|--------|------|-----------|
| `checklist-templates` | `checklist-templates.md` | 检查清单与快速参考 | 检查清单、checklist、快速参考、命令 |

## 使用方式

### 自动加载（推荐）

OpenCode 可根据任务描述自动匹配并加载相应的 Skill 文件。

**触发关键词匹配示例**：
- 用户说"检查类型错误" → 自动加载 `code-quality.md`
- 用户说"如何回滚版本" → 自动加载 `version-control.md`
- 用户说"检查安全漏洞" → 自动加载 `security-guardrails.md`

### 手动加载

在会话开始时明确指定需要加载的 Skill：

```text
请加载以下 Skill 文件：
1. skills/core-rules.md
2. skills/code-quality.md
3. skills/security-guardrails.md

然后帮我审查这段代码的安全性...
```

### 完整加载

如需加载所有 Skill（全面审查时）：

```text
请按顺序加载 skills/ 目录下的所有 Skill 文件，然后...
```

## 依赖关系

```
core-rules (基础，无依赖)
    ├── code-quality (依赖 core-rules)
    ├── version-control (依赖 core-rules)
    ├── security-guardrails (依赖 core-rules)
    ├── ai-traceability (依赖 core-rules)
    └── checklist-templates (依赖 core-rules)
```

## 与主文档的关系

- **原 `RULES_FOR_OPENCODE.md`**：完整的规范文档（约 5000 字）
- **Skill 文件**：按功能域拆分后的模块化规范

**建议**：
- 日常开发：使用 Skill 文件（按需加载，避免上下文过载）
- 全面审查：参考完整的 `RULES_FOR_OPENCODE.md`
- 新成员入职：先阅读 `core-rules.md`，再按需深入其他 Skill

## 更新维护

当需要更新规范时：

1. 确定变更涉及的功能域
2. 更新对应的 Skill 文件
3. 同步更新完整的 `RULES_FOR_OPENCODE.md`
4. 在 `CHANGELOG.md` 中记录规范变更

## 扩展新的 Skill

如需添加新的 Skill：

1. 创建新的 `.md` 文件
2. 在文件头部添加元数据：
   ```yaml
   ---
   skill_id: your-skill-id
   trigger_keywords: ["关键词1", "关键词2"]
   dependencies: ["core-rules"]
   context_window: 描述适用场景
   ---
   ```
3. 在本 README 中添加条目
4. 更新依赖关系图

---

**版本**: v2.0.0  
**最后更新**: 2026-02-03
