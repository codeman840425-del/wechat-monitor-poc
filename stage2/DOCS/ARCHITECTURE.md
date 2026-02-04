---
title: 项目架构文档
category: 项目管理
version: v1.0.0
date: 2026-02-03
status: 活跃
related_files: [monitor_v2.py, web_app.py, core/, sources/]
---

# 项目架构文档

**项目**: wechat-monitor-poc  
**版本**: v0.4.0  
**最后更新**: 2026-02-03

---

## 1. 系统概述

微信消息监控服务是一个基于 Python 的桌面应用监控系统，通过截图+OCR技术捕获聊天软件消息，进行关键字匹配和存储，提供Web管理界面。

### 1.1 核心功能

- **多源消息监控**: 支持微信桌面、QQ、飞书等多个消息源
- **关键字匹配**: 实时匹配预设关键字，标记重要消息
- **数据存储**: SQLite 数据库存储消息记录
- **Web 管理**: Flask 提供 Dashboard、消息查询、关键字管理

### 1.2 技术栈

- **后端**: Python 3.9+, Flask
- **数据库**: SQLite3
- **OCR**: Tesseract-OCR + pytesseract
- **截图**: PIL/Pillow + Win32 API
- **前端**: Bootstrap 5 + Jinja2 模板

---

## 2. 系统架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        用户层                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ 微信桌面     │  │ QQ/飞书      │  │ Web 管理界面 │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
└─────────┼─────────────────┼─────────────────┼──────────────┘
          │                 │                 │
          ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────┐
│                      消息源层 (sources/)                     │
│  ┌────────────────┐  ┌────────────────┐                     │
│  │ WeChatScreen   │  │ WindowScreen   │                     │
│  │ Source         │  │ Source         │                     │
│  └───────┬────────┘  └───────┬────────┘                     │
│          │                   │                              │
│          └─────────┬─────────┘                              │
│                    ▼                                        │
│           ┌────────────────┐                                │
│           │ MessageSource  │                                │
│           │ (Base Class)   │                                │
│           └───────┬────────┘                                │
└───────────────────┼─────────────────────────────────────────┘
                    │
                    ▼ poll()
┌─────────────────────────────────────────────────────────────┐
│                      核心层 (core/)                          │
│           ┌────────────────┐                                │
│           │ ChatMessage    │                                │
│           │ (统一消息格式)  │                                │
│           └───────┬────────┘                                │
└───────────────────┼─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│                     处理层 (monitor_v2.py)                   │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐ │
│  │ KeywordFilter  │  │ MultiSource    │  │ Database       │ │
│  │ (关键字匹配)   │  │ Monitor        │  │ Manager        │ │
│  └───────┬────────┘  └───────┬────────┘  └───────┬────────┘ │
│          │                   │                   │          │
│          └───────────────────┼───────────────────┘          │
│                              ▼                              │
│                    ┌────────────────┐                       │
│                    │ SQLite DB      │                       │
│                    └────────────────┘                       │
└─────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│                     展示层 (web_app.py)                      │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐ │
│  │ Dashboard      │  │ Messages       │  │ Keywords       │ │
│  │ (统计面板)     │  │ (消息列表)     │  │ (关键字管理)   │ │
│  └────────────────┘  └────────────────┘  └────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 数据流

```
微信窗口 → 截图 → OCR识别 → 文本提取 → 关键字匹配 → 数据库存储 → Web展示
```

详细流程：
1. **截图**: `WeChatScreenSource._capture_screenshot()` 使用 PIL 截取窗口
2. **OCR**: `WeChatScreenSource._recognize_text()` 使用 Tesseract 识别文字
3. **解析**: 将 OCR 结果解析为 `ChatMessage` 对象
4. **匹配**: `KeywordFilter.check()` 进行关键字匹配
5. **存储**: `DatabaseManager.insert_message()` 存入 SQLite
6. **展示**: `web_app.py` 提供 Web 界面查询

---

## 3. 模块详解

### 3.1 消息源模块 (sources/)

#### 3.1.1 BaseMessageSource (sources/base.py)

**职责**: 消息源抽象基类，定义统一接口

