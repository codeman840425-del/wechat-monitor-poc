#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信客服 API 消息源
通过 Webhook 接收微信客服消息
"""

import os
import sys
import json
import time
import logging
import hashlib
import hmac
import base64
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from threading import Lock

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sources.base import BaseMessageSource, SourceConfig
from core.message import ChatMessage

logger = logging.getLogger(__name__)


@dataclass
class WeChatApiConfig:
    """微信 API 配置"""

    app_id: str  # 小程序/公众号 AppID
    app_secret: str  # AppSecret
    token: str  # Webhook Token（用于验证）
    encoding_aes_key: Optional[str] = None  # 消息加密密钥（可选）
    encrypt_mode: str = "plaintext"  # 加密模式：plaintext, compatible, safe


class WeChatApiSource(BaseMessageSource):
    """
    微信客服 API 消息源

    通过 Webhook 接收微信推送的消息，实现实时获取客服消息
    """

    # 类级别的消息队列（用于存储 Webhook 接收到的消息）
    _message_queues: Dict[str, List[Dict]] = {}
    _queue_lock = Lock()

    def __init__(self, config: SourceConfig, api_config: WeChatApiConfig):
        super().__init__(config)
        self.api_config = api_config
        self._processed_message_ids: set = set()

        # 初始化消息队列
        with WeChatApiSource._queue_lock:
            if self.name not in WeChatApiSource._message_queues:
                WeChatApiSource._message_queues[self.name] = []

        logger.info(f"微信 API 消息源初始化: {self.name}")
        logger.info(f"AppID: {api_config.app_id[:8]}...")

    @classmethod
    def add_webhook_message(cls, source_name: str, message: Dict):
        """
        添加 Webhook 消息到队列

        由 Webhook 处理器调用
        """
        with cls._queue_lock:
            if source_name in cls._message_queues:
                cls._message_queues[source_name].append(message)
                logger.debug(f"消息已添加到队列 {source_name}: {message.get('MsgId')}")

    def poll(self) -> List[ChatMessage]:
        """
        拉取新消息

        从 Webhook 消息队列中获取消息
        """
        messages = []

        try:
            # 从队列获取消息
            with WeChatApiSource._queue_lock:
                queue = WeChatApiSource._message_queues.get(self.name, [])
                raw_messages = queue.copy()
                queue.clear()

            # 转换为 ChatMessage
            for raw_msg in raw_messages:
                try:
                    msg = self._parse_wechat_message(raw_msg)
                    if msg and msg.id not in self._processed_message_ids:
                        self._processed_message_ids.add(msg.id)
                        messages.append(msg)
                except Exception as e:
                    logger.error(f"解析微信消息失败: {e}, raw_msg: {raw_msg}")

            # 更新统计
            if messages:
                self._message_count += len(messages)
                logger.info(f"从 {self.name} 获取到 {len(messages)} 条新消息")

            self._update_poll_status(True)

        except Exception as e:
            logger.error(f"轮询微信 API 消息源失败: {e}")
            self._update_poll_status(False, str(e))

        return messages

    def _parse_wechat_message(self, raw_msg: Dict) -> Optional[ChatMessage]:
        """
        解析微信消息为统一格式

        微信消息格式文档：https://developers.weixin.qq.com/miniprogram/dev/framework/server/message/push.html
        """
        # 获取消息类型
        msg_type = raw_msg.get("MsgType", "")

        # 只处理文本消息
        if msg_type != "text":
            logger.debug(f"跳过非文本消息: {msg_type}")
            return None

        # 提取字段
        msg_id = str(raw_msg.get("MsgId", ""))
        from_user = raw_msg.get("FromUserName", "")  # 用户 OpenID
        to_user = raw_msg.get("ToUserName", "")  # 小程序/公众号 ID
        content = raw_msg.get("Content", "")
        create_time = raw_msg.get("CreateTime", int(time.time()))

        if not msg_id:
            # 如果没有 MsgId，生成一个
            msg_id = f"{from_user}_{create_time}"

        # 转换时间戳
        timestamp = datetime.fromtimestamp(int(create_time))

        # 创建 ChatMessage
        msg = ChatMessage(
            id=msg_id,
            platform="wechat_kf",
            channel=from_user[:16] + "..."
            if len(from_user) > 16
            else from_user,  # 用户标识作为频道
            sender=from_user,
            sender_id=from_user,
            content=content,
            timestamp=timestamp,
            message_type="text",
            source_name=self.name,
            raw_data=raw_msg,
        )

        return msg

    def is_available(self) -> bool:
        """检查消息源是否可用"""
        if not super().is_available():
            return False

        # 检查必要配置
        if not self.api_config.app_id or not self.api_config.app_secret:
            return False

        return True

    def verify_webhook_signature(
        self, signature: str, timestamp: str, nonce: str
    ) -> bool:
        """
        验证 Webhook 签名

        微信服务器会发送签名用于验证消息来源
        """
        try:
            # 按字典序排序 token, timestamp, nonce
            tmp_list = [self.api_config.token, timestamp, nonce]
            tmp_list.sort()
            tmp_str = "".join(tmp_list)

            # SHA1 加密
            hashcode = hashlib.sha1(tmp_str.encode()).hexdigest()

            return hashcode == signature
        except Exception as e:
            logger.error(f"验证签名失败: {e}")
            return False

    def get_access_token(self) -> Optional[str]:
        """
        获取微信 Access Token

        用于调用微信 API（如发送客服消息回复）
        """
        # TODO[P2]: 实现获取 access_token 的逻辑
        # 需要：1) 使用 app_id 和 app_secret 请求微信接口
        #      2) 缓存 token，避免频繁请求（token有效期7200秒）
        #      3) 实现自动刷新机制
        # 参考：https://developers.weixin.qq.com/doc/offiaccount/Basic_Information/Get_access_token.html
        logger.warning("get_access_token 未实现，返回 None")
        return None


def create_wechat_api_source(
    name: str,
    app_id: str,
    app_secret: str,
    token: str,
    encoding_aes_key: Optional[str] = None,
    poll_interval: int = 5,
) -> WeChatApiSource:
    """
    创建微信 API 消息源的工厂函数

    Args:
        name: 消息源名称
        app_id: 小程序/公众号 AppID
        app_secret: AppSecret
        token: Webhook Token
        encoding_aes_key: 消息加密密钥（可选）
        poll_interval: 轮询间隔

    Returns:
        WeChatApiSource 实例
    """
    config = SourceConfig(
        name=name,
        platform="wechat_kf",
        enabled=True,
        poll_interval=poll_interval,
    )

    api_config = WeChatApiConfig(
        app_id=app_id,
        app_secret=app_secret,
        token=token,
        encoding_aes_key=encoding_aes_key,
    )

    return WeChatApiSource(config, api_config)
