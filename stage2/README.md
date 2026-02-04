# 微信消息监控服务 - 阶段2：运行指南

## ⚠️ 重要限制

### 窗口可见性要求
**当前版本要求被监控的微信窗口必须保持在前台且完全可见，不能被遮挡或最小化。**

**原因：**
- 当前使用 `PIL.ImageGrab.grab()` 进行屏幕截图，该函数截取的是屏幕像素，而非窗口内容
- 如果窗口被其他窗口遮挡、最小化或移出屏幕，截图将包含错误内容（如遮挡窗口、黑屏或桌面）

**使用建议：**
1. 将微信窗口固定在屏幕的一个角落（如右侧）
2. 调整窗口大小，确保聊天区域完整显示
3. 不要最小化或遮挡微信窗口
4. 避免在监控期间使用全屏应用覆盖微信窗口

### 后台截图支持状态
- **当前版本：不支持后台窗口截图**
- **未来版本：考虑使用 Win32 API PrintWindow 或 DXGI 实现后台截图**

---

## 📋 项目结构

```
wechat-monitor-poc/
├── stage2/
│   ├── config.yaml          # 配置文件
│   ├── monitor.py           # 监控服务主程序
│   ├── database.py          # 数据库模块
│   ├── query.py             # 数据查询工具
│   ├── requirements.txt     # 依赖列表
│   └── README.md            # 本文件
├── wechat_monitor.db        # SQLite数据库（运行后生成）
├── screenshots/             # 截图保存目录（运行后生成）
└── monitor.log              # 日志文件（运行后生成）
```

---

## 🚀 快速开始

### 第一步：安装依赖

打开 PowerShell 或 CMD，执行：

```bash
cd F:\opencode\wechat-monitor-poc\stage2
pip install -r requirements.txt
```

**依赖列表：**
- `uiautomation` - Windows UI 自动化
- `Pillow` - 图像处理
- `pytesseract` - OCR 库
- `PyYAML` - YAML 配置解析
- `schedule` - 定时任务
- `tabulate` - 表格输出（可选，用于查询工具）
- `aiohttp` - 异步 HTTP 客户端（通知功能）
- `aiosmtplib` - 异步 SMTP（邮件通知）
- `flask-socketio` - WebSocket 实时推送（可选）

### 第二步：配置关键字

编辑 `config.yaml` 文件，修改 `keywords.list`：

```yaml
keywords:
  list:
    - "付款"
    - "发货"
    - "投诉"
    - "退款"
    - "订单"
    - "价格"
    # 添加你需要的其他关键字
```

### 第三步：配置目标窗口（可选）

如果你要监控特定的聊天窗口，修改：

```yaml
monitor:
  # 目标窗口标题（部分匹配）
  # 例如："时光2部落" 会匹配 "时光2部落-盛世YY：80270"
  target_window_title: "时光2部落"
```

如果不配置，启动时会列出所有窗口让你选择。

### 第四步：运行监控服务

```bash
python monitor.py
```

**首次运行流程：**
1. 列出所有微信窗口
2. 选择要监控的窗口（如果配置了目标标题会自动匹配）
3. 开始定时监控（默认每5秒扫描一次）
4. 按 `Ctrl+C` 停止服务

---

## 📊 验证步骤

### 验证1：检查服务是否正常运行

观察终端输出，你应该看到：
```
============================================================
微信消息监控服务启动
============================================================
目标窗口: 时光2部落-盛世YY：80270
监控间隔: 5秒
数据库: ./wechat_monitor.db
============================================================
按 Ctrl+C 停止服务
```

### 验证2：测试关键字匹配

1. 在监控的微信窗口中发送一条包含关键字的消息，例如：
   ```
   客户要求退款，请处理一下
   ```

2. 等待5-10秒

3. 观察终端输出，你应该看到：
   ```
   ✓ 匹配到关键字 '退款': 客户要求退款，请处理一下...
     已保存到数据库，ID: 1
   ```

### 验证3：查询数据库

在另一个终端窗口执行：

```bash
cd F:\opencode\wechat-monitor-poc\stage2
python query.py recent 10
```

你应该看到类似输出：
```
+----+--------------+-----------+----------------------+---------------------+
| ID | 窗口         | 关键字    | 消息内容             | 时间                |
+====+==============+===========+======================+=====================+
|  1 | 时光2部落... | 退款      | 客户要求退款，请...  | 2025-02-03 10:30:15 |
+----+--------------+-----------+----------------------+---------------------+
共 1 条消息
```

### 验证4：查看统计信息

```bash
python query.py stats
```

输出示例：
```
============================================================
统计信息
============================================================
总消息数: 5
今日消息: 5

关键字分布:
  退款: 2
  订单: 2
  付款: 1
============================================================
```

### 验证5：直接查看数据库

使用 SQLite 浏览器工具（如 DB Browser for SQLite）打开 `wechat_monitor.db` 文件，查看 `messages` 表。