**核心方法**:
- `poll() -> List[ChatMessage]`: 拉取新消息
- `is_available() -> bool`: 检查消息源可用性
- `get_status() -> SourceStatus`: 获取状态信息

#### 3.1.2 WeChatScreenSource (sources/wechat_screen.py)

**职责**: 微信桌面版 OCR 消息源

**核心流程**:
1. `_find_window()`: 查找微信窗口
2. `_capture_screenshot()`: 截图（支持相对/绝对区域）
3. `_recognize_text()`: OCR 识别
4. `_parse_messages()`: 解析为 ChatMessage

**配置项**:
- `window_title_pattern`: 窗口标题匹配模式
- `capture_region`: 截图区域 `(offset_x, offset_y, width, height)`
- `ocr_lang`: OCR 语言（默认 `chi_sim+eng`）

#### 3.1.3 WindowScreenSource (sources/window_screen.py)

**职责**: 通用窗口截图源，支持 QQ、飞书等

**特点**:
- 通过 `app_type` 识别不同应用
- 支持类名模式匹配
- 复用 WeChatScreenSource 的截图逻辑

### 3.2 核心数据模块 (core/)

#### 3.2.1 ChatMessage (core/message.py)

**职责**: 统一的消息数据结构

**字段**:
```python
@dataclass
class ChatMessage:
    id: str              # 消息唯一标识
    platform: str        # 平台类型（wechat_win、qq_win等）
    channel: str         # 会话/频道标识
    sender: str          # 发送者
    content: str         # 消息内容
    timestamp: datetime  # 时间戳
    matched_keywords: List[str]  # 匹配到的关键字
```

### 3.3 监控引擎 (monitor_v2.py)

#### 3.3.1 MultiSourceMonitor

**职责**: 多消息源统一监控管理

**核心功能**:
- 管理多个消息源（`sources: List[BaseMessageSource]`）
- 轮询调度（根据 `poll_interval`）
- 统一消息处理（去重、匹配、存储）
- 心跳机制（数据库状态更新）

**配置加载**:
1. 优先从数据库 `keywords` 表加载关键字
2. 数据库为空时回退到 `config.yaml`

#### 3.3.2 KeywordFilter

**职责**: 关键字匹配过滤器

**匹配模式**:
- `contain`: 包含匹配（默认）
- `exact`: 精确匹配
- `fuzzy`: 模糊匹配（使用 difflib）

### 3.4 Web 管理界面 (web_app.py)

#### 3.4.1 路由结构

```
/                    -> Dashboard（统计面板）
/messages            -> 消息列表（支持筛选、分页）
/messages/<id>       -> 消息详情
/keywords            -> 关键字管理（CRUD）
/api/stats           -> 统计数据 API
/api/status          -> 监控状态 API
/api/webhook/wechat  -> 微信 Webhook 接收
```

#### 3.4.2 数据库模型

**messages 表**:
```sql
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    window_title TEXT,        -- 窗口标题
    message_text TEXT,        -- 消息内容
    matched_keyword TEXT,     -- 匹配到的关键字
    screenshot_path TEXT,     -- 截图路径
    created_at TIMESTAMP      -- 创建时间
);
```

**keywords 表**:
```sql
CREATE TABLE keywords (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word TEXT UNIQUE,         -- 关键字
    enabled BOOLEAN,          -- 是否启用
    created_at TIMESTAMP      -- 创建时间
);
```

---

## 4. 配置体系

### 4.1 配置文件 (config.yaml)

```yaml
# 数据库配置
database:
  db_path: "./wechat_monitor.db"

# 监控配置
monitor:
  interval: 5                    # 轮询间隔（秒）
  target_window_title: ""        # 目标窗口标题
  capture_region: []             # 截图区域 [offset_x, offset_y, width, height]
  
# OCR配置
ocr:
  lang: "chi_sim+eng"           # OCR语言
  tesseract_cmd: null           # Tesseract路径（null表示使用系统PATH）
  
# 关键字配置
keywords:
  list: ["退款", "订单", "投诉"]  # 默认关键字列表
  match_mode: "contain"         # 匹配模式
  case_sensitive: false         # 是否区分大小写
```

