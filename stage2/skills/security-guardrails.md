---
skill_id: security-guardrails
trigger_keywords: ["安全", "密码", "密钥", "token", "硬编码", "SQL注入", "XSS", "敏感信息", "扫描", "审查"]
dependencies: ["core-rules"]
context_window: 安全审查、敏感信息防护、代码安全扫描
---

# Security Guardrails - 安全红线与敏感信息防护

**版本**: v2.0.0  
**日期**: 2026-02-03  
**状态**: 安全与合规层（安全相关任务时加载）

---

## 9. 安全与敏感信息防护

### 9.1 安全红线（硬性禁止）

以下行为在任何情况下都禁止出现在代码或提示词中：

1. **禁止硬编码**：
   - 微信 API 密钥、Token、数据库连接字符串
   - 绝对路径（如 `C:\Users\RealName\` 或 `/home/username/`）
   - 测试用的真实手机号、微信号、个人身份信息

2. **禁止生产数据入 AI 上下文**：
   - 不得将真实用户聊天截图、生产数据库导出内容发送给 AI 进行"调试分析"
   - 调试必须使用脱敏数据（使用 `tests/fixtures/sanitized_*.png` 和 `tests/fixtures/mock_db.sql`）

3. **禁止危险操作**：
   - AI 生成的代码不得包含 `os.system()`, `subprocess.call()`, `eval()`, `exec()` 除非经过安全审查并在注释中标记 `[SECURITY_REVIEWED]`
   - 不得关闭 SSL 证书验证（`verify=False`）

### 9.2 自动化安全扫描

在 `health_check.py` 中增加 `SecurityCheck` 类：

```python
class SecurityCheck:
    def check_hardcoded_secrets(self) -> List[Violation]:
        """扫描代码中疑似硬编码的密钥"""
        patterns = [r'api[_-]?key\s*=\s*["\'][a-zA-Z0-9]{32,}["\']']
        pass
    
    def check_sql_injection_risk(self) -> List[Violation]:
        """检查字符串拼接 SQL（应使用参数化查询）"""
        pass
    
    def check_path_traversal(self) -> List[Violation]:
        """检查文件操作是否验证路径在允许目录内"""
        pass
```

**执行频率**：
- 每次提交前本地运行：`python health_check.py --security`
- CI 流程中阻断：发现 `CRITICAL` 或 `HIGH` 级别安全问题立即阻断合并

### 9.3 截图隐私处理

OCR 截图片段在入库前必须处理：
- 自动检测并模糊身份证号（正则 `\d{17}[\dXx]`）、手机号（正则 `1[3-9]\d{9}`）等敏感模式
- 在 `config.yaml` 中增加 `privacy.mask_patterns` 配置，允许用户自定义正则
- Web 界面展示截图时，叠加水印（当前操作用户 + 时间戳），防止截图泄露后无法溯源

---

## 安全审查清单

### 代码提交前检查

- [ ] 无硬编码的 API 密钥、Token、密码
- [ ] 无绝对路径（使用相对路径或配置）
- [ ] 无真实用户数据（使用脱敏测试数据）
- [ ] 无 `eval()`, `exec()`, `os.system()` 等危险函数
- [ ] 数据库查询使用参数化（防止 SQL 注入）
- [ ] 文件路径经过验证（防止路径遍历）
- [ ] 用户输入经过验证和转义（防止 XSS）

### 高风险场景审查

| 风险等级 | 场景 | 审查要点 |
|---------|------|---------|
| **CRITICAL** | 数据库 Schema 变更（新增表、修改字段类型） | 数据迁移脚本、向后兼容、回滚方案 |
| **HIGH** | 消息源解析逻辑（微信 API/OCR 结果解析） | 异常消息处理、XSS 防护、编码问题 |
| **HIGH** | 文件系统操作（截图保存、日志写入） | 路径验证、权限检查、磁盘满处理 |
| **MEDIUM** | Flask 路由新增/修改 | 输入验证、CSRF 防护、响应格式一致性 |

---

## 敏感信息处理规范

### 配置文件中的敏感信息

**正确做法**：
```yaml
# config.yaml
api:
  app_id: ""  # 从环境变量读取: ${WECHAT_APP_ID}
  app_secret: ""  # 从环境变量读取: ${WECHAT_APP_SECRET}
  token: ""  # 从环境变量读取: ${WECHAT_TOKEN}
```

**错误做法**：
```yaml
# config.yaml - 禁止！
api:
  app_id: "wx1234567890abcdef"
  app_secret: "a1b2c3d4e5f6..."
  token: "my_secret_token_123"
```

### 环境变量使用

```python
import os

# 正确做法
app_id = os.environ.get('WECHAT_APP_ID')
if not app_id:
    raise ValueError("WECHAT_APP_ID 环境变量未设置")

# 错误做法 - 禁止！
app_id = "wx1234567890abcdef"  # 硬编码
```

---

## 安全扫描命令

```bash
# 运行安全扫描
python health_check.py --security

# 手动检查硬编码密钥
grep -r "api_key\|app_secret\|token" --include="*.py" . | grep -v "^#" | grep -v "os.environ"

# 检查危险函数
grep -r "eval\|exec\|os.system\|subprocess.call" --include="*.py" .
```

---

## 交叉引用

- 核心规则 → 参见 `core-rules.md`
- 代码质量 → 参见 `code-quality.md`
- AI 代码溯源 → 参见 `ai-traceability.md`
- 健康检查 → 参见 `production-health.md`
- 检查清单 → 参见 `checklist-templates.md`
