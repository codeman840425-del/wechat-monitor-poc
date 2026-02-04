# Phase 3 实时通知系统设计文档

**版本**: v0.5.0  
**日期**: 2026-02-03  
**状态**: 设计阶段

---

## 1. 需求分析

### 1.1 当前痛点

1. **被动监控**: 必须主动查询数据库或Web界面才能看到匹配的消息
2. **延迟感知**: 无法实时知道重要消息（如"投诉"、"退款"）的出现
3. **后台限制**: 微信窗口必须保持可见，不能最小化
4. **单一渠道**: 只能通过日志文件查看，缺乏多渠道通知

### 1.2 业务需求

| 优先级 | 需求 | 说明 |
|--------|------|------|
| P0 | 实时通知 | 匹配到关键字后立即推送通知 |
| P0 | 后台截图 | 微信窗口最小化也能监控 |
| P1 | 多渠道通知 | 支持钉钉、企业微信、邮件等 |
| P1 | 通知分级 | 不同关键字不同通知方式 |
| P2 | Web实时推送 | Web界面实时显示新消息 |
| P2 | 智能分类 | 自动分类消息优先级 |

---

## 2. 系统架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    微信消息监控服务 v0.5.0                    │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   后台截图    │  │   OCR识别    │  │   消息处理    │      │
│  │  (PrintWindow)│  │  (Tesseract) │  │ (关键词匹配)  │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │              │
│         └──────────────────┴──────────────────┘              │
│                            │                                 │
│                            ▼                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              消息队列 (Queue)                        │   │
│  │         - 异步处理，解耦生产者和消费者               │   │
│  └─────────────────────────────────────────────────────┘   │
│                            │                                 │
│         ┌──────────────────┼──────────────────┐              │
│         ▼                  ▼                  ▼              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  钉钉通知    │  │ 企业微信通知 │  │   邮件通知   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              WebSocket 实时推送                      │   │
│  │         - Flask-SocketIO 实现                       │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 核心模块设计

#### 2.2.1 后台截图模块 (BackgroundCapture)

```python
class BackgroundCapture:
    """后台窗口截图实现"""
    
    def __init__(self, window_handle: int):
        self.hwnd = window_handle
        
    def capture(self) -> Optional[Image.Image]:
        """使用PrintWindow截取后台窗口"""
        # 1. 获取窗口DC
        # 2. 创建兼容DC和位图
        # 3. 调用PrintWindow
        # 4. 转换为PIL Image
        pass
        
    def is_window_minimized(self) -> bool:
        """检查窗口是否最小化"""
        pass
        
    def restore_window(self) -> bool:
        """恢复最小化窗口"""
        pass
```

**技术选型**:
- **首选**: Win32 API PrintWindow (简单，兼容性好)
- **备选**: Windows Graphics Capture API (Win10 1903+, 功能更强)

#### 2.2.2 通知系统 (NotificationSystem)

```python
class NotificationSystem:
    """统一通知管理"""
    
    def __init__(self):
        self.channels: Dict[str, NotificationChannel] = {}
        self.rules: List[NotificationRule] = []
        
    def register_channel(self, name: str, channel: NotificationChannel):
        """注册通知渠道"""
        pass
        
    def add_rule(self, rule: NotificationRule):
        """添加通知规则"""
        pass
        
    async def notify(self, message: MessageRecord):
        """根据规则发送通知"""
        # 1. 匹配规则
        # 2. 选择渠道
        # 3. 异步发送
        pass

class NotificationRule:
    """通知规则"""
    keyword: str           # 匹配的关键字
    channels: List[str]    # 通知渠道列表
    priority: int          # 优先级 (1-5)
    cooldown: int          # 冷却时间（秒）
    
class NotificationChannel(ABC):
    """通知渠道抽象基类"""
    
    @abstractmethod
    async def send(self, title: str, content: str, **kwargs) -> bool:
        pass
```

