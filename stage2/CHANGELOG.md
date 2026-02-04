# Changelog

本项目的主要版本变更记录。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

## [Unreleased]

## [0.5.0] - 2026-02-03

### 主要功能
- **实时通知系统** (Phase 3)
  - 新增 `notification_system.py`，支持6种通知渠道：
    - 钉钉机器人 (DingTalk)
    - 企业微信机器人 (WeCom)
    - 邮件通知 (Email)
    - Windows桌面通知 (Desktop)
    - 文件日志 (File)
    - 控制台输出 (Console)
  - 通知规则引擎：按关键字路由到不同渠道
  - 冷却机制：防止重复轰炸
  - 异步发送：不阻塞监控流程
  
- **通知系统集成到监控流程**
  - `monitor_v2.py` 集成通知系统
  - 匹配到关键字后自动触发通知
  - 支持多渠道并发发送
  - 配置驱动，通过 `config.yaml` 配置通知规则

### 技术改进
- **后台截图探索**
  - 新增 `background_capture.py`，尝试 Win32 API PrintWindow
  - 发现微信使用硬件加速，PrintWindow 返回黑屏（已知限制）
  
- **WebSocket 实时推送**
  - 新增 `websocket_manager.py`，支持 WebSocket 实时推送
  - 可用于 Web 界面实时显示新消息

### 配置更新
- `config.yaml` 新增 `notification` 配置块
- 支持按关键字配置不同通知渠道
- 支持配置冷却时间和优先级

### 文档更新
- README.md 添加通知功能说明和配置示例
- 更新 requirements.txt，添加 Phase 3 依赖

## [0.4.1] - 2026-02-03

### 合规优化
- **代码溯源标记**
  - 为 `web_app.py`, `monitor_v2.py`, `sources/wechat_screen.py` 添加 `[AI-GENERATED]` 标记头
  - 标记头包含：日期、任务描述、审查状态、安全检查
- **类型注解完善**
  - 为 `web_app.py` 补充缺失的类型注解（模板过滤器、错误处理器）
- **文档同步**
  - 更新 `DEV_NOTES.md`，记录已知类型警告及处理决策

### 已知问题
- 4个 Pylance 类型警告（运行时不影响）：
  - `sources/wechat_screen.py:112,118` - window_element 可能为 None（运行时已检查）
  - `sources/window_screen.py:46` - class_name_patterns 类型（运行时正常）
  - `monitor.py:1396` - heartbeat 属性（运行时正常）

## [0.4.0] - 2026-02-03

### 主要功能
- **多源监控架构** (monitor_v2.py)
  - 抽象统一 `ChatMessage` 数据结构
  - 抽象消息源接口 (`MessageSource` 协议)
  - 新增 `MultiSourceMonitor`，支持多个消息源并行监控
  - 实现微信桌面屏幕源 (`WeChatScreenSource`)
  - 预留微信客服 API 源 (`WeChatApiSource`)
  - 预留通用窗口源 (`WindowScreenSource`)
- **关键字管理优化**
  - 监控程序优先从数据库 `keywords` 表加载关键字
  - 如果数据库为空，回退到 config.yaml 默认关键字
  - 启动时打印最终用于匹配的关键字列表
- **截图区域计算修复**
  - 修复相对坐标计算错误 (right < left 问题)
  - 增加截图区域安全检查
  - 增加详细日志输出，方便排查坐标问题

### Breaking Changes
- 配置格式变化：`capture_region` 从 `(left, top, right, bottom)` 改为 `(offset_x, offset_y, width, height)`
  - 旧版：相对窗口左上角的绝对坐标
  - 新版：相对窗口左上角的偏移量 + 区域宽高
- 数据库表 `keywords` 成为主要关键字来源，config.yaml 中的 `keywords.list` 作为后备

### Git Tag
```bash
git tag -a v0.4.0 -m "多源监控架构稳定版"
```

## [0.3.0] - 2026-02-02

### 主要功能
- **Web 管理界面** (web_app.py)
  - Dashboard：总消息数、今日消息数、关键字命中统计
  - `/messages`：支持分页和时间/关键字过滤的历史消息列表
  - `/keywords`：关键字管理（新增/删除/启用禁用），存储到数据库
  - `/api/*`：RESTful API 接口
- **数据库扩展**
  - 新增 `keywords` 表：存储关键字列表
  - 新增 `monitor_status` 表：记录监控服务状态
- **Flask 应用结构**
  - 使用 Bootstrap 5 美化界面
  - 响应式布局，支持移动端访问

### Breaking Changes
- 新增依赖：Flask (已在 requirements.txt 中)
- 需要运行 `pip install -r requirements.txt` 安装新依赖

### Git Tag
```bash
git tag -a v0.3.0 -m "Web管理界面稳定版"
```

## [0.2.0] - 2026-02-01

### 主要功能
- **交互式截图区域选择** (`RegionSelector`)
  - 支持鼠标拖拽选择截图区域
  - 支持在配置中保存截图区域 (`capture_region`)
  - 支持相对坐标和绝对坐标两种模式
- **稳定性优化**
  - 为关键方法增加类型注解和断言
  - Pylance 0 报错
  - 截图失败和窗口失效时的异常处理优化
  - 增加截图对比功能，跳过未变化的帧
- **配置增强**
  - 支持 `always_reselect_region` 强制重新选择区域
  - 支持 `force_reselect` 临时强制选择

### Git Tag
```bash
git tag -a v0.2.0 -m "区域选择与稳定性优化版"
```

## [0.1.0] - 2025-01-31

### 主要功能
- **基础监控服务** (monitor.py)
  - 定时截图 + OCR 识别
  - SQLite 数据存储 (`wechat_monitor.db`)
  - 关键字过滤（配置文件固定关键字）
  - 命令行查询工具 (query.py)
  - 数据导出工具 (export.py)
- **配置管理**
  - YAML 配置文件 (`config.yaml`)
  - 支持关键字、监控间隔、OCR 参数等配置

### Git Tag
```bash
git tag -a v0.1.0 -m "初始版本"
```

---

## 版本对应关系

| 版本 | 主要脚本 | 数据库结构 | 配置文件 |
|------|---------|-----------|---------|
| v0.1.0 | monitor.py | messages 表 | 基础配置 |
| v0.2.0 | monitor.py | messages 表 | 增加区域配置 |
| v0.3.0 | monitor.py + web_app.py | 增加 keywords, monitor_status 表 | 不变 |
| v0.4.0 | monitor_v2.py + web_app.py | 不变 | capture_region 格式变化 |

## 兼容性说明

- **v0.1.0 → v0.2.0**：完全兼容，只需更新 config.yaml
- **v0.2.0 → v0.3.0**：数据库自动升级，无需手动操作
- **v0.3.0 → v0.4.0**：
  - 需要重新配置 `capture_region`（格式变化）
  - 建议通过 Web 界面重新添加关键字到数据库
