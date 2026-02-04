#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通知模块 - 支持多种通知方式

使用示例:
    notifier = NotificationManager()
    notifier.add_notifier(FileNotifier("./notifications.log"))
    notifier.notify("标题", "内容")
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional


class Notifier(ABC):
    """通知器抽象基类"""

    @abstractmethod
    def notify(self, title: str, content: str) -> None:
        """
        发送通知

        参数:
            title: 通知标题
            content: 通知内容
        """
        pass


class FileNotifier(Notifier):
    """文件通知器 - 将通知写入日志文件"""

    def __init__(self, log_path: str = "./notifications.log"):
        self.log_path = log_path
        # 创建独立的logger
        self.logger = logging.getLogger("notification_file")
        self.logger.setLevel(logging.INFO)

        # 避免重复添加handler
        if not self.logger.handlers:
            handler = logging.FileHandler(log_path, encoding="utf-8")
            handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
                )
            )
            self.logger.addHandler(handler)

    def notify(self, title: str, content: str) -> None:
        """写入通知到文件"""
        self.logger.info(f"[{title}] {content}")


class ConsoleNotifier(Notifier):
    """控制台通知器 - 在终端显示通知"""

    def notify(self, title: str, content: str) -> None:
        """在控制台打印通知"""
        print("\n" + "=" * 60)
        print(f"【通知】{title}")
        print("-" * 60)
        print(content)
        print("=" * 60)


class DesktopNotifier(Notifier):
    """桌面通知器 - 使用系统通知（Windows Toast）"""

    def __init__(self):
        self.enabled = False
        try:
            # 尝试导入 Windows Toast 库
            from win10toast import ToastNotifier

            self.toaster = ToastNotifier()
            self.enabled = True
        except ImportError:
            logging.warning("win10toast 未安装，桌面通知功能不可用")
            logging.warning("请运行: pip install win10toast")

    def notify(self, title: str, content: str) -> None:
        """显示桌面通知"""
        if not self.enabled:
            return

        try:
            self.toaster.show_toast(
                title,
                content,
                duration=5,
                threaded=True,
            )
        except Exception as e:
            logging.error(f"桌面通知失败: {e}")


class NotificationManager:
    """通知管理器 - 管理多个通知器并支持防抖"""

    def __init__(self, dedup_interval: int = 300):
        """
        初始化通知管理器

        参数:
            dedup_interval: 去重时间间隔（秒），默认5分钟
        """
        self.notifiers: List[Notifier] = []
        self.dedup_interval = dedup_interval
        self._recent_notifications: dict = {}  # 用于去重

    def add_notifier(self, notifier: Notifier) -> None:
        """添加通知器"""
        self.notifiers.append(notifier)

    def _should_notify(self, key: str) -> bool:
        """
        检查是否应该发送通知（防抖）

        参数:
            key: 通知的唯一标识

        返回:
            True 表示应该发送，False 表示应该跳过
        """
        now = datetime.now()

        if key in self._recent_notifications:
            last_time = self._recent_notifications[key]
            elapsed = (now - last_time).total_seconds()

            if elapsed < self.dedup_interval:
                return False

        self._recent_notifications[key] = now
        return True

    def notify(self, title: str, content: str, dedup_key: Optional[str] = None) -> None:
        """
        发送通知到所有通知器

        参数:
            title: 通知标题
            content: 通知内容
            dedup_key: 去重标识，如果提供则用于防抖检查
        """
        # 生成去重key
        if dedup_key is None:
            dedup_key = f"{title}:{content[:50]}"

        # 检查是否应该发送
        if not self._should_notify(dedup_key):
            logging.debug(f"通知被防抖跳过: {title}")
            return

        # 发送到所有通知器
        for notifier in self.notifiers:
            try:
                notifier.notify(title, content)
            except Exception as e:
                logging.error(f"通知器 {type(notifier).__name__} 失败: {e}")


def create_notifier_from_config(config: dict) -> Optional[NotificationManager]:
    """
    从配置创建通知管理器

    配置示例:
        notification:
          enabled: true
          dedup_interval: 300
          file:
            enabled: true
            path: ./notifications.log
          console:
            enabled: true
          desktop:
            enabled: false
    """
    if not config.get("notification", {}).get("enabled", False):
        return None

    notif_config = config["notification"]
    dedup_interval = notif_config.get("dedup_interval", 300)

    manager = NotificationManager(dedup_interval=dedup_interval)

    # 文件通知
    if notif_config.get("file", {}).get("enabled", False):
        log_path = notif_config["file"].get("path", "./notifications.log")
        manager.add_notifier(FileNotifier(log_path))

    # 控制台通知
    if notif_config.get("console", {}).get("enabled", True):
        manager.add_notifier(ConsoleNotifier())

    # 桌面通知
    if notif_config.get("desktop", {}).get("enabled", False):
        manager.add_notifier(DesktopNotifier())

    return manager


if __name__ == "__main__":
    # 测试代码
    print("测试通知模块...")

    manager = NotificationManager(dedup_interval=5)
    manager.add_notifier(ConsoleNotifier())
    manager.add_notifier(FileNotifier("./test_notifications.log"))

    # 测试通知
    manager.notify("测试标题", "这是一条测试通知")

    # 测试防抖
    print("\n5秒内重复发送相同通知应该被跳过...")
    manager.notify("测试标题", "这是一条测试通知", dedup_key="test1")
    manager.notify("测试标题", "这是一条测试通知", dedup_key="test1")

    print("\n通知测试完成")
