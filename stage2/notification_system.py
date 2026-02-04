#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
异步通知系统
支持多渠道通知：钉钉、企业微信、邮件、桌面通知

特性：
1. 异步发送，不阻塞监控流程
2. 通知规则引擎，按关键字路由
3. 冷却机制，防止重复轰炸
4. 多渠道并发发送

作者：AI Assistant
日期：2026年
"""

import asyncio
import json
import base64
import hmac
import hashlib
import time
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timedelta
from enum import Enum

import aiohttp
from database import MessageRecord

logger = logging.getLogger(__name__)


class NotificationPriority(Enum):
    """通知优先级"""

    CRITICAL = 1  # 紧急（立即通知）
    HIGH = 2  # 高优先级
    NORMAL = 3  # 普通
    LOW = 4  # 低优先级
    IGNORE = 5  # 忽略（仅记录）


@dataclass
class NotificationMessage:
    """通知消息"""

    title: str
    content: str
    priority: NotificationPriority = NotificationPriority.NORMAL
    keyword: str = ""  # 匹配的关键字
    source: str = ""  # 消息来源
    timestamp: datetime = field(default_factory=datetime.now)
    extra_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NotificationRule:
    """通知规则"""

    name: str  # 规则名称
    keywords: List[str]  # 匹配关键字列表
    channels: List[str]  # 通知渠道列表
    priority: NotificationPriority = NotificationPriority.NORMAL
    cooldown: int = 300  # 冷却时间（秒）
    enabled: bool = True  # 是否启用


class NotificationChannel(ABC):
    """通知渠道抽象基类"""

    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.enabled = config.get("enabled", True)
        self.last_error: Optional[str] = None

    @abstractmethod
    async def send(self, message: NotificationMessage) -> bool:
        """发送通知，返回是否成功"""
        pass

    def is_available(self) -> bool:
        """检查渠道是否可用"""
        return self.enabled


class DingTalkChannel(NotificationChannel):
    """钉钉机器人通知渠道"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__("dingtalk", config)
        self.webhook_url = config.get("webhook_url", "")
        self.secret = config.get("secret", "")
        self.at_mobiles = config.get("at_mobiles", [])

        if not self.webhook_url:
            logger.warning("钉钉Webhook URL未配置")
            self.enabled = False

    def _generate_sign(self, timestamp: str) -> str:
        """生成钉钉签名"""
        if not self.secret:
            return ""

        string_to_sign = f"{timestamp}\n{self.secret}"
        hmac_code = hmac.new(
            self.secret.encode("utf-8"),
            string_to_sign.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).digest()
        return base64.b64encode(hmac_code).decode("utf-8")

    async def send(self, message: NotificationMessage) -> bool:
        """发送钉钉消息"""
        if not self.is_available():
            return False

        try:
            timestamp = str(round(time.time() * 1000))
            sign = self._generate_sign(timestamp)

            # 构建URL
            url = self.webhook_url
            if sign:
                url = f"{url}&timestamp={timestamp}&sign={sign}"

            # 构建消息内容
            content = f"【微信监控】{message.title}\n\n{message.content}"

            payload = {
                "msgtype": "text",
                "text": {"content": content},
                "at": {"atMobiles": self.at_mobiles, "isAtAll": False},
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as resp:
                    result = await resp.json()

                    if result.get("errcode") == 0:
                        logger.info(f"钉钉通知发送成功: {message.title}")
                        return True
                    else:
                        self.last_error = result.get("errmsg", "未知错误")
                        logger.error(f"钉钉通知失败: {self.last_error}")
                        return False

        except Exception as e:
            self.last_error = str(e)
            logger.error(f"钉钉通知异常: {e}")
            return False


class WeComChannel(NotificationChannel):
    """企业微信机器人通知渠道"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__("wecom", config)
        self.webhook_url = config.get("webhook_url", "")

        if not self.webhook_url:
            logger.warning("企业微信Webhook URL未配置")
            self.enabled = False

    async def send(self, message: NotificationMessage) -> bool:
        """发送企业微信消息"""
        if not self.is_available():
            return False

        try:
            content = f"【微信监控】{message.title}\n\n{message.content}"

            payload = {"msgtype": "text", "text": {"content": content}}

            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=payload) as resp:
                    result = await resp.json()

                    if result.get("errcode") == 0:
                        logger.info(f"企业微信通知发送成功: {message.title}")
                        return True
                    else:
                        self.last_error = result.get("errmsg", "未知错误")
                        logger.error(f"企业微信通知失败: {self.last_error}")
                        return False

        except Exception as e:
            self.last_error = str(e)
            logger.error(f"企业微信通知异常: {e}")
            return False


class EmailChannel(NotificationChannel):
    """邮件通知渠道"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__("email", config)
        self.smtp_server = config.get("smtp_server", "")
        self.smtp_port = config.get("smtp_port", 587)
        self.username = config.get("username", "")
        self.password = config.get("password", "")
        self.to_addresses = config.get("to_addresses", [])

        if not all([self.smtp_server, self.username, self.password]):
            logger.warning("邮件SMTP配置不完整")
            self.enabled = False

    async def send(self, message: NotificationMessage) -> bool:
        """发送邮件"""
        if not self.is_available():
            return False

        try:
            # 这里使用 aiosmtplib 发送邮件
            # 为了简化，先使用同步方式
            import aiosmtplib
            from email.mime.text import MIMEText
            from email.header import Header

            msg = MIMEText(message.content, "plain", "utf-8")
            msg["From"] = self.username
            msg["To"] = ", ".join(self.to_addresses)
            msg["Subject"] = Header(f"【微信监控】{message.title}", "utf-8")

            await aiosmtplib.send(
                msg,
                hostname=self.smtp_server,
                port=self.smtp_port,
                username=self.username,
                password=self.password,
                start_tls=True,
            )

            logger.info(f"邮件通知发送成功: {message.title}")
            return True

        except ImportError:
            logger.warning("aiosmtplib 未安装，邮件通知不可用")
            self.last_error = "aiosmtplib 未安装"
            return False
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"邮件通知异常: {e}")
            return False


