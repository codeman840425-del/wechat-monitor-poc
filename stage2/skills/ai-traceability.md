---
skill_id: ai-traceability
trigger_keywords: ["AI生成", "代码标记", "审查", "溯源", "贡献记录", "AI代码"]
dependencies: ["core-rules"]
context_window: AI 代码标记、人工审查、贡献追踪
---

# AI Traceability - AI 代码溯源与审查

**版本**: v2.0.0  
**日期**: 2026-02-03  
**状态**: 安全与合规层（代码审查时加载）

---

## 8. AI 代码溯源与审查

### 8.1 代码标记规范

所有 AI 生成的非 trivial 代码（超过 10 行或涉及核心业务逻辑）必须包含结构化注释头：

```python
# [AI-GENERATED] Date: 2026-02-03 | PromptHash: a1b2c3d
# [CONTEXT] Task: 实现多窗口截图轮询器 | Issue: #42
# [REVIEWED] By: username | Date: 2026-02-03 | Status: VERIFIED
# [DEPENDENCIES] Requires: monitor_v2.py#L45-L67, config.yaml::screenshot_interval
# [SAFETY] Checked: 无 SQL 注入风险, 无路径遍历风险, 已处理异常
```

**字段说明**：
- `PromptHash`: 提示词的哈希前 8 位，用于追溯生成上下文
- `REVIEWED`: 人工审查标记，必须包含审查者身份和日期
- `SAFETY`: 针对本项目常见风险（路径遍历、正则回溯、敏感信息泄露）的自检确认

### 8.2 高风险代码人工审查清单

以下场景强制要求人工审查并签名（通过代码审查工具或注释确认）：

| 风险等级 | 场景 | 审查要点 |
|---------|------|---------|
| **CRITICAL** | 数据库 Schema 变更（新增表、修改字段类型） | 数据迁移脚本、向后兼容、回滚方案 |
| **HIGH** | 消息源解析逻辑（微信 API/OCR 结果解析） | 异常消息处理、XSS 防护、编码问题 |
| **HIGH** | 文件系统操作（截图保存、日志写入） | 路径验证、权限检查、磁盘满处理 |
| **MEDIUM** | Flask 路由新增/修改 | 输入验证、CSRF 防护、响应格式一致性 |

### 8.3 AI 贡献追踪

在 `CHANGELOG.md` 中增加 `### AI Contributions` 子章节，记录：
- AI 生成的主要功能模块（如："v0.4.0 的消息源抽象基类由 AI 辅助生成"）
- 已知限制（如："AI 生成的 OCR 预处理逻辑在低分辨率下需人工调优"）

---

## AI 代码标记模板

### 简单函数（10-30 行）

```python
# [AI-GENERATED] Date: 2026-02-03 | Task: 关键字匹配优化
def optimized_keyword_match(text: str, keywords: List[str]) -> Optional[str]:
    """优化的关键字匹配函数"""
    # 实现代码...
    pass
```

### 复杂模块（30+ 行或核心逻辑）

```python
# [AI-GENERATED] Date: 2026-02-03 | PromptHash: a1b2c3d
# [CONTEXT] Task: 实现多窗口截图轮询器 | Issue: #42
# [REVIEWED] By: admin | Date: 2026-02-03 | Status: VERIFIED
# [DEPENDENCIES] Requires: monitor_v2.py#L45-L67
# [SAFETY] Checked: 无 SQL 注入风险, 无路径遍历风险, 已处理异常

class MultiWindowPoller:
    """
    多窗口截图轮询器
    
    功能：同时监控多个微信窗口，支持动态添加/移除窗口
    """
    
    def __init__(self, config: Dict[str, Any]):
        # 实现代码...
        pass
```

### 需要安全审查的代码

```python
# [AI-GENERATED] Date: 2026-02-03 | Task: 文件上传处理
# [SECURITY_REVIEWED] By: security-team | Date: 2026-02-03
# [SAFETY] Checked: 
#   - 路径遍历防护: 使用 os.path.abspath 验证
#   - 文件类型检查: 只允许 .png, .jpg
#   - 大小限制: 最大 10MB
#   - 病毒扫描: 集成 ClamAV

def handle_file_upload(file_data: bytes, filename: str) -> str:
    """安全地处理文件上传"""
    # 实现代码...
    pass
```

---

## 审查流程

### 自动标记（AI 生成时）

1. AI 生成代码时自动添加 `[AI-GENERATED]` 标记
2. 记录生成日期和任务描述
3. 生成 PromptHash（提示词哈希）

### 人工审查（开发者）

1. 审查代码逻辑正确性
2. 检查安全风险（参见安全审查清单）
3. 添加 `[REVIEWED]` 标记
4. 确认 `[SAFETY]` 检查项

### 合并前检查

- [ ] 所有 AI 代码都有 `[AI-GENERATED]` 标记
- [ ] 高风险代码有 `[REVIEWED]` 标记
- [ ] 安全相关代码有 `[SECURITY_REVIEWED]` 标记
- [ ] 依赖关系明确（`[DEPENDENCIES]`）

---

## AI 贡献记录

在 `CHANGELOG.md` 中记录：

```markdown
## [0.4.0] - 2026-02-03

### 主要功能
- 多源监控架构 (monitor_v2.py)
- ...

### AI Contributions
- **消息源抽象基类** (`sources/base.py`): 由 AI 辅助生成，经人工审查验证
- **OCR 预处理优化** (`core/image_processor.py`): AI 生成，在低分辨率场景需人工调参
- **Webhook 路由处理** (`web_app.py`): AI 生成，已进行安全审查

### 已知限制
- AI 生成的 OCR 预处理逻辑在 720p 以下分辨率识别率下降 15%，建议人工调优
```

---

## 交叉引用

- 核心规则 → 参见 `core-rules.md`
- 代码质量 → 参见 `code-quality.md`
- 安全规范 → 参见 `security-guardrails.md`
- 检查清单 → 参见 `checklist-templates.md`
