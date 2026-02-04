# 项目文档规范化管理与内容对应说明

**分析日期**: 2026-02-03  
**文档总数**: 17 个 Markdown 文件  
**分析范围**: 根目录 + DOCS/ + skills/

---

## 一、文档分类与定位

### 1.1 项目入口文档（根目录）

| 文件名 | 主要用途 | 目标读者 | 更新频率 |
|--------|---------|---------|---------|
| `README.md` | 项目简介、快速开始、故障排查 | 新用户、运维人员 | 低 |
| `CHANGELOG.md` | 版本变更记录、功能迭代历史 | 开发者、用户 | 每次版本发布 |
| `UPGRADE.md` | 版本升级指南、回滚策略 | 运维人员、升级用户 | 每次重大版本 |
| `HEALTH_CHECK.md` | 健康检查机制说明 | 开发者、运维 | 中 |
| `KEYWORDS_TROUBLESHOOTING.md` | 关键字问题排查 | 用户 | 低 |
| `后台截图方案评估.md` | 技术方案评估（历史） | 开发者 | 归档 |
| `生产配置建议.md` | 生产环境建议（历史） | 运维 | 归档 |

### 1.2 开发规范文档（skills/）

| 文件名 | 规范领域 | 加载策略 | 依赖关系 |
|--------|---------|---------|---------|
| `skills/core-rules.md` | 核心基础规范（会话启动、项目结构） | 强制加载 | 无 |
| `skills/code-quality.md` | 代码质量（类型检查、测试） | 开发任务时 | core-rules |
| `skills/version-control.md` | 版本管理（Git、回滚） | 版本任务时 | core-rules |
| `skills/security-guardrails.md` | 安全红线、敏感信息 | 安全任务时 | core-rules |
| `skills/ai-traceability.md` | AI代码溯源、审查 | 审查任务时 | core-rules |
| `skills/checklist-templates.md` | 检查清单、快速参考 | 随时参考 | core-rules |
| `skills/README.md` | Skill系统说明、索引 | 参考 | N/A |

### 1.3 项目管理文档（DOCS/）

| 文件名 | 用途 | 更新时机 |
|--------|------|---------|
| `DOCS/ITERATIVE_BOARD.md` | 迭代看板、需求管理 | 每个迭代 |
| `DOCS/STEP_MANUAL.md` | 步骤交付手册、测试指南 | 每步完成后 |
| `DOCS/DEV_NOTES.md` | 开发笔记、决策记录 | 持续更新 |

---

## 二、内容冲突与重复分析

### 2.1 已识别的重复内容

#### 🔴 重复 1：健康检查说明
- **位置 1**: `HEALTH_CHECK.md` 全文
- **位置 2**: `skills/code-quality.md` 第 3.2 节
- **重复程度**: 高度重复
- **建议**: 保留 `HEALTH_CHECK.md` 作为用户手册，`skills/code-quality.md` 中改为引用链接

#### 🔴 重复 2：版本管理策略
- **位置 1**: `UPGRADE.md` 全文
- **位置 2**: `skills/version-control.md` 全文
- **重复程度**: 中度重复（UPGRADE 更详细）
- **建议**: `UPGRADE.md` 保持详细操作指南，`skills/version-control.md` 保持规范摘要

#### 🟡 重复 3：已知类型警告清单
- **位置 1**: `HEALTH_CHECK.md` 第 62-75 行
- **位置 2**: `DOCS/DEV_NOTES.md` 第 46-55 行
- **重复程度**: 内容一致
- **建议**: 统一维护在 `DOCS/DEV_NOTES.md`，其他文档引用

#### 🟡 重复 4：项目结构说明
- **位置 1**: `README.md` 第 24-38 行
- **位置 2**: `skills/core-rules.md` 第 2.1 节
- **重复程度**: 中度重复
- **建议**: `README.md` 保持简洁，`skills/core-rules.md` 保持详细规范

### 2.2 已识别的冲突内容

#### ⚠️ 冲突 1：启动前阅读文件清单
- **skills/core-rules.md 第 1.1 节**: 要求阅读 6 个文件（含 RULES_FOR_OPENCODE.md）
- **实际项目**: RULES_FOR_OPENCODE.md 不存在，已被拆分为 skills/
- **建议**: 更新为阅读 skills/core-rules.md 和 skills/README.md

#### ⚠️ 冲突 2：文档引用路径
- **多处引用**: `DOCS/ARCHITECTURE.md`, `DOCS/WORKFLOW.md`
- **实际项目**: 这两个文件不存在
- **建议**: 创建占位文件或更新引用

#### ⚠️ 冲突 3：版本日期不一致
- **CHANGELOG.md**: v0.4.0 日期为 2025-02-03（错误年份）
- **实际**: 应该是 2026-02-03
- **建议**: 修正日期

---

## 三、规范化管理建议

### 3.1 文档创建标准

所有新文档必须包含头部元数据：

```markdown
---
title: 文档标题
category: [项目入口|开发规范|项目管理]
version: v1.0.0
date: 2026-02-03
status: [活跃|归档|草稿]
related_files: [相关文件列表]
---
```

### 3.2 文档更新流程