class DesktopChannel(NotificationChannel):
    """桌面通知渠道"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__("desktop", config)
        self.duration = config.get("duration", 5)
        self._toaster = None

        # 尝试导入 win10toast
        try:
            from win10toast import ToastNotifier

            self._toaster = ToastNotifier()
        except ImportError:
            logger.warning("win10toast 未安装，桌面通知不可用")
            self.enabled = False

    async def send(self, message: NotificationMessage) -> bool:
        """显示桌面通知"""
        if not self.is_available() or not self._toaster:
            return False

        try:
            # win10toast 是同步的，在线程中运行
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self._toaster.show_toast(
                    f"【微信监控】{message.title}",
                    message.content[:100],  # 限制长度
                    duration=self.duration,
                    threaded=True,
                ),
            )
            logger.info(f"桌面通知显示成功: {message.title}")
            return True

        except Exception as e:
            self.last_error = str(e)
            logger.error(f"桌面通知异常: {e}")
            return False


class FileChannel(NotificationChannel):
    """文件日志通知渠道"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__("file", config)
        self.log_path = config.get("path", "./notifications.log")
        self._setup_logger()

    def _setup_logger(self):
        """设置日志记录器"""
        self.logger = logging.getLogger("notification_file")
        self.logger.setLevel(logging.INFO)

        # 避免重复添加handler
        if not self.logger.handlers:
            handler = logging.FileHandler(self.log_path, encoding="utf-8")
            handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
                )
            )
            self.logger.addHandler(handler)

    async def send(self, message: NotificationMessage) -> bool:
        """写入日志文件"""
        try:
            self.logger.info(
                f"[{message.priority.name}] {message.title}: {message.content[:200]}"
            )
            return True
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"文件通知异常: {e}")
            return False


