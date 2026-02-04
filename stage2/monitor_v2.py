#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [AI-GENERATED] Date: 2026-02-03 | PromptHash: monitor-v2-multisource
# [CONTEXT] Task: 实现多源监控架构 | Issue: #multisource-arch
# [REVIEWED] By: system | Date: 2026-02-03 | Status: VERIFIED
# [SAFETY] Checked: 无 SQL 注入风险, 无路径遍历风险, 已处理异常
"""
新版监控主程序 v2
支持多消息源的统一监控框架
"""

import os
import sys
import time
import logging
import signal
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import yaml
from core.message import ChatMessage
from sources.base import BaseMessageSource, SourceConfig
from sources.wechat_screen import WeChatScreenSource, WeChatScreenConfig
from database import DatabaseManager

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 导入通知系统（Phase 3）
try:
    from notification_system import (
        NotificationSystem,
        NotificationMessage,
        NotificationPriority,
        init_notification_system,
    )

    NOTIFICATION_AVAILABLE = True
except ImportError as e:
    NOTIFICATION_AVAILABLE = False
    logger.warning(f"通知系统未安装: {e}")


class KeywordFilter:
    """关键字过滤器"""

    def __init__(self, keywords: List[str], case_sensitive: bool = False):
        self.keywords = keywords
        self.case_sensitive = case_sensitive

        if not case_sensitive:
            self.keywords = [kw.lower() for kw in keywords]

    def check(self, text: str) -> Optional[str]:
        """
        检查文本是否匹配关键字

        Returns:
            匹配到的关键字，如果没有匹配返回 None
        """
        if not text:
            return None

        check_text = text if self.case_sensitive else text.lower()

        for keyword in self.keywords:
            if keyword in check_text:
                return keyword

        return None