**支持渠道**:
1. **钉钉群机器人** (Webhook)
2. **企业微信机器人** (Webhook)
3. **邮件通知** (SMTP)
4. **桌面通知** (Windows Toast)
5. **WebSocket推送** (实时到Web界面)

#### 2.2.3 消息队列 (MessageQueue)

```python
import asyncio
from asyncio import Queue

class AsyncMessageQueue:
    """异步消息队列"""
    
    def __init__(self, maxsize: int = 1000):
        self.queue: Queue[MessageRecord] = Queue(maxsize=maxsize)
        self.consumers: List[Callable] = []
        
    async def put(self, message: MessageRecord):
        """放入消息"""
        await self.queue.put(message)
        
    async def consume(self):
        """消费消息"""
        while True:
            message = await self.queue.get()
            for consumer in self.consumers:
                try:
                    await consumer(message)
                except Exception as e:
                    logger.error(f"Consumer error: {e}")
            self.queue.task_done()
            
    def add_consumer(self, consumer: Callable):
        """添加消费者"""
        self.consumers.append(consumer)
```

---

## 3. 配置设计

### 3.1 通知配置 (config.yaml)

```yaml
# ==================== 通知配置 ====================
notification:
  enabled: true
  
  # 默认通知渠道（当没有匹配规则时使用）
  default_channels:
    - console
    - file
  
  # 通知规则
  rules:
    # 规则1: 投诉类消息 -> 钉钉+邮件
    - name: "投诉告警"
      keywords: ["投诉", "举报", "纠纷"]
      channels: ["dingtalk", "email"]
      priority: 5
      cooldown: 300  # 5分钟内不重复通知
      
    # 规则2: 退款类消息 -> 企业微信
    - name: "退款提醒"
      keywords: ["退款", "退钱", "退货"]
      channels: ["wecom"]
      priority: 4
      cooldown: 60
      
    # 规则3: 订单类消息 -> 桌面通知
    - name: "订单通知"
      keywords: ["订单", "下单", "购买"]
      channels: ["desktop"]
      priority: 3
      cooldown: 0
  
  # 渠道配置
  channels:
    # 钉钉机器人
    dingtalk:
      enabled: true
      webhook_url: "https://oapi.dingtalk.com/robot/send?access_token=xxx"
      secret: ""  # 加签密钥（可选）
      at_mobiles: []  # @的手机号列表
      
    # 企业微信机器人
    wecom:
      enabled: true
      webhook_url: "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx"
      
    # 邮件通知
    email:
      enabled: true
      smtp_server: "smtp.qq.com"
      smtp_port: 587
      username: "your_email@qq.com"
      password: "your_auth_code"
      to_addresses: ["admin@company.com"]
      
    # 桌面通知
    desktop:
      enabled: true
      duration: 5  # 显示时长（秒）
      
    # WebSocket实时推送
    websocket:
      enabled: true
      
    # 文件日志
    file:
      enabled: true
      path: "./notifications.log"
      
    # 控制台
    console:
      enabled: true
```

---

## 4. 实现计划

### 4.1 开发阶段

| 阶段 | 任务 | 预计时间 | 依赖 |
|------|------|----------|------|
| **Phase 3.1** | 后台截图功能 | 2-3天 | 无 |
| **Phase 3.2** | 通知系统框架 | 2-3天 | 无 |
| **Phase 3.3** | 钉钉/企业微信集成 | 2-3天 | 3.2 |
| **Phase 3.4** | WebSocket实时推送 | 2-3天 | 3.2 |
| **Phase 3.5** | 测试与优化 | 2-3天 | 全部 |

**总计**: 10-15天

### 4.2 详细任务分解

#### Phase 3.1: 后台截图功能

- [ ] 实现 `background_capture.py` 模块
- [ ] 使用 Win32 API PrintWindow
- [ ] 处理窗口最小化/恢复
- [ ] 测试微信兼容性
- [ ] 集成到 monitor.py
- [ ] 添加配置选项