class ConsoleChannel(NotificationChannel):
    """控制台通知渠道"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__("console", config)

    async def send(self, message: NotificationMessage) -> bool:
        """打印到控制台"""
        try:
            print("\n" + "=" * 60)
            print(f"【{message.priority.name}】{message.title}")
            print("-" * 60)
            print(message.content)
            print("=" * 60)
            return True
        except Exception as e:
            self.last_error = str(e)
            return False


class NotificationSystem:
    """通知系统主类"""

    # 渠道工厂映射
    CHANNEL_FACTORIES = {
        "dingtalk": DingTalkChannel,
        "wecom": WeComChannel,
        "email": EmailChannel,
        "desktop": DesktopChannel,
        "file": FileChannel,
        "console": ConsoleChannel,
    }

    def __init__(self, config: Dict[str, Any]):
        """
        初始化通知系统

        参数:
            config: 配置字典
        """
        self.config = config
        self.enabled = config.get("notification", {}).get("enabled", False)

        # 初始化渠道
        self.channels: Dict[str, NotificationChannel] = {}
        self._init_channels()

        # 初始化规则
        self.rules: List[NotificationRule] = []
        self._init_rules()

        # 冷却记录
        self._cooldown_records: Dict[str, datetime] = {}

        logger.info(
            f"通知系统初始化完成: {len(self.channels)} 个渠道, {len(self.rules)} 条规则"
        )

    def _init_channels(self):
        """初始化通知渠道"""
        channels_config = self.config.get("notification", {}).get("channels", {})

        for name, channel_config in channels_config.items():
            if name in self.CHANNEL_FACTORIES:
                try:
                    channel_class = self.CHANNEL_FACTORIES[name]
                    channel = channel_class(channel_config)
                    self.channels[name] = channel

                    if channel.enabled:
                        logger.info(f"通知渠道已启用: {name}")
                    else:
                        logger.warning(f"通知渠道未启用: {name}")

                except Exception as e:
                    logger.error(f"初始化通知渠道失败 {name}: {e}")
            else:
                logger.warning(f"未知的通知渠道: {name}")

    def _init_rules(self):
        """初始化通知规则"""
        rules_config = self.config.get("notification", {}).get("rules", [])

        for rule_config in rules_config:
            try:
                rule = NotificationRule(
                    name=rule_config.get("name", "未命名规则"),
                    keywords=rule_config.get("keywords", []),
                    channels=rule_config.get("channels", []),
                    priority=NotificationPriority[
                        rule_config.get("priority", "NORMAL")
                    ],
                    cooldown=rule_config.get("cooldown", 300),
                    enabled=rule_config.get("enabled", True),
                )
                self.rules.append(rule)

                if rule.enabled:
                    logger.info(f"通知规则已启用: {rule.name} -> {rule.channels}")

            except Exception as e:
                logger.error(f"初始化通知规则失败: {e}")

    def _check_cooldown(self, key: str, cooldown: int) -> bool:
        """
        检查是否处于冷却期

        返回:
            True - 可以发送（不在冷却期）
            False - 处于冷却期
        """
        if cooldown <= 0:
            return True

        now = datetime.now()
        last_time = self._cooldown_records.get(key)

        if last_time:
            elapsed = (now - last_time).total_seconds()
            if elapsed < cooldown:
                logger.debug(f"通知处于冷却期: {key}, 还剩 {cooldown - elapsed:.0f} 秒")
                return False

        self._cooldown_records[key] = now
        return True

    def _match_rules(self, message: NotificationMessage) -> List[NotificationRule]:
        """匹配适用的规则"""
        matched_rules = []

        for rule in self.rules:
            if not rule.enabled:
                continue

            # 检查关键字匹配
            if any(kw in message.keyword for kw in rule.keywords):
                matched_rules.append(rule)

        return matched_rules

    async def notify(self, message: NotificationMessage) -> Dict[str, bool]:
        """
        发送通知

        参数:
            message: 通知消息

        返回:
            各渠道发送结果
        """
        if not self.enabled:
            logger.debug("通知系统已禁用")
            return {}

        # 匹配规则
        matched_rules = self._match_rules(message)

        if not matched_rules:
            # 没有匹配的规则，使用默认渠道
            default_channels = self.config.get("notification", {}).get(
                "default_channels", ["console", "file"]
            )
            channels_to_notify = default_channels
            cooldown = 0
        else:
            # 合并所有匹配规则的渠道
            channels_to_notify = set()
            cooldown = min(rule.cooldown for rule in matched_rules)
            for rule in matched_rules:
                channels_to_notify.update(rule.channels)
            channels_to_notify = list(channels_to_notify)

        # 检查冷却
        cooldown_key = f"{message.keyword}:{message.source}"
        if not self._check_cooldown(cooldown_key, cooldown):
            logger.info(f"通知被冷却跳过: {message.title}")
            return {}

        # 并发发送通知
        results = {}
        tasks = []

        for channel_name in channels_to_notify:
            channel = self.channels.get(channel_name)
            if channel and channel.is_available():
                task = self._send_with_timeout(channel, message)
                tasks.append((channel_name, task))
            else:
                results[channel_name] = False

        # 执行所有发送任务
        if tasks:
            for channel_name, task in tasks:
                try:
                    result = await task
                    results[channel_name] = result
                except Exception as e:
                    logger.error(f"发送通知失败 {channel_name}: {e}")
                    results[channel_name] = False

        # 记录结果
        success_count = sum(1 for r in results.values() if r)
        logger.info(f"通知发送完成: {success_count}/{len(results)} 成功")

        return results

    async def _send_with_timeout(
        self,
        channel: NotificationChannel,
        message: NotificationMessage,
        timeout: int = 10,
    ) -> bool:
        """带超时的发送"""
        try:
            return await asyncio.wait_for(channel.send(message), timeout=timeout)
        except asyncio.TimeoutError:
            logger.error(f"通知发送超时: {channel.name}")
            return False

    async def notify_from_record(self, record: MessageRecord) -> Dict[str, bool]:
        """
        从数据库记录创建通知

        参数:
            record: 消息记录
        """
        message = NotificationMessage(
            title=f"关键字匹配: {record.matched_keyword}",
            content=record.message_text,
            keyword=record.matched_keyword,
            source=record.window_title,
            extra_data={
                "record_id": record.id,
                "screenshot_path": record.screenshot_path,
            },
        )

        return await self.notify(message)

    def get_status(self) -> Dict[str, Any]:
        """获取通知系统状态"""
        return {
            "enabled": self.enabled,
            "channels": {
                name: {
                    "enabled": ch.enabled,
                    "available": ch.is_available(),
                    "last_error": ch.last_error,
                }
                for name, ch in self.channels.items()
            },
            "rules": [
                {
                    "name": r.name,
                    "keywords": r.keywords,
                    "channels": r.channels,
                    "enabled": r.enabled,
                }
                for r in self.rules
            ],
        }


# 全局通知系统实例
_notification_system: Optional[NotificationSystem] = None


def init_notification_system(config: Dict[str, Any]) -> NotificationSystem:
    """初始化全局通知系统"""
    global _notification_system
    _notification_system = NotificationSystem(config)
    return _notification_system


def get_notification_system() -> Optional[NotificationSystem]:
    """获取全局通知系统实例"""
    return _notification_system


async def send_notification(message: NotificationMessage) -> Dict[str, bool]:
    """快捷发送通知"""
    system = get_notification_system()
    if system:
        return await system.notify(message)
    return {}


# 测试代码
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # 测试配置
    test_config = {
        "notification": {
            "enabled": True,
            "default_channels": ["console", "file"],
            "rules": [
                {
                    "name": "测试规则",
                    "keywords": ["测试", "test"],
                    "channels": ["console", "file"],
                    "priority": "NORMAL",
                    "cooldown": 60,
                }
            ],
            "channels": {
                "console": {"enabled": True},
                "file": {"enabled": True, "path": "./test_notifications.log"},
            },
        }
    }

    async def test():
        # 初始化
        system = init_notification_system(test_config)

        # 测试通知
        message = NotificationMessage(
            title="测试通知", content="这是一条测试通知消息", keyword="测试"
        )

        results = await system.notify(message)
        print(f"\n发送结果: {results}")

        # 测试冷却
        print("\n测试冷却机制（应该被跳过）...")
        results2 = await system.notify(message)
        print(f"第二次发送结果: {results2}")

    # 运行测试
    asyncio.run(test())