1. **确定变更范围**: 影响哪些文档类别
2. **更新主文档**: 在权威位置更新内容
3. **同步引用文档**: 添加引用或链接，不重复内容
4. **记录变更**: 在 CHANGELOG.md 中记录文档变更

### 3.3 引用规范

避免内容重复，使用引用链接：

```markdown
<!-- 正确：引用而非复制 -->
详见 [健康检查说明](HEALTH_CHECK.md)

<!-- 错误：复制内容 -->
## 健康检查
健康检查包含以下 6 个方面...
（复制全文）
```

---

## 四、文档内容对应列表

### 4.1 按主题索引

#### 主题：项目启动
| 文档 | 章节 | 内容摘要 |
|------|------|---------|
| README.md | 快速开始 | 安装依赖、配置、运行 |
| skills/core-rules.md | 1.1 | 启动前必须阅读的文件 |
| UPGRADE.md | 查看当前版本 | Git 命令 |

#### 主题：代码质量
| 文档 | 章节 | 内容摘要 |
|------|------|---------|
| skills/code-quality.md | 3.1 | 类型检查要求 |
| HEALTH_CHECK.md | 类型检查 | 已知问题清单 |
| DOCS/DEV_NOTES.md | 健康检查状态 | 最新检查结果 |

#### 主题：版本管理
| 文档 | 章节 | 内容摘要 |
|------|------|---------|
| CHANGELOG.md | 全文 | 版本历史 |
| UPGRADE.md | 全文 | 升级步骤 |
| skills/version-control.md | 4.x | 规范要求 |

#### 主题：AI 代码规范
| 文档 | 章节 | 内容摘要 |
|------|------|---------|
| skills/ai-traceability.md | 8.1 | 代码标记规范 |
| DOCS/DEV_NOTES.md | 合规优化 | AI-GENERATED 标记实施 |

#### 主题：安全检查
| 文档 | 章节 | 内容摘要 |
|------|------|---------|
| skills/security-guardrails.md | 9.1 | 安全红线 |
| skills/code-quality.md | 3.2 | 健康检查包含安全 |

### 4.2 按读者角色索引

#### 新用户
推荐阅读顺序：
1. README.md（了解项目）
2. UPGRADE.md（选择版本）
3. HEALTH_CHECK.md（了解检查机制）

#### 开发者
推荐阅读顺序：
1. skills/core-rules.md（基础规范）
2. skills/code-quality.md（代码质量）
3. DOCS/DEV_NOTES.md（当前状态）
4. CHANGELOG.md（版本历史）

#### 运维人员
推荐阅读顺序：
1. UPGRADE.md（升级指南）
2. HEALTH_CHECK.md（健康检查）
3. KEYWORDS_TROUBLESHOOTING.md（问题排查）

---

## 五、待办事项（文档规范化）

### 高优先级
- [ ] 修正 CHANGELOG.md 中的日期错误（2025→2026）
- [ ] 更新 skills/core-rules.md 中的文件引用（RULES_FOR_OPENCODE.md→skills/）
- [ ] 创建缺失的 DOCS/ARCHITECTURE.md 和 DOCS/WORKFLOW.md
- [ ] 统一已知类型警告清单的维护位置

### 中优先级
- [ ] 为所有文档添加标准头部元数据
- [ ] 建立文档间引用链接（避免重复）
- [ ] 归档历史文档（后台截图方案评估.md、生产配置建议.md）

### 低优先级
- [ ] 建立文档更新自动化检查
- [ ] 创建文档模板（template.md）

---

## 六、文档依赖关系图

```
README.md (入口)
    ├── CHANGELOG.md (版本历史)
    ├── UPGRADE.md (升级指南)
    ├── HEALTH_CHECK.md (健康检查)
    └── skills/ (规范体系)
        ├── core-rules.md (基础)
        │   ├── code-quality.md
        │   ├── version-control.md
        │   ├── security-guardrails.md
        │   ├── ai-traceability.md
        │   └── checklist-templates.md
        └── README.md (索引)

DOCS/ (项目管理)
    ├── ITERATIVE_BOARD.md (看板)
    ├── STEP_MANUAL.md (步骤手册)
    ├── DEV_NOTES.md (开发笔记)
    ├── ARCHITECTURE.md (待创建)
    └── WORKFLOW.md (待创建)
```

---

## 七、使用建议

### 日常开发流程
1. 新会话开始：阅读 `skills/core-rules.md`
2. 开发中：参考相关 Skill 文件
3. 开发完成：更新 `DOCS/DEV_NOTES.md` 和 `CHANGELOG.md`
4. 测试：使用 `HEALTH_CHECK.md` 指导

### 版本发布流程
1. 更新 `CHANGELOG.md`
2. 更新 `UPGRADE.md`（如有破坏性变更）
3. 打 Git Tag
4. 更新 `DOCS/DEV_NOTES.md` 状态

### 问题排查流程
1. 查看 `HEALTH_CHECK.md` 运行检查
2. 查看 `KEYWORDS_TROUBLESHOOTING.md`
3. 查看 `DOCS/DEV_NOTES.md` 已知问题
4. 必要时查看 Skill 规范

---

**总结**: 项目文档体系已初步建立，但存在内容重复和引用不一致问题。建议优先修正高优先级待办事项，建立统一的文档维护规范。
