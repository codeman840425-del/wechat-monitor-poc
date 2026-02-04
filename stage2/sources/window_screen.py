#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用窗口截图消息源
支持多窗口、多应用的截图+OCR监控
可用于 QQ、飞书、钉钉等桌面应用
"""

import os
import sys
import time
import logging
import re
from datetime import datetime
from typing import List, Optional, Tuple, Any
from dataclasses import dataclass

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uiautomation as auto
from PIL import Image, ImageGrab
import pytesseract

from sources.base import BaseMessageSource, SourceConfig
from sources.wechat_screen import WeChatScreenSource, WeChatScreenConfig
from core.message import ChatMessage

logger = logging.getLogger(__name__)


@dataclass
class WindowScreenConfig:
    """窗口监控配置"""

    app_type: str = "wechat"  # 应用类型：wechat, qq, dingtalk, feishu, custom
    title_pattern: str = ""  # 窗口标题匹配模式（支持正则）
    title_contains: str = ""  # 窗口标题包含文字（简单匹配）
    capture_region: Optional[Tuple[int, int, int, int]] = None
    use_relative_region: bool = True
    ocr_lang: str = "chi_sim+eng"
    ocr_config: str = "--oem 3 --psm 6"
    preprocess_scale: float = 2.0

    # 应用特定的窗口类名（用于自动检测）
    class_name_patterns: Optional[List[str]] = None

    def __post_init__(self):
        if self.class_name_patterns is None:
            # 默认类名模式
            patterns = {
                "wechat": ["WeChat", "wechat"],
                "qq": ["TXGuiFoundation", "QQ"],
                "dingtalk": ["DingTalk"],
                "feishu": ["Feishu", "Lark"],
            }
            self.class_name_patterns = patterns.get(self.app_type, [])


class WindowScreenSource(BaseMessageSource):
    """
    通用窗口截图消息源

    支持监控多个不同的聊天窗口，适用于多会话场景
    """

    def __init__(self, config: SourceConfig, window_config: WindowScreenConfig):
        super().__init__(config)
        self.window_config = window_config
        self.window_element: Optional[Any] = None
        self.window_title: str = ""
        self._last_screenshot_hash: Optional[str] = None

        # 尝试查找窗口
        self._find_window()

    def _find_window(self) -> bool:
        """查找目标窗口"""
        try:
            desktop = auto.GetRootControl()

            for window in desktop.GetChildren():
                try:
                    class_name = window.ClassName or ""
                    window_name = window.Name or ""

                    # 检查类名匹配
                    class_match = False
                    patterns = self.window_config.class_name_patterns or []
                    for pattern in patterns:
                        if pattern.lower() in class_name.lower():
                            class_match = True
                            break

                    # 检查标题匹配
                    title_match = False
                    if self.window_config.title_pattern:
                        # 正则匹配
                        try:
                            if re.search(self.window_config.title_pattern, window_name):
                                title_match = True
                        except re.error:
                            logger.warning(
                                f"标题正则表达式错误: {self.window_config.title_pattern}"
                            )
                    elif self.window_config.title_contains:
                        # 包含匹配
                        if self.window_config.title_contains in window_name:
                            title_match = True
                    else:
                        # 没有指定标题模式，只要类名匹配即可
                        title_match = True

                    if class_match and title_match:
                        self.window_element = window
                        self.window_title = window_name
                        logger.info(f"找到窗口: {window_name} (类名: {class_name})")
                        return True

                except Exception as e:
                    continue

            logger.warning(
                f"未找到匹配的窗口: {self.window_config.title_contains or self.window_config.title_pattern}"
            )
            return False

        except Exception as e:
            logger.error(f"查找窗口失败: {e}")
            return False

    def _capture_screenshot(self) -> Optional[Any]:
        """截取窗口截图"""
        if not self.window_element:
            if not self._find_window():
                return None

        try:
            # 确保 window_element 不为 None
            if self.window_element is None:
                return None

            # 将窗口置为前台
            try:
                self.window_element.SetFocus()
                time.sleep(0.2)
            except:
                pass

            # 获取窗口位置
            rect = self.window_element.BoundingRectangle
            left, top, right, bottom = rect.left, rect.top, rect.right, rect.bottom

            # 使用配置的区域或整个窗口
            if self.window_config.capture_region:
                if self.window_config.use_relative_region:
                    r = self.window_config.capture_region
                    left, top, right, bottom = (
                        left + r[0],
                        top + r[1],
                        left + r[2],
                        top + r[3],
                    )
                else:
                    left, top, right, bottom = self.window_config.capture_region

            screenshot = ImageGrab.grab(bbox=(left, top, right, bottom))
            return screenshot

        except Exception as e:
            logger.error(f"截图失败: {e}")
            return None

    def _recognize_text(self, image: Any) -> str:
        """OCR 识别"""
        try:
            # 预处理
            if self.window_config.preprocess_scale > 1:
                width, height = image.size
                new_size = (
                    int(width * self.window_config.preprocess_scale),
                    int(height * self.window_config.preprocess_scale),
                )
                image = image.resize(new_size, Image.Resampling.LANCZOS)

            # OCR
            text = pytesseract.image_to_string(
                image,
                lang=self.window_config.ocr_lang,
                config=self.window_config.ocr_config,
            )
            return text
        except Exception as e:
            logger.error(f"OCR 失败: {e}")
            return ""

    def _calculate_image_hash(self, image: Any) -> str:
        """计算图像哈希"""
        try:
            import hashlib

            small = image.convert("L").resize((16, 16), Image.Resampling.LANCZOS)
            pixels = list(small.getdata())
            avg = sum(pixels) / len(pixels)

            diff = []
            for i in range(16):
                for j in range(15):
                    left_pixel = pixels[i * 16 + j]
                    right_pixel = pixels[i * 16 + j + 1]
                    diff.append(left_pixel > right_pixel)

            decimal_value = sum(bit << i for i, bit in enumerate(diff))
            return hex(decimal_value)[2:].zfill(16)
        except Exception as e:
            return ""

    def _parse_messages(self, text: str) -> List[ChatMessage]:
        """解析消息"""
        messages = []

        if not text.strip():
            return messages

        lines = [line.strip() for line in text.split("\n") if line.strip()]
        current_time = datetime.now()

        for line in lines:
            msg_id = self._generate_message_id(line, current_time, self.window_title)

            msg = ChatMessage(
                id=msg_id,
                platform=f"{self.window_config.app_type}_win",
                channel=self.window_title,
                sender="",
                content=line,
                timestamp=current_time,
                source_name=self.name,
            )
            messages.append(msg)

        return messages

    def poll(self) -> List[ChatMessage]:
        """拉取消息"""
        messages = []

        try:
            screenshot = self._capture_screenshot()
            if not screenshot:
                self._update_poll_status(False, "截图失败")
                return messages

            # 检查截图变化
            current_hash = self._calculate_image_hash(screenshot)
            if current_hash and current_hash == self._last_screenshot_hash:
                self._update_poll_status(True)
                return messages

            self._last_screenshot_hash = current_hash

            # OCR
            text = self._recognize_text(screenshot)
            if not text.strip():
                self._update_poll_status(True)
                return messages

            # 解析
            messages = self._parse_messages(text)
            messages = self._deduplicate_messages(messages)

            self._message_count += len(messages)
            self._update_poll_status(True)

            if messages:
                logger.debug(f"从 {self.name} 获取到 {len(messages)} 条消息")

        except Exception as e:
            logger.error(f"轮询失败: {e}")
            self._update_poll_status(False, str(e))

        return messages

    def is_available(self) -> bool:
        """检查可用性"""
        if not super().is_available():
            return False

        if self.window_element:
            try:
                _ = self.window_element.Name
                return True
            except:
                return self._find_window()

        return self._find_window()


def create_window_screen_source(
    name: str,
    app_type: str,
    title_contains: str = "",
    title_pattern: str = "",
    capture_region: Optional[Tuple[int, int, int, int]] = None,
    poll_interval: int = 5,
) -> WindowScreenSource:
    """工厂函数"""
    config = SourceConfig(
        name=name,
        platform=f"{app_type}_win",
        enabled=True,
        poll_interval=poll_interval,
    )

    window_config = WindowScreenConfig(
        app_type=app_type,
        title_contains=title_contains,
        title_pattern=title_pattern,
        capture_region=capture_region,
    )

    return WindowScreenSource(config, window_config)