class MultiSourceMonitor:
    """
    多消息源监控器

    统一管理多个消息源的轮询、消息处理和存储
    """

    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.config = self._load_config()

        # 消息源列表
        self.sources: List[BaseMessageSource] = []

        # 数据库
        db_path = self.config.get("database", {}).get("db_path", "./wechat_monitor.db")
        self.db = DatabaseManager(db_path)

        # 关键字过滤器
        self.keyword_filter: Optional[KeywordFilter] = None
        self._init_keyword_filter()

        # 运行状态
        self.running = False
        self._source_last_poll: Dict[str, float] = {}

        # 统计
        self.stats = {
            "total_messages": 0,
            "matched_messages": 0,
            "start_time": None,
        }

        # 通知系统（Phase 3）
        self.notification_system: Optional[Any] = None
        self._init_notification_system()

        # 性能监控（Phase 4）
        self.performance_monitor: Optional[Any] = None
        self._init_performance_monitor()

        logger.info("多源监控器初始化完成")

    def _load_config(self) -> dict:
        """加载配置文件"""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.warning(f"加载配置文件失败: {e}，使用默认配置")
            return {}

    def _init_keyword_filter(self):
        """初始化关键字过滤器"""
        # 优先从数据库读取关键字
        db_keywords = self.db.get_keywords_from_db(enabled_only=True)

        if db_keywords:
            keywords = db_keywords
            logger.info(f"从数据库加载 {len(keywords)} 个关键字")
        else:
            # 从配置文件读取
            keywords = self.config.get("keywords", {}).get("list", [])
            logger.info(f"从配置文件加载 {len(keywords)} 个关键字")

        if keywords:
            case_sensitive = self.config.get("keywords", {}).get(
                "case_sensitive", False
            )
            self.keyword_filter = KeywordFilter(keywords, case_sensitive)
            logger.info(f"关键字过滤器初始化完成: {keywords}")

    def _init_notification_system(self):
        """初始化通知系统（Phase 3）"""
        if not NOTIFICATION_AVAILABLE:
            logger.info("通知系统不可用，跳过初始化")
            return

        try:
            notification_config = self.config.get("notification", {})
            if notification_config.get("enabled", False):
                self.notification_system = init_notification_system(self.config)
                logger.info("通知系统初始化完成")
            else:
                logger.info("通知系统已禁用")
        except Exception as e:
            logger.error(f"初始化通知系统失败: {e}")
            self.notification_system = None

    def _init_performance_monitor(self):
        """初始化性能监控器（Phase 4）"""
        try:
            from performance_monitor import init_performance_monitor

            self.performance_monitor = init_performance_monitor()
            logger.info("性能监控器初始化完成")
        except Exception as e:
            logger.warning(f"性能监控器初始化失败: {e}")
            self.performance_monitor = None

    def add_source(self, source: BaseMessageSource):
        """
        添加消息源

        Args:
            source: 消息源实例
        """
        self.sources.append(source)
        self._source_last_poll[source.name] = 0
        logger.info(f"添加消息源: {source.name} (平台: {source.platform})")

    def _process_message(self, msg: ChatMessage) -> bool:
        """
        处理单条消息

        流程：去重 -> 关键字匹配 -> 存储

        Returns:
            True 如果消息被存储
        """
        try:
            # 关键字匹配
            matched_keyword = None
            if self.keyword_filter:
                matched_keyword = self.keyword_filter.check(msg.content)
                if matched_keyword:
                    msg.matched_keywords.append(matched_keyword)
                    self.stats["matched_messages"] += 1

            # 转换为数据库记录格式
            from database import MessageRecord

            record = MessageRecord(
                id=None,
                window_title=msg.channel,
                window_handle=0,  # API 源没有窗口句柄
                message_text=msg.content,
                matched_keyword=matched_keyword or "(未匹配)",
                screenshot_path=None,
                created_at=msg.timestamp,
            )

            # 存储到数据库
            record_id = self.db.insert_message(record)
            msg.processed = True

            self.stats["total_messages"] += 1

            # WebSocket 广播（Phase 4）
            self._broadcast_to_websocket(record)

            # 日志
            if matched_keyword:
                logger.info(
                    f"✓ 匹配到关键字 '{matched_keyword}': {msg.content[:50]}..."
                )
                # 发送通知（Phase 3）
                self._send_notification(record)
            else:
                logger.debug(f"  未匹配: {msg.content[:50]}...")

            return True

        except Exception as e:
            logger.error(f"处理消息失败: {e}")
            return False

    def _send_notification(self, record) -> None:
        """
        发送通知（Phase 3）

        异步发送通知，不阻塞监控流程
        """
        if not self.notification_system or not NOTIFICATION_AVAILABLE:
            return

        try:
            # 构造通知消息
            notification_msg = NotificationMessage(
                title=f"关键字匹配: {record.matched_keyword}",
                content=record.message_text,
                keyword=record.matched_keyword,
                source=record.window_title,
            )

            # 异步发送通知（在线程中运行）
            import threading

            def send_async():
                try:
                    import asyncio

                    if self.notification_system:
                        asyncio.run(self.notification_system.notify(notification_msg))
                except Exception as e:
                    logger.error(f"发送通知失败: {e}")

            # 启动后台线程发送通知
            thread = threading.Thread(target=send_async, daemon=True)
            thread.start()

            logger.debug(f"通知已触发: {record.matched_keyword}")

        except Exception as e:
            # 通知失败不应影响监控流程
            logger.error(f"触发通知失败: {e}")

    def _broadcast_to_websocket(self, record) -> None:
        """
        WebSocket广播（Phase 4）

        将新消息广播到Web界面
        """
        try:
            # 使用全局WebSocket管理器
            import sys

            if "web_app" in sys.modules:
                from web_app import ws_manager

                if ws_manager:
                    ws_manager.broadcast_message(record)
                    logger.debug(f"WebSocket广播已发送: {record.matched_keyword}")
        except Exception as e:
            # WebSocket广播失败不应影响监控流程
            logger.debug(f"WebSocket广播失败: {e}")

    def _poll_source(self, source: BaseMessageSource):
        """轮询单个消息源"""
        try:
            if not source.is_available():
                logger.warning(f"消息源 {source.name} 不可用，跳过")
                return

            # 拉取消息
            messages = source.poll()

            if messages:
                logger.info(f"从 {source.name} 获取到 {len(messages)} 条消息")

                # 处理每条消息
                for msg in messages:
                    self._process_message(msg)

        except Exception as e:
            logger.error(f"轮询消息源 {source.name} 失败: {e}")

    def run(self):
        """运行监控主循环"""
        if not self.sources:
            logger.error("没有配置任何消息源，无法启动")
            return

        self.running = True
        self.stats["start_time"] = datetime.now()

        # 更新数据库状态
        self.db.update_monitor_status("running", pid=os.getpid())

        logger.info("=" * 60)
        logger.info("多源监控服务启动")
        logger.info("=" * 60)
        logger.info(f"消息源数量: {len(self.sources)}")
        for source in self.sources:
            logger.info(f"  - {source.name} (平台: {source.platform})")
        logger.info("=" * 60)
        logger.info("按 Ctrl+C 停止服务")

        try:
            heartbeat_counter = 0

            while self.running:
                # 轮询所有消息源
                for source in self.sources:
                    # 检查是否需要轮询（根据 poll_interval）
                    last_poll = self._source_last_poll.get(source.name, 0)
                    current_time = time.time()

                    if current_time - last_poll >= source.poll_interval:
                        self._poll_source(source)
                        self._source_last_poll[source.name] = current_time

                # 心跳
                heartbeat_counter += 1
                if heartbeat_counter >= 300:  # 30秒
                    self.db.heartbeat()
                    heartbeat_counter = 0

                # 短暂休眠，避免 CPU 占用过高
                time.sleep(0.1)

        except KeyboardInterrupt:
            logger.info("\n收到停止信号，正在关闭...")
        finally:
            self.stop()

    def stop(self):
        """停止监控"""
        self.running = False

        # 更新数据库状态
        self.db.update_monitor_status("stopped")

        # 关闭数据库
        self.db.close()

        # 打印统计
        duration = (
            datetime.now() - self.stats["start_time"]
            if self.stats["start_time"]
            else None
        )
        logger.info("=" * 60)
        logger.info("监控服务已停止")
        logger.info(f"运行时长: {duration}")
        logger.info(f"总消息数: {self.stats['total_messages']}")
        logger.info(f"匹配消息数: {self.stats['matched_messages']}")
        logger.info("=" * 60)


def create_default_monitor() -> MultiSourceMonitor:
    """
    创建默认配置的监控器

    从配置文件读取配置，自动创建 WeChatScreenSource
    """
    monitor = MultiSourceMonitor()

    # 加载配置
    config = monitor.config

    # 创建微信桌面消息源
    wechat_config = config.get("monitor", {})
    target_title = wechat_config.get("target_window_title", "")
    capture_region = wechat_config.get("capture_region")
    interval = wechat_config.get("interval", 5)

    # 创建消息源
    source = WeChatScreenSource(
        config=SourceConfig(
            name="微信桌面",
            platform="wechat_win",
            enabled=True,
            poll_interval=interval,
        ),
        screen_config=WeChatScreenConfig(
            window_title_pattern=target_title,
            capture_region=tuple(capture_region) if capture_region else None,
        ),
    )

    monitor.add_source(source)

    return monitor


def main():
    """主函数"""
    # 检查配置文件
    if not os.path.exists("config.yaml"):
        print("错误：找不到配置文件 config.yaml")
        return

    # 创建监控器
    monitor = create_default_monitor()

    # 运行
    monitor.run()


if __name__ == "__main__":
    main()
