#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
核心消息定义模块
定义统一的消息数据结构和消息源协议
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Protocol, List, Any
from enum import Enum


class PlatformType(str, Enum):
    """平台类型枚举"""

    WECHAT_WIN = "wechat_win"  # 微信桌面版（OCR）
    WECHAT_KF = "wechat_kf"  # 微信客服
    WECHAT_WORK = "wechat_work"  # 企业微信
    QQ = "qq"  # QQ
    DINGTALK = "dingtalk"  # 钉钉
    FEISHU = "feishu"  # 飞书
    SLACK = "slack"  # Slack
    CUSTOM = "custom"  # 自定义


@dataclass
class ChatMessage:
    """
    统一的消息数据结构

    所有消息源（OCR、API、Webhook等）都将消息转换为这个标准格式
    """

    # 必需字段
    id: str  # 消息唯一标识
    platform: str  # 平台类型（PlatformType的值）
    channel: str  # 会话/频道标识（窗口标题、群名、会话ID）
    content: str  # 消息文本内容
    timestamp: datetime  # 消息时间

    # 可选字段
    sender: str = ""  # 发送者昵称或ID
    sender_id: str = ""  # 发送者唯一ID
    message_type: str = "text"  # 消息类型：text, image, file等
    raw_data: Optional[dict] = None  # 原始数据（保留上游平台的原始信息）

    # 内部处理字段
    source_name: str = ""  # 消息源名称（用于调试）
    processed: bool = False  # 是否已处理
    matched_keywords: List[str] = field(default_factory=list)  # 匹配到的关键字

    def __post_init__(self):
        """初始化后处理"""
        if isinstance(self.timestamp, str):
            # 尝试解析 ISO 格式时间字符串
            try:
                ts_str = str(self.timestamp)
                ts_str = ts_str.replace("Z", "+00:00")
                if ts_str.endswith("+00:00"):
                    ts_str = ts_str[:-6]
                self.timestamp = datetime.fromisoformat(ts_str)
            except Exception:
                self.timestamp = datetime.now()

    def to_dict(self) -> dict:
        """转换为字典（用于数据库存储）"""
        return {
            "id": self.id,
            "platform": self.platform,
            "channel": self.channel,
            "sender": self.sender,
            "sender_id": self.sender_id,
            "content": self.content,
            "message_type": self.message_type,
            "timestamp": self.timestamp.isoformat(),
            "source_name": self.source_name,
            "matched_keywords": ",".join(self.matched_keywords)
            if self.matched_keywords
            else "",
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ChatMessage":
        """从字典创建实例"""
        return cls(
            id=data.get("id", ""),
            platform=data.get("platform", ""),
            channel=data.get("channel", ""),
            sender=data.get("sender", ""),
            sender_id=data.get("sender_id", ""),
            content=data.get("content", ""),
            message_type=data.get("message_type", "text"),
            timestamp=data.get("timestamp", datetime.now()),
            source_name=data.get("source_name", ""),
            matched_keywords=data.get("matched_keywords", "").split(",")
            if data.get("matched_keywords")
            else [],
        )


class MessageSource(Protocol):
    """
    消息源协议

    所有消息源（OCR、API、Webhook等）都必须实现这个协议
    """

    name: str  # 消息源名称
    platform: str  # 平台类型

    def poll(self) -> List[ChatMessage]:
        """
        拉取新消息

        Returns:
            自上次调用以来的新消息列表
        """
        ...

    def is_available(self) -> bool:
        """
        检查消息源是否可用

        Returns:
            True 如果消息源可以正常工作
        """
        ...

    def get_status(self) -> dict:
        """
        获取消息源状态信息

        Returns:
            包含状态信息的字典
        """
        ...


@dataclass
class SourceStatus:
    """消息源状态信息"""

    name: str
    platform: str
    is_available: bool
    last_poll_time: Optional[datetime] = None
    last_error: Optional[str] = None
    message_count: int = 0
    error_count: int = 0
