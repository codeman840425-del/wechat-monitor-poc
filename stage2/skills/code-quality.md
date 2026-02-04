---
skill_id: code-quality
trigger_keywords: ["类型检查", "Pylance", "pyright", "类型注解", "测试", "健康检查", "质量"]
dependencies: ["core-rules"]
context_window: 代码质量保证、类型系统、测试验证
---

# Code Quality - 代码质量与类型规范

**版本**: v2.0.0  
**日期**: 2026-02-03  
**状态**: 基础层（开发任务时加载）

---

## 3. 类型检查、自检与测试

### 3.1 类型检查（硬性要求）

以下模块的目标是 **Pylance 0 报错**：

- `monitor.py`  
- `monitor_v2.py`  
- `web_app.py`  
- `core/` 目录下所有文件  
- `sources/` 目录下所有文件  

**规则**：
- 如果临时存在无法马上处理的类型告警：  
  - 必须在 `DOCS/DEV_NOTES.md` 中记录：文件、行号、报错内容、暂缓原因。  
  - 只有在有明确断言或逻辑保证安全的情况下，才使用局部 `# type: ignore`，并在附近注释说明原因。

### 3.2 基础健康检查（Health Check）

提供统一自检入口（`health_check.py` 或 `monitor_v2.py --health-check`），至少执行：

1. **数据库检查**  
   - 能否成功连接 `wechat_monitor.db`；  
   - 是否存在关键表（如消息表、关键字表）以及必要字段。  

2. **Web 路由检查**  
   - 能否初始化 Flask app 并注册关键路由：  
     - `/`  
     - `/messages`  
     - `/keywords`  
     - `/images/...`  
     - Webhook 路由（如 `/api/webhook/wechat/<source_name>`）  

3. **消息源检查**  
   - 当前配置中的各消息源是否可以被初始化（不进入永久循环）；  
   - 对每个消息源执行一次安全的"模拟 poll"：  
     - 不做真实截图/写库（可用 dry-run 或 mock）；  
     - 确认不会抛异常（初始化逻辑健壮）。

**执行后报告**：
- 推荐运行的自检命令（例如 `python health_check.py`）；  
- 正常情况下的预期结果（例如："所有检查通过，无错误；2 个消息源可用"）。

### 3.3 测试用例（最小手动测试）

每个重要功能或阶段性迭代，必须在 `DOCS/WORKFLOW.md` 中附上一套最小手动测试步骤，包括但不限于：

- 启动监控脚本的命令  
- 在微信/其它聊天应用中发送的测试消息内容（包括命中关键字和不命中的例子）  
- 如何通过：  
  - 命令行（如 `python query.py recent 20`）  
  - Web 界面（如 `/messages` / `/keywords`）  

验证行为是否符合预期（命中关键字、截图正确、Web 展示正常等）。

---

## 2.2 代码风格与最佳实践（补充）

### 类型注解详细规范

**必须提供类型注解的场景**：
- 所有公开函数（非私有方法）
- 类属性（特别是配置类、数据类）
- 返回类型可能为 `None` 的函数

**类型注解示例**：

```python
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass

@dataclass
class ChatMessage:
    id: str
    platform: str
    content: str
    timestamp: datetime
    sender: Optional[str] = None  # 可能为 None
    metadata: Dict[str, any] = field(default_factory=dict)

def process_message(
    message: ChatMessage,
    keywords: List[str],
    case_sensitive: bool = False
) -> Optional[str]:
    """
    处理消息，返回匹配到的关键字或 None
    """
    if not message.content:
        return None
    
    # 处理逻辑...
    return matched_keyword
```

**禁止的类型使用**：
- 避免使用裸 `Any`，除非确实无法确定类型
- 避免使用 `*args, **kwargs` 而不提供类型重载
- 避免循环导入导致的类型问题（使用 `TYPE_CHECKING` 或字符串前向引用）

### 异常处理规范

**必须捕获的异常**：
- 数据库操作：`sqlite3.Error`
- 文件操作：`IOError`, `FileNotFoundError`
- 网络操作：`requests.RequestException`
- OCR 操作：`pytesseract.TesseractError`

**异常处理模板**：

```python
def safe_operation() -> Optional[Result]:
    try:
        # 业务逻辑
        return result
    except SpecificException as e:
        logger.error(f"操作失败: {e}")
        # 记录到错误日志
        ErrorTracker.record(e, context={"operation": "safe_operation"})
        return None
    except Exception as e:
        # 未预期的异常，记录并上报
        logger.exception(f"未预期的错误: {e}")
        raise  # 或者返回安全的默认值
```

---

## 交叉引用

- 项目结构 → 参见 `core-rules.md` 第 2 章
- 版本管理 → 参见 `version-control.md` 第 4 章
- AI 代码标记 → 参见 `ai-traceability.md` 第 8 章
- 安全扫描 → 参见 `security-guardrails.md` 第 9 章
- 生产级健康检查 → 参见 `production-health.md` 第 10 章