或使用命令行：
```bash
sqlite3 wechat_monitor.db "SELECT * FROM messages;"
```

---

## ⚙️ 配置说明

### 监控间隔

```yaml
monitor:
  interval: 5  # 每5秒扫描一次
```

建议值：
- 5-10秒：平衡实时性和性能
- 30秒以上：降低系统负载

### 关键字配置

```yaml
keywords:
  list:
    - "付款"
    - "发货"
  match_mode: "contain"  # 包含匹配
  case_sensitive: false  # 不区分大小写
```

匹配模式：
- `contain` - 消息包含关键字即可（推荐）
- `exact` - 消息必须完全等于关键字

### 数据保留

```yaml
database:
  data_retention_days: 30  # 保留30天数据
```

设置为 `0` 表示永久保留。

### 截图配置

```yaml
monitor:
  screenshot:
    save_screenshots: true    # 是否保存截图
    save_directory: "./screenshots"
    retention_days: 7         # 截图保留7天
```

### 通知配置（新功能）

```yaml
notification:
  enabled: true  # 启用通知
  
  # 通知规则
  rules:
    - name: "投诉告警"
      keywords: ["投诉", "举报", "纠纷"]
      channels: ["dingtalk", "email"]
      priority: "CRITICAL"
      cooldown: 300  # 5分钟内不重复通知
      
    - name: "退款提醒"
      keywords: ["退款", "退钱", "退货"]
      channels: ["wecom"]
      priority: "HIGH"
      cooldown: 60
  
  # 通知渠道配置
  channels:
    dingtalk:
      enabled: false
      webhook_url: "https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN"
      
    wecom:
      enabled: false
      webhook_url: "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY"
      
    email:
      enabled: false
      smtp_server: "smtp.qq.com"
      smtp_port: 587
      username: "your_email@qq.com"
      password: "your_auth_code"
      
    desktop:
      enabled: true  # Windows桌面通知
      
    file:
      enabled: true
      path: "./notifications.log"
      
    console:
      enabled: true
```

**配置说明：**
1. 启用通知后，匹配到关键字会自动发送通知
2. 支持多渠道并发（如钉钉+邮件同时发送）
3. 冷却机制防止重复轰炸
4. 需要配置Webhook才能使用钉钉/企业微信通知

---

## 🔧 故障排查

### 问题1：找不到微信窗口

**现象：**
```
未找到任何微信窗口
```

**解决：**
1. 确认微信已启动并登录
2. 确认打开的是 Windows 桌面版微信（不是网页版）
3. 尝试不配置 `target_window_title`，手动选择

### 问题2：OCR 识别失败

**现象：**
```
OCR识别失败: tesseract is not installed or it's not in your PATH
```

**解决：**
1. 下载安装 Tesseract-OCR：https://github.com/UB-Mannheim/tesseract/wiki
2. 安装时勾选中文语言包
3. 将安装路径添加到系统 PATH
4. 或在 `config.yaml` 中指定路径：
   ```yaml
   ocr:
     tesseract_cmd: "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
   ```

### 问题3：没有匹配到关键字

**排查步骤：**
1. 检查截图是否生成（`screenshots/` 目录）
2. 查看截图中的文字是否清晰
3. 手动运行 OCR 测试：
   ```python
   from PIL import Image
   import pytesseract
   
   img = Image.open('screenshots/xxx.png')
   text = pytesseract.image_to_string(img, lang='chi_sim')
   print(text)
   ```
4. 调整 `ocr.chat_area` 裁剪参数

### 问题4：数据库查询不到数据

**排查：**
```bash
# 检查数据库文件是否存在
ls wechat_monitor.db

# 使用 sqlite3 命令行查看
sqlite3 wechat_monitor.db
sqlite> .tables
sqlite> SELECT * FROM messages;
```

---

## 📈 性能优化建议

1. **调整监控间隔**：如果系统负载高，增加到 10-30 秒
2. **关闭截图保存**：如果不需要截图证据，设置 `save_screenshots: false`
3. **定期清理数据**：设置合理的数据保留期限
4. **优化裁剪区域**：根据你的微信窗口布局调整 `chat_area` 参数

---

## 🔒 数据安全提醒

1. **数据库文件**：`wechat_monitor.db` 包含所有监控数据，请妥善保管
2. **截图文件**：定期清理 `screenshots/` 目录，避免占用过多磁盘空间
3. **访问控制**：限制对监控服务器的物理和远程访问
4. **合规使用**：确保符合相关法律法规和公司政策

---

## 📝 后续扩展

阶段3可能的功能：
- Web 管理界面
- 多窗口同时监控
- 实时通知（邮件、钉钉、企业微信）
- 消息导出（Excel、CSV）
- 更智能的消息去重算法

---

**版本：** 阶段2 - 持续监控 + 数据存储  
**更新日期：** 2025年
