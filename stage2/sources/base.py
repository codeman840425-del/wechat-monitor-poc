#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
消息源基类模块
提供所有消息源的公共基础功能
"""

import logging
import hashlib
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Set
from dataclasses import dataclass, field

from core.message import ChatMessage, SourceStatus

logger = logging.getLogger(__name__)


@dataclass
class SourceConfig:
    """消息源配置"""

    name: str  # 消息源名称
    platform: str  # 平台类型
    enabled: bool = True  # 是否启用
    poll_interval: int = 5  # 轮询间隔（秒）
    keywords: List[str] = field(default_factory=list)  # 该源关注的关键字


class BaseMessageSource(ABC):
    """
    消息源抽象基类

    所有具体的消息源实现都应该继承这个类
    """

    def __init__(self, config: SourceConfig):
        self.config = config
        self.name = config.name
        self.platform = config.platform
        self.enabled = config.enabled
        self.poll_interval = config.poll_interval

        # 状态追踪
        self._last_poll_time: Optional[datetime] = None
        self._last_error: Optional[str] = None
        self._message_count = 0
        self._error_count = 0
        self._seen_message_ids: Set[str] = set()  # 用于去重

        logger.info(f"初始化消息源: {self.name} (平台: {self.platform})")

    @abstractmethod
    def poll(self) -> List[ChatMessage]:
        """
        拉取新消息

        子类必须实现这个方法

        Returns:
            新消息列表
        """
        pass

    def is_available(self) -> bool:
        """
        检查消息源是否可用

        默认实现检查 enabled 状态和最后错误时间
        子类可以重写以提供更复杂的检查
        """
        if not self.enabled:
            return False

        # 如果最近5分钟内有错误，认为不可用
        if self._last_error and self._last_poll_time:
            from datetime import timedelta

            if datetime.now() - self._last_poll_time < timedelta(minutes=5):
                return False

        return True

    def get_status(self) -> SourceStatus:
        """获取消息源状态"""
        return SourceStatus(
            name=self.name,
            platform=self.platform,
            is_available=self.is_available(),
            last_poll_time=self._last_poll_time,
            last_error=self._last_error,
            message_count=self._message_count,
            error_count=self._error_count,
        )

    def _deduplicate_messages(self, messages: List[ChatMessage]) -> List[ChatMessage]:
        """
        消息去重

        基于消息 ID 进行去重
        """
        new_messages = []
        for msg in messages:
            if msg.id not in self._seen_message_ids:
                self._seen_message_ids.add(msg.id)
                new_messages.append(msg)

                # 限制去重集合大小，防止内存无限增长
                if len(self._seen_message_ids) > 10000:
                    # 保留最近 8000 条
                    self._seen_message_ids = set(list(self._seen_message_ids)[-8000:])

        return new_messages

    def _generate_message_id(
        self, content: str, timestamp: datetime, channel: str
    ) -> str:
        """
        生成消息唯一 ID

        用于没有原生 ID 的消息源（如 OCR）
        """
        # 使用内容哈希 + 时间 + 频道生成 ID
        content_hash = hashlib.md5(content.encode("utf-8")).hexdigest()[:8]
        time_str = timestamp.strftime("%Y%m%d%H%M%S")
        return f"{self.platform}_{channel}_{time_str}_{content_hash}"

    def _update_poll_status(self, success: bool, error_msg: Optional[str] = None):
        """更新轮询状态"""
        self._last_poll_time = datetime.now()

        if success:
            self._last_error = None
        else:
            self._error_count += 1
            self._last_error = error_msg or "Unknown error"
            logger.error(f"消息源 {self.name} 轮询失败: {self._last_error}")

    def enable(self):
        """启用消息源"""
        self.enabled = True
        logger.info(f"消息源 {self.name} 已启用")

    def disable(self):
        """禁用消息源"""
        self.enabled = False
        logger.info(f"消息源 {self.name} 已禁用")

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name}, platform={self.platform})"

    def __repr__(self) -> str:
        return self.__str__()