### 4.2 配置优先级

1. **数据库配置**（运行时动态修改）> 最高优先级
2. **config.yaml**（文件配置）> 中等优先级
3. **代码默认值** > 最低优先级

---

## 5. 扩展点

### 5.1 新增消息源

1. 继承 `BaseMessageSource`
2. 实现 `poll()` 方法
3. 返回 `List[ChatMessage]`
4. 在 `monitor_v2.py` 中添加实例

示例：
```python
class DingTalkSource(BaseMessageSource):
    def poll(self) -> List[ChatMessage]:
        # 实现钉钉消息获取逻辑
        pass
```

### 5.2 新增 Web 路由

1. 在 `web_app.py` 中添加路由函数
2. 使用 `@app.route()` 装饰器
3. 返回 `render_template()` 或 `jsonify()`

### 5.3 新增关键字匹配模式

1. 在 `KeywordFilter` 中添加模式处理逻辑
2. 在 `config.yaml` 中支持新模式

---

## 6. 部署架构

### 6.1 单机部署

```
┌─────────────────────────────────────┐
│           单台服务器                 │
│  ┌─────────┐  ┌─────────┐          │
│  │ monitor │  │ web_app │          │
│  │ _v2.py  │  │ .py     │          │
│  │ (后台)  │  │ (前台)  │          │
│  └────┬────┘  └────┬────┘          │
│       └─────────────┘               │
│              │                      │
│       ┌──────┴──────┐               │
│       │ SQLite DB   │               │
│       └─────────────┘               │
└─────────────────────────────────────┘
```

### 6.2 目录结构

```
wechat-monitor-poc/
├── monitor_v2.py          # 监控主程序
├── web_app.py             # Web管理界面
├── health_check.py        # 健康检查
├── config.yaml            # 配置文件
├── wechat_monitor.db      # SQLite数据库
├── core/                  # 核心模块
│   ├── __init__.py
│   └── message.py         # ChatMessage定义
├── sources/               # 消息源模块
│   ├── __init__.py
│   ├── base.py            # BaseMessageSource
│   ├── wechat_screen.py   # 微信桌面源
│   ├── wechat_api.py      # 微信API源
│   └── window_screen.py   # 通用窗口源
├── templates/             # HTML模板
│   ├── base.html
│   ├── dashboard.html
│   ├── messages.html
│   └── keywords.html
└── DOCS/                  # 文档
    ├── ARCHITECTURE.md    # 本文档
    ├── DEV_NOTES.md       # 开发笔记
    └── ...
```

---

## 7. 性能考虑

### 7.1 截图优化

- **区域裁剪**: 只截取聊天区域，减少 OCR 处理时间
- **变化检测**: 对比截图哈希，跳过未变化的帧
- **预处理**: 缩放图像提升 OCR 准确率

### 7.2 数据库优化

- **索引**: `created_at`, `matched_keyword` 字段已索引
- **分页**: Web 界面使用分页，避免大数据量查询
- **清理**: 支持按时间自动清理旧数据

### 7.3 轮询优化

- **多源并发**: 各消息源独立轮询，互不阻塞
- **间隔可调**: 根据系统负载调整 `poll_interval`

---

## 8. 安全考虑

### 8.1 数据安全

- **数据库**: 本地 SQLite，无网络暴露风险
- **截图**: 本地存储，定期清理
- **敏感信息**: OCR 结果中可能包含敏感信息，需妥善保管

### 8.2 代码安全

- **SQL注入**: 使用参数化查询，无字符串拼接
- **路径遍历**: 文件操作前验证路径在允许目录内
- **XSS防护**: Web 界面使用模板转义

---

## 9. 相关文档

- [DEV_NOTES.md](DEV_NOTES.md) - 开发笔记、决策记录
- [WORKFLOW.md](WORKFLOW.md) - 开发流程、测试用例
- [UPGRADE.md](../UPGRADE.md) - 版本升级指南
- [CHANGELOG.md](../CHANGELOG.md) - 版本变更记录
- [skills/README.md](../skills/README.md) - 开发规范体系

---

**维护者**: AI Assistant  
**最后更新**: 2026-02-03
