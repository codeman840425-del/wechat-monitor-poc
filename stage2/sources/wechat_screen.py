#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [AI-GENERATED] Date: 2026-02-03 | PromptHash: wechat-screen-source
# [CONTEXT] Task: 重构微信桌面 OCR 为 MessageSource 接口 | Issue: #refactor-source
# [REVIEWED] By: system | Date: 2026-02-03 | Status: VERIFIED
# [SAFETY] Checked: 无路径遍历风险(已验证路径), 已处理异常, 截图区域已验证
# [NOTE] 已知类型警告: window_element 可能为 None (Pylance), 运行时已做空值检查
"""
微信桌面版 OCR 消息源
封装现有的截图+OCR逻辑，实现 BaseMessageSource 接口
"""

import os
import sys
import time
import logging
from datetime import datetime
from typing import List, Optional, Tuple, Any
from dataclasses import dataclass

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uiautomation as auto
from PIL import Image, ImageGrab
import pytesseract

from sources.base import BaseMessageSource, SourceConfig
from core.message import ChatMessage

logger = logging.getLogger(__name__)


@dataclass
class WeChatScreenConfig:
    """微信桌面监控配置"""

    window_title_pattern: str = ""  # 窗口标题匹配模式
    capture_region: Optional[Tuple[int, int, int, int]] = (
        None  # 截图区域 (left, top, right, bottom)
    )
    use_relative_region: bool = True  # 是否使用相对坐标
    ocr_lang: str = "chi_sim+eng"  # OCR 语言
    ocr_config: str = "--oem 3 --psm 6"  # OCR 配置
    preprocess_scale: float = 2.0  # 预处理缩放比例
    message_separator: str = "\n"  # 消息分隔符