#### Phase 3.2: 通知系统框架

- [ ] 设计通知系统架构
- [ ] 实现 `notification_system.py`
- [ ] 实现消息队列
- [ ] 实现基础通知渠道（文件、控制台）
- [ ] 实现通知规则引擎
- [ ] 集成到监控流程

#### Phase 3.3: 第三方通知集成

- [ ] 钉钉Webhook封装
- [ ] 企业微信Webhook封装
- [ ] 邮件SMTP封装
- [ ] 桌面通知封装
- [ ] 配置验证和测试

#### Phase 3.4: WebSocket实时推送

- [ ] 集成 Flask-SocketIO
- [ ] 实现消息广播
- [ ] Web界面实时更新
- [ ] 连接管理（断线重连）

#### Phase 3.5: 测试与优化

- [ ] 单元测试
- [ ] 集成测试
- [ ] 性能测试
- [ ] 文档更新

---

## 5. 技术选型

### 5.1 新增依赖

```txt
# 后台截图
pywin32>=306          # Win32 API访问

# 通知系统
aiohttp>=3.8.0        # 异步HTTP客户端（钉钉/企业微信）
aiosmtplib>=3.0.0     # 异步SMTP

# WebSocket
flask-socketio>=5.3.0 # WebSocket支持
python-socketio>=5.8.0

# 异步支持
asyncio-mqtt>=0.13.0  # 可选：MQTT支持
```

### 5.2 关键技术点

1. **后台截图**: `win32gui.PrintWindow`
2. **异步HTTP**: `aiohttp.ClientSession`
3. **异步邮件**: `aiosmtplib.SMTP`
4. **WebSocket**: `Flask-SocketIO`
5. **消息队列**: `asyncio.Queue`

---

## 6. 风险评估

| 风险 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|----------|
| PrintWindow不支持微信 | 中 | 高 | 准备DXGI备选方案 |
| 钉钉/企业微信API变更 | 低 | 中 | 封装抽象层，便于适配 |
| 异步代码复杂度 | 中 | 中 | 充分测试，完善文档 |
| 通知频率过高 | 中 | 中 | 实现冷却机制和限流 |

---

## 7. 验收标准

### 7.1 功能验收

- [ ] 微信窗口最小化时仍能截图识别
- [ ] 匹配到关键字后5秒内收到钉钉通知
- [ ] Web界面实时显示新消息（延迟<3秒）
- [ ] 支持按关键字配置不同通知渠道
- [ ] 通知冷却机制有效（不重复轰炸）

### 7.2 性能验收

- [ ] 后台截图耗时 < 2秒
- [ ] 通知发送延迟 < 5秒
- [ ] 内存占用增长 < 10%（相比v0.4.0）
- [ ] CPU占用无明显增加

---

## 8. 附录

### 8.1 钉钉机器人API

```python
import aiohttp
import json
import base64
import hmac
import hashlib
import time

async def send_dingtalk(webhook_url: str, secret: str, message: str):
    """发送钉钉消息"""
    timestamp = str(round(time.time() * 1000))
    string_to_sign = f"{timestamp}\n{secret}"
    hmac_code = hmac.new(
        secret.encode('utf-8'),
        string_to_sign.encode('utf-8'),
        digestmod=hashlib.sha256
    ).digest()
    sign = base64.b64encode(hmac_code).decode('utf-8')
    
    url = f"{webhook_url}&timestamp={timestamp}&sign={sign}"
    
    payload = {
        "msgtype": "text",
        "text": {"content": message}
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as resp:
            return await resp.json()
```

### 8.2 企业微信机器人API

```python
async def send_wecom(webhook_url: str, message: str):
    """发送企业微信消息"""
    payload = {
        "msgtype": "text",
        "text": {"content": message}
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(webhook_url, json=payload) as resp:
            return await resp.json()
```

---

**文档版本**: v1.0  
**最后更新**: 2026-02-03  
**状态**: 待评审