class WeChatScreenSource(BaseMessageSource):
    """
    微信桌面版 OCR 消息源

    通过截图+OCR的方式从微信桌面版获取消息
    """

    def __init__(self, config: SourceConfig, screen_config: WeChatScreenConfig):
        super().__init__(config)
        self.screen_config = screen_config
        self.window_element: Optional[Any] = None
        self.window_title: str = ""
        self._last_screenshot_hash: Optional[str] = None

        # 尝试查找窗口
        self._find_window()

    def _find_window(self) -> bool:
        """查找微信窗口"""
        try:
            desktop = auto.GetRootControl()

            for window in desktop.GetChildren():
                try:
                    class_name = window.ClassName or ""
                    window_name = window.Name or ""

                    # 检测微信窗口
                    is_wechat = False
                    if "WeChat" in class_name or "wechat" in class_name.lower():
                        is_wechat = True
                    elif "Qt" in class_name and (
                        "微信" in window_name or len(window_name) > 0
                    ):
                        is_wechat = True
                    elif "微信" in window_name and len(window_name) < 20:
                        is_wechat = True

                    # 如果指定了标题模式，进行匹配
                    if is_wechat and self.screen_config.window_title_pattern:
                        if self.screen_config.window_title_pattern not in window_name:
                            continue

                    if is_wechat:
                        self.window_element = window
                        self.window_title = window_name
                        logger.info(f"找到微信窗口: {window_name}")
                        return True

                except Exception as e:
                    continue

            logger.warning("未找到微信窗口")
            return False

        except Exception as e:
            logger.error(f"查找窗口失败: {e}")
            return False

    def _capture_screenshot(self) -> Optional[Image.Image]:
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
                time.sleep(0.3)
            except:
                pass

            # 获取窗口位置
            rect = self.window_element.BoundingRectangle
            win_left, win_top, win_right, win_bottom = (
                rect.left,
                rect.top,
                rect.right,
                rect.bottom,
            )
            win_width = win_right - win_left
            win_height = win_bottom - win_top

            # 使用配置的区域或整个窗口
            if self.screen_config.capture_region:
                if self.screen_config.use_relative_region:
                    # 相对坐标: (offset_x, offset_y, width, height)
                    r = self.screen_config.capture_region
                    offset_x, offset_y, region_width, region_height = (
                        r[0],
                        r[1],
                        r[2],
                        r[3],
                    )

                    # 计算绝对坐标
                    left = win_left + offset_x
                    top = win_top + offset_y
                    right = left + region_width
                    bottom = top + region_height

                    logger.debug(
                        f"相对区域计算: 窗口({win_left}, {win_top}, {win_right}, {win_bottom}), "
                        f"偏移({offset_x}, {offset_y}), 区域({region_width}x{region_height}), "
                        f"最终({left}, {top}, {right}, {bottom})"
                    )
                else:
                    # 绝对坐标: (left, top, right, bottom)
                    left, top, right, bottom = self.screen_config.capture_region
                    logger.debug(f"绝对区域: ({left}, {top}, {right}, {bottom})")
            else:
                # 使用整个窗口
                left, top, right, bottom = win_left, win_top, win_right, win_bottom
                logger.debug(f"使用整个窗口: ({left}, {top}, {right}, {bottom})")

            # 安全检查
            if right <= left or bottom <= top:
                logger.error(
                    f"截图区域无效: left={left}, top={top}, right={right}, bottom={bottom}"
                )
                logger.error(
                    f"窗口信息: left={win_left}, top={win_top}, right={win_right}, bottom={win_bottom}"
                )
                if self.screen_config.capture_region:
                    logger.error(f"配置区域: {self.screen_config.capture_region}")
                self._last_error = f"截图区域无效: right({right}) <= left({left}) 或 bottom({bottom}) <= top({top})"
                return None

            # 截图
            logger.info(f"截图区域: ({left}, {top}, {right}, {bottom})")
            screenshot = ImageGrab.grab(bbox=(left, top, right, bottom))
            return screenshot

        except Exception as e:
            logger.error(f"截图失败: {e}")
            self._last_error = f"截图失败: {e}"
            return None

    def _calculate_image_hash(self, image: Image.Image) -> str:
        """计算图像哈希用于去重"""
        try:
            small = image.convert("L").resize((16, 16), Image.Resampling.LANCZOS)
            pixels: List[int] = list(small.getdata())  # type: ignore
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
            logger.debug(f"计算图像哈希失败: {e}")
            return ""

    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """图像预处理"""
        # 缩放
        if self.screen_config.preprocess_scale > 1:
            width, height = image.size
            new_size = (
                int(width * self.screen_config.preprocess_scale),
                int(height * self.screen_config.preprocess_scale),
            )
            image = image.resize(new_size, Image.Resampling.LANCZOS)

        return image

    def _recognize_text(self, image: Image.Image) -> str:
        """OCR 识别文字"""
        try:
            # 预处理
            processed = self._preprocess_image(image)

            # OCR 识别
            text = pytesseract.image_to_string(
                processed,
                lang=self.screen_config.ocr_lang,
                config=self.screen_config.ocr_config,
            )

            return text
        except Exception as e:
            logger.error(f"OCR 识别失败: {e}")
            return ""

    def _parse_messages(self, text: str) -> List[ChatMessage]:
        """解析 OCR 文本为消息列表"""
        messages = []

        if not text.strip():
            return messages

        # 按行分割，过滤空行
        lines = [line.strip() for line in text.split("\n") if line.strip()]

        current_time = datetime.now()

        for i, line in enumerate(lines):
            # 生成消息 ID
            msg_id = self._generate_message_id(line, current_time, self.window_title)

            # 创建消息对象
            msg = ChatMessage(
                id=msg_id,
                platform="wechat_win",
                channel=self.window_title,
                sender="",  # OCR 无法识别发送者
                content=line,
                timestamp=current_time,
                source_name=self.name,
            )

            messages.append(msg)

        return messages

    def poll(self) -> List[ChatMessage]:
        """
        拉取新消息

        实现 BaseMessageSource 的抽象方法
        """
        messages = []

        try:
            # 截图
            screenshot = self._capture_screenshot()
            if not screenshot:
                self._update_poll_status(False, "截图失败")
                return messages

            # 检查截图是否变化（简单去重）
            current_hash = self._calculate_image_hash(screenshot)
            if current_hash and current_hash == self._last_screenshot_hash:
                # 截图未变化，跳过处理
                self._update_poll_status(True)
                return messages

            self._last_screenshot_hash = current_hash

            # OCR 识别
            text = self._recognize_text(screenshot)
            if not text.strip():
                self._update_poll_status(True)
                return messages

            # 解析消息
            messages = self._parse_messages(text)

            # 去重
            messages = self._deduplicate_messages(messages)

            # 更新统计
            self._message_count += len(messages)
            self._update_poll_status(True)

            if messages:
                logger.debug(f"从 {self.name} 获取到 {len(messages)} 条新消息")

        except Exception as e:
            logger.error(f"轮询消息源 {self.name} 失败: {e}")
            self._update_poll_status(False, str(e))

        return messages

    def is_available(self) -> bool:
        """检查消息源是否可用"""
        if not super().is_available():
            return False

        # 检查窗口是否仍然存在
        if self.window_element:
            try:
                # 尝试访问窗口属性
                _ = self.window_element.Name
                return True
            except:
                # 窗口可能已关闭，尝试重新查找
                return self._find_window()

        return self._find_window()


def create_wechat_screen_source(
    name: str = "微信桌面",
    window_title_pattern: str = "",
    capture_region: Optional[Tuple[int, int, int, int]] = None,
    poll_interval: int = 5,
) -> WeChatScreenSource:
    """
    创建微信桌面消息源的工厂函数

    Args:
        name: 消息源名称
        window_title_pattern: 窗口标题匹配模式
        capture_region: 截图区域
        poll_interval: 轮询间隔

    Returns:
        WeChatScreenSource 实例
    """
    config = SourceConfig(
        name=name,
        platform="wechat_win",
        enabled=True,
        poll_interval=poll_interval,
    )

    screen_config = WeChatScreenConfig(
        window_title_pattern=window_title_pattern,
        capture_region=capture_region,
    )

    return WeChatScreenSource(config, screen_config)
