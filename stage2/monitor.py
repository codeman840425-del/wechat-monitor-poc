#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信消息监控服务 - 阶段2：持续监控 + 数据存储
监控服务主模块

作者：AI Assistant
日期：2025年
"""

import os
import sys
import time
import logging
import shutil
from datetime import datetime
from typing import List, Optional, Set, Any, cast
from pathlib import Path

import yaml
import schedule

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager, MessageRecord

# 导入OCR相关库，如果失败则直接退出
import uiautomation as auto
from PIL import Image, ImageGrab
import pytesseract


class Config:
    """配置管理类"""

    def __init__(self, config_path: str = "config.yaml"):
        """加载配置文件"""
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

    def get(self, key: str, default=None):
        """获取配置项"""
        keys = key.split(".")
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value


class WeChatWindow:
    """微信窗口封装类"""

    def __init__(self, window_element):
        self.element = window_element
        self.name = window_element.Name
        self.handle = window_element.NativeWindowHandle

        # 获取窗口位置
        try:
            rect = window_element.BoundingRectangle
            self.left = rect.left
            self.top = rect.top
            self.right = rect.right
            self.bottom = rect.bottom
        except:
            self.left = self.top = self.right = self.bottom = 0

    def capture_screenshot(self) -> Optional[Any]:
        """截取窗口截图 - 修复DPI缩放问题"""
        try:
            # 将窗口置为前台
            try:
                self.element.SetFocus()
                time.sleep(0.5)  # 增加等待时间，确保窗口完全激活
            except:
                pass

            # 获取窗口实际位置和大小（处理DPI缩放）
            # 使用uiautomation的BoundingRectangle获取逻辑坐标
            try:
                rect = self.element.BoundingRectangle
                left, top, right, bottom = rect.left, rect.top, rect.right, rect.bottom
                width, height = right - left, bottom - top
            except Exception as e:
                logging.error(f"获取窗口位置失败: {e}")
                # 回退到保存的坐标
                left, top, right, bottom = self.left, self.top, self.right, self.bottom
                width, height = right - left, bottom - top

            logging.debug(
                f"窗口坐标: ({left}, {top}, {right}, {bottom}), 尺寸: {width}x{height}"
            )

            # 截图 - 使用屏幕坐标
            screenshot = ImageGrab.grab(bbox=(left, top, right, bottom))

            # 保存调试图
            if screenshot:
                screenshot.save("debug_before_crop.png")
                logging.debug(
                    f"原始截图已保存: debug_before_crop.png, 尺寸: {screenshot.size}"
                )

                # 获取截图的统计信息
                from PIL import ImageStat

                stat = ImageStat.Stat(screenshot)

                # 如果图像是纯色的（标准差很小），可能是黑屏或被遮挡
                if stat.stddev[0] < 10:
                    logging.warning("截图可能是纯色（窗口可能被遮挡或最小化）")

                # 检查图像尺寸是否与预期一致
                if screenshot.size != (width, height):
                    logging.warning(
                        f"截图尺寸异常: {screenshot.size}, 期望: {(width, height)}"
                    )

            return screenshot
        except Exception as e:
            logging.error(f"截图失败: {e}")
            return None


class KeywordFilter:
    """关键字过滤器 - 支持模糊匹配"""

    def __init__(
        self,
        keywords: List[str],
        match_mode: str = "contain",
        case_sensitive: bool = False,
        fuzzy_threshold: float = 0.7,
    ):
        """
        初始化关键字过滤器

        参数:
            keywords: 关键字列表
            match_mode: 匹配模式 ("contain", "exact", "fuzzy")
            case_sensitive: 是否区分大小写
            fuzzy_threshold: 模糊匹配阈值 (0-1)，越高要求越严格
        """
        self.keywords = keywords
        self.match_mode = match_mode
        self.case_sensitive = case_sensitive
        self.fuzzy_threshold = fuzzy_threshold

    def _fuzzy_match(self, text: str, keyword: str) -> float:
        """
        计算文本与关键字的模糊匹配度
        使用简单编辑距离算法
        """
        import difflib

        if not self.case_sensitive:
            text = text.lower()
            keyword = keyword.lower()

        # 使用 SequenceMatcher 计算相似度
        return difflib.SequenceMatcher(None, text, keyword).ratio()

    def _ocr_error_match(self, text: str, keyword: str) -> bool:
        """
        OCR 容错匹配：处理常见 OCR 错误
        例如："退款" 可能被识别为 "退欵" 或 "退 款"
        """
        if not self.case_sensitive:
            text = text.lower()
            keyword = keyword.lower()

        # 移除空格后匹配
        text_no_space = text.replace(" ", "").replace("\n", "")
        keyword_no_space = keyword.replace(" ", "").replace("\n", "")

        if keyword_no_space in text_no_space:
            return True

        # 常见 OCR 错误替换
        ocr_error_map = {
            "欵": "款",
            "吿": "告",
            "訴": "诉",
            "単": "单",
            "扴": "打",
            "収": "收",
            "発": "发",
            "貨": "货",
            "価": "价",
            "扱": "投",
            "訴": "诉",
        }

        # 替换可能的 OCR 错误字符后匹配
        corrected_text = text_no_space
        for error_char, correct_char in ocr_error_map.items():
            corrected_text = corrected_text.replace(error_char, correct_char)

        if keyword_no_space in corrected_text:
            return True

        return False

    def check(self, text: str) -> Optional[str]:
        """
        检查文本是否匹配关键字

        参数:
            text: 要检查的文本

        返回:
            匹配到的关键字，如果没有匹配返回 None
        """
        if not text:
            return None

        check_text = text if self.case_sensitive else text.lower()

        for keyword in self.keywords:
            check_keyword = keyword if self.case_sensitive else keyword.lower()

            if self.match_mode == "contain":
                if check_keyword in check_text:
                    return keyword
                # 额外检查 OCR 容错匹配
                if self._ocr_error_match(text, keyword):
                    return keyword
            elif self.match_mode == "exact":
                if check_keyword == check_text:
                    return keyword
            elif self.match_mode == "fuzzy":
                # 模糊匹配模式
                similarity = self._fuzzy_match(text, keyword)
                if similarity >= self.fuzzy_threshold:
                    return keyword
                # 同时检查包含关系
                if check_keyword in check_text:
                    return keyword

        return None


class RegionSelector:
    """区域选择器 - 使用鼠标框选截图区域"""

    def __init__(self):
        self.start_x = 0
        self.start_y = 0
        self.end_x = 0
        self.end_y = 0
        self.is_drawing = False
        self.selected_region: Optional[tuple[int, int, int, int]] = None

    def select_region(self) -> Optional[tuple[int, int, int, int]]:
        """引导用户通过鼠标框选截图区域"""
        try:
            import tkinter as tk
            from PIL import ImageTk

            # 获取屏幕截图
            print("正在捕获屏幕，请稍候...")
            screen = ImageGrab.grab()
            screen_width, screen_height = screen.size

            # 创建全屏窗口
            root = tk.Tk()
            root.title("选择监控区域 - 拖动鼠标框选聊天区域")
            root.geometry(f"{screen_width}x{screen_height}+0+0")
            root.attributes("-topmost", True)
            root.attributes("-fullscreen", True)
            root.configure(cursor="crosshair")

            # 转换PIL图像为Tkinter格式
            tk_image = ImageTk.PhotoImage(screen)

            # 创建画布
            canvas = tk.Canvas(root, highlightthickness=0)
            canvas.pack(fill=tk.BOTH, expand=True)
            canvas.create_image(0, 0, anchor=tk.NW, image=tk_image)

            # 创建提示文字
            hint_text = canvas.create_text(
                screen_width // 2,
                50,
                text="请拖动鼠标框选微信聊天区域，按 ESC 取消，按 Enter 确认",
                fill="red",
                font=("Arial", 20, "bold"),
                anchor=tk.CENTER,
            )

            # 矩形框
            rect_id = None

            def on_mouse_down(event):
                nonlocal rect_id, self
                self.start_x = event.x
                self.start_y = event.y
                self.is_drawing = True
                if rect_id:
                    canvas.delete(rect_id)
                rect_id = canvas.create_rectangle(
                    self.start_x,
                    self.start_y,
                    self.start_x,
                    self.start_y,
                    outline="red",
                    width=3,
                )

            def on_mouse_move(event):
                nonlocal rect_id
                if self.is_drawing and rect_id:
                    canvas.coords(rect_id, self.start_x, self.start_y, event.x, event.y)

            def on_mouse_up(event):
                self.is_drawing = False
                self.end_x = event.x
                self.end_y = event.y

            def on_key_press(event):
                if event.keysym == "Return":  # Enter键确认
                    if self.start_x != self.end_x and self.start_y != self.end_y:
                        left = min(self.start_x, self.end_x)
                        top = min(self.start_y, self.end_y)
                        right = max(self.start_x, self.end_x)
                        bottom = max(self.start_y, self.end_y)
                        self.selected_region = (left, top, right - left, bottom - top)
                    root.destroy()
                elif event.keysym == "Escape":  # ESC键取消
                    root.destroy()

            # 绑定事件
            canvas.bind("<Button-1>", on_mouse_down)
            canvas.bind("<B1-Motion>", on_mouse_move)
            canvas.bind("<ButtonRelease-1>", on_mouse_up)
            root.bind("<Key>", on_key_press)

            print("\n" + "=" * 60)
            print("区域选择模式")
            print("=" * 60)
            print("请在全屏窗口中拖动鼠标框选微信聊天区域")
            print("按 Enter 确认选择，按 ESC 取消")
            print("=" * 60 + "\n")

            root.mainloop()

            if self.selected_region is not None:
                left, top, width, height = self.selected_region
                print(
                    f"已选择区域: left={left}, top={top}, width={width}, height={height}"
                )
                return self.selected_region
            else:
                print("未选择区域，操作取消")
                return None

        except Exception as e:
            print(f"区域选择失败: {e}")
            return None


class WeChatMonitor:
    """微信监控服务主类"""

    def __init__(self, config_path: str = "config.yaml"):
        """初始化监控服务"""
        self.config = Config(config_path)
        self.db = None
        self.keyword_filter = None
        self.target_window: Optional[WeChatWindow] = None
        self.running = False
        self.capture_region: Optional[tuple[int, int, int, int]] = (
            None  # 截图区域 (left, top, width, height) - 绝对屏幕坐标
        )
        self.capture_region_offset: Optional[tuple[int, int, int, int]] = (
            None  # 相对窗口偏移 (x_offset, y_offset, width, height)
        )
        self.capture_region_reference_window: Optional[tuple[int, int, int, int]] = (
            None  # 选区时窗口位置 (left, top, right, bottom)
        )

        # 窗口重连相关
        self.window_check_interval = 30  # 每30秒检查一次窗口状态
        self.last_window_check = 0
        self.target_window_title = ""  # 保存目标窗口标题用于重连

        # 统计数据
        self.stats = {
            "total_scans": 0,
            "total_messages": 0,
            "matched_messages": 0,
            "start_time": None,
        }

        # 已处理的消息缓存（用于去重）
        self.processed_messages: Set[str] = set()

        # 上一次截图的哈希值（用于检测屏幕是否变化）
        self.last_screenshot_hash: Optional[str] = None
        self.screenshot_similarity_threshold: float = (
            0.95  # 相似度阈值，超过则认为没有变化
        )

        self._setup_logging()
        self._init_capture_region()  # 初始化截图区域
        self._init_components()

    def _init_capture_region(self):
        """初始化截图区域 - 支持强制重新选区和相对偏移"""
        # 检查是否总是重新选区（当前阶段默认开启）
        always_reselect = self.config.get("monitor.always_reselect_region", True)
        if always_reselect:
            self.logger.info("配置要求每次启动重新选区，启动区域选择...")
            self._perform_region_selection()
            return

        # 检查是否强制重新选区（一次性）
        force_reselect = self.config.get("monitor.force_reselect_region", False)
        if force_reselect:
            self.logger.info("配置强制重新选区，启动区域选择...")
            self._perform_region_selection()
            # 重置配置开关
            self._disable_force_reselect()
            return

        # 检查是否有相对偏移配置
        offset = self.config.get("monitor.capture_region_offset")
        reference = self.config.get("monitor.capture_region_reference")

        if offset and reference:
            # 使用相对偏移模式
            self.capture_region_offset = tuple(offset)
            self.capture_region_reference_window = tuple(reference)
            self.logger.info(
                f"使用相对窗口偏移: offset={self.capture_region_offset}, "
                f"reference={self.capture_region_reference_window}"
            )
            return

        # 检查配置中是否已有绝对截图区域
        region = self.config.get("monitor.capture_region")

        if region:
            # 使用已保存的区域（绝对坐标）
            self.capture_region = tuple(region)
            self.logger.info(f"使用已保存的绝对截图区域: {self.capture_region}")
            self.logger.warning(
                "注意：使用的是绝对屏幕坐标，移动窗口后可能需要重新选区"
            )
        else:
            # 引导用户选择区域
            self.logger.info("未配置截图区域，启动区域选择...")
            self._perform_region_selection()

    def _perform_region_selection(self):
        """执行区域选择流程"""
        # 确保有目标窗口才能计算相对偏移
        if self.target_window is None:
            self.logger.warning("未找到目标窗口，无法计算相对偏移，将使用绝对坐标")

        selector = RegionSelector()
        selected = selector.select_region()

        if selected:
            self._save_region_with_offset(selected)
        else:
            self.logger.warning("未选择截图区域，将使用窗口截图模式")

    def _save_region_with_offset(self, region: tuple):
        """
        保存截图区域，同时计算和保存相对窗口偏移

        参数:
            region: 选定的屏幕区域 (left, top, width, height)
        """
        abs_left, abs_top, width, height = region

        if self.target_window is not None:
            try:
                # 获取当前窗口位置
                rect = self.target_window.element.BoundingRectangle
                win_left, win_top = rect.left, rect.top

                # 计算相对偏移
                x_offset = abs_left - win_left
                y_offset = abs_top - win_top

                # 保存相对偏移配置
                self.capture_region_offset = (x_offset, y_offset, width, height)
                self.capture_region_reference_window = (
                    rect.left,
                    rect.top,
                    rect.right,
                    rect.bottom,
                )

                self._save_capture_region_config(
                    offset=self.capture_region_offset,
                    reference=self.capture_region_reference_window,
                )

                self.logger.info(
                    f"已保存相对窗口偏移: offset=({x_offset}, {y_offset}, {width}, {height}), "
                    f"窗口位置=({win_left}, {win_top})"
                )

            except Exception as e:
                self.logger.warning(f"计算相对偏移失败，使用绝对坐标: {e}")
                self.capture_region = region
                self._save_capture_region_config(absolute=region)
        else:
            # 没有目标窗口，使用绝对坐标
            self.capture_region = region
            self._save_capture_region_config(absolute=region)
            self.logger.info(f"已保存绝对截图区域: {region}")

    def _save_capture_region_config(
        self,
        offset: Optional[tuple] = None,
        reference: Optional[tuple] = None,
        absolute: Optional[tuple] = None,
    ):
        """
        保存截图区域配置到配置文件

        参数:
            offset: 相对窗口偏移 (x_offset, y_offset, width, height)
            reference: 选区时窗口位置 (left, top, right, bottom)
            absolute: 绝对屏幕坐标 (left, top, width, height)
        """
        try:
            config_path = "config.yaml"
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            if config is None:
                config = {}

            if "monitor" not in config:
                config["monitor"] = {}

            # 保存相对偏移（优先）
            if offset:
                config["monitor"]["capture_region_offset"] = list(offset)
            if reference:
                config["monitor"]["capture_region_reference"] = list(reference)

            # 同时保存绝对坐标（兼容旧版本）
            if absolute:
                config["monitor"]["capture_region"] = list(absolute)

            # 添加注释说明
            config["monitor"]["_capture_region_note"] = (
                "capture_region_offset 是相对于目标窗口左上角的偏移量"
            )

            with open(config_path, "w", encoding="utf-8") as f:
                yaml.dump(config, f, allow_unicode=True, default_flow_style=False)

            self.logger.info(f"截图区域配置已保存到 {config_path}")

        except Exception as e:
            self.logger.error(f"保存截图区域配置失败: {e}")

    def _disable_force_reselect(self):
        """禁用强制重新选区开关"""
        try:
            config_path = "config.yaml"
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            if config and "monitor" in config:
                config["monitor"]["force_reselect_region"] = False

                with open(config_path, "w", encoding="utf-8") as f:
                    yaml.dump(config, f, allow_unicode=True, default_flow_style=False)

        except Exception as e:
            self.logger.debug(f"重置强制选区开关失败: {e}")

    def _calculate_capture_bbox(self) -> Optional[tuple[int, int, int, int]]:
        """
        计算实际截图的bbox
        如果有相对偏移，根据当前窗口位置计算；否则使用绝对坐标

        返回:
            (left, top, right, bottom) 或 None（如果计算失败）
        """
        # 优先使用相对偏移
        if self.capture_region_offset is not None and self.target_window is not None:
            try:
                # 获取当前窗口位置
                rect = self.target_window.element.BoundingRectangle
                win_left, win_top = rect.left, rect.top

                x_offset, y_offset, width, height = self.capture_region_offset

                # 计算实际截图坐标
                abs_left = win_left + x_offset
                abs_top = win_top + y_offset
                abs_right = abs_left + width
                abs_bottom = abs_top + height

                self.logger.debug(
                    f"使用相对偏移计算bbox: "
                    f"窗口=({win_left}, {win_top}), "
                    f"偏移=({x_offset}, {y_offset}), "
                    f"bbox=({abs_left}, {abs_top}, {abs_right}, {abs_bottom})"
                )

                return (abs_left, abs_top, abs_right, abs_bottom)

            except Exception as e:
                self.logger.warning(f"计算相对偏移bbox失败: {e}，尝试使用绝对坐标")

        # 使用绝对坐标
        if self.capture_region is not None:
            left, top, width, height = self.capture_region
            return (left, top, left + width, top + height)

        return None

    def _save_capture_region(self, region: tuple):
        """保存截图区域到配置文件"""
        try:
            config_path = "config.yaml"
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            if config is None:
                config = {}

            if "monitor" not in config:
                config["monitor"] = {}

            config["monitor"]["capture_region"] = list(region)

            with open(config_path, "w", encoding="utf-8") as f:
                yaml.dump(config, f, allow_unicode=True, default_flow_style=False)

            print(f"截图区域已保存到 {config_path}")
        except Exception as e:
            print(f"保存截图区域失败: {e}")

    def _validate_capture_region(self) -> bool:
        """
        验证截图区域是否有效
        检查区域是否在当前屏幕范围内
        """
        if self.capture_region is None:
            return False

        try:
            left, top, width, height = self.capture_region
            right = left + width
            bottom = top + height

            # 获取屏幕尺寸
            screen = ImageGrab.grab()
            screen_width, screen_height = screen.size

            # 检查区域是否在屏幕范围内
            if left < 0 or top < 0 or right > screen_width or bottom > screen_height:
                self.logger.warning(
                    f"截图区域超出屏幕范围: "
                    f"区域=({left}, {top}, {right}, {bottom}), "
                    f"屏幕=({screen_width}, {screen_height})"
                )
                return False

            # 检查区域大小是否合理
            if width < 100 or height < 100:
                self.logger.warning(f"截图区域过小: {width}x{height}, 最小要求100x100")
                return False

            return True

        except Exception as e:
            self.logger.error(f"验证截图区域时出错: {e}")
            return False

    def _check_window_valid(self) -> bool:
        """
        检查目标窗口是否仍然有效
        返回True表示窗口有效，False表示需要重新查找
        """
        if self.target_window is None:
            return False

        try:
            # 尝试获取窗口元素，如果失败说明窗口已关闭
            rect = self.target_window.element.BoundingRectangle
            if rect is None:
                return False

            # 检查窗口标题是否匹配（防止窗口被替换）
            # 如果 target_window_title 为空，跳过标题检查（首次选择时）
            if self.target_window_title:
                current_name = self.target_window.element.Name
                if current_name != self.target_window_title:
                    self.logger.warning(
                        f"窗口标题已改变: {self.target_window_title} -> {current_name}"
                    )
                    return False

            return True

        except Exception as e:
            self.logger.debug(f"窗口检查失败: {e}")
            return False

    def _try_reconnect_window(self) -> bool:
        """
        尝试重新查找并连接目标窗口
        返回True表示重连成功
        """
        self.logger.info("尝试重新查找目标窗口...")

        try:
            if self.find_target_window():
                self.logger.info("窗口重连成功")
                return True
            else:
                self.logger.warning("未找到目标窗口，将在下次扫描时重试")
                return False
        except Exception as e:
            self.logger.error(f"窗口重连失败: {e}")
            return False

    def _setup_logging(self):
        """配置日志"""
        log_level = self.config.get("logging.level", "INFO")
        log_file = self.config.get("logging.log_file", "./monitor.log")
        console_output = self.config.get("logging.console_output", True)

        # 创建日志目录
        log_dir = os.path.dirname(log_file) if log_file else ""
        if log_dir and not os.path.exists(str(log_dir)):
            os.makedirs(str(log_dir))

        # 配置日志 - 使用 List[logging.Handler] 类型
        handlers: List[logging.Handler] = []
        if log_file:
            handlers.append(logging.FileHandler(str(log_file), encoding="utf-8"))
        if console_output:
            handlers.append(logging.StreamHandler())

        # 确保 log_level 不为 None
        level_str = log_level if log_level else "INFO"
        logging.basicConfig(
            level=getattr(logging, str(level_str).upper()),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=handlers,
        )

        self.logger = logging.getLogger(__name__)

    def _init_components(self):
        """初始化组件"""
        # 初始化数据库
        db_path = self.config.get("database.db_path", "./wechat_monitor.db")
        if db_path is None:
            db_path = "./wechat_monitor.db"
        self.db = DatabaseManager(str(db_path))

        # 初始化关键字过滤器（优先从数据库读取，否则使用配置文件）
        db_keywords = self.db.get_keywords_from_db(enabled_only=True)
        if db_keywords:
            keywords = db_keywords
            self.logger.info("从数据库加载关键字")
        else:
            keywords = self.config.get("keywords.list", [])
            if keywords is None:
                keywords = []
            self.logger.info("从配置文件加载关键字")

        match_mode = self.config.get("keywords.match_mode", "contain")
        if match_mode is None:
            match_mode = "contain"
        case_sensitive = self.config.get("keywords.case_sensitive", False)
        if case_sensitive is None:
            case_sensitive = False
        self.keyword_filter = KeywordFilter(
            keywords, str(match_mode), bool(case_sensitive)
        )

        # 更新监控状态为运行中
        self.db.update_monitor_status("running", pid=os.getpid())

        self.logger.info("组件初始化完成")
        self.logger.info(f"监控关键字: {keywords}")

    def find_target_window(self) -> bool:
        """
        查找目标微信窗口

        返回:
            是否找到窗口
        """
        target_title = self.config.get("monitor.target_window_title", "")

        desktop = auto.GetRootControl()
        candidates = []

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

                if is_wechat:
                    candidates.append(WeChatWindow(window))

            except:
                continue

        if not candidates:
            self.logger.error("未找到任何微信窗口")
            return False

        # 如果指定了目标标题，尝试匹配
        if target_title:
            for window in candidates:
                if target_title in window.name:
                    self.target_window = window
                    self.logger.info(f"找到目标窗口: {window.name}")
                    return True
            self.logger.warning(f"未找到标题包含 '{target_title}' 的窗口")

        # 如果只有一个候选窗口，直接使用
        if len(candidates) == 1:
            selected_window = candidates[0]
            self.target_window = selected_window
            self.logger.info(f"使用唯一窗口: {selected_window.name}")
            return True

        # 多个窗口，列出让用户选择
        print("\n找到多个微信窗口：")
        for i, window in enumerate(candidates, 1):
            print(f"  [{i}] {window.name}")

        while True:
            try:
                choice = input(f"\n请选择窗口编号 (1-{len(candidates)}): ").strip()
                index = int(choice) - 1
                if 0 <= index < len(candidates):
                    selected_window = candidates[index]
                    self.target_window = selected_window
                    self.target_window_title = (
                        selected_window.name
                    )  # 保存窗口标题用于后续检查
                    self.logger.info(f"选择窗口: {selected_window.name}")
                    return True
            except:
                pass
            print("请输入有效的编号")

    def _ensure_components_initialized(self):
        """确保所有组件已初始化"""
        assert self.target_window is not None, "目标窗口未初始化"
        assert self.db is not None, "数据库未初始化"
        assert self.keyword_filter is not None, "关键字过滤器未初始化"

    def _calculate_image_hash(self, image: Any) -> str:
        """
        计算图像的感知哈希值
        用于快速比对两张截图是否相似
        """
        try:
            from PIL import Image

            # 缩放到小尺寸并转为灰度图
            small = image.convert("L").resize((16, 16), Image.Resampling.LANCZOS)
            pixels = list(small.getdata())
            avg = sum(pixels) / len(pixels)

            # 计算差异哈希
            diff = []
            for i in range(16):
                for j in range(15):
                    left_pixel = pixels[i * 16 + j]
                    right_pixel = pixels[i * 16 + j + 1]
                    diff.append(left_pixel > right_pixel)

            # 转换为十六进制字符串
            decimal_value = sum(bit << i for i, bit in enumerate(diff))
            return hex(decimal_value)[2:].zfill(16)
        except Exception as e:
            self.logger.debug(f"计算图像哈希失败: {e}")
            return ""

    def _is_screenshot_changed(self, screenshot: Any) -> bool:
        """
        检查截图是否与上一次有显著变化

        返回:
            True - 截图有变化，需要处理
            False - 截图无变化，可以跳过
        """
        current_hash = self._calculate_image_hash(screenshot)

        if not current_hash:
            return True  # 哈希计算失败，默认处理

        if self.last_screenshot_hash is None:
            # 第一次截图
            self.last_screenshot_hash = current_hash
            self.logger.debug(f"首次截图，哈希值: {current_hash}")
            return True

        # 计算哈希相似度
        if current_hash == self.last_screenshot_hash:
            self.logger.debug("截图与上次完全相同，跳过处理")
            return False

        # 更新哈希值
        self.last_screenshot_hash = current_hash
        self.logger.debug(f"截图有变化，新哈希值: {current_hash}")
        return True

    def extract_chat_area(self, screenshot: Any) -> Any:
        """提取聊天区域 - 优化版本"""
        width, height = screenshot.size

        # 微信PC版布局分析（根据常见分辨率优化）
        # 左侧联系人列表约占 25-30%
        # 顶部标题栏约占 8-10%
        # 底部输入框约占 12-15%
        # 右侧滚动条约占 2-3%

        # 更精确的裁剪参数 - 适配不同窗口大小
        left_crop = 0.28  # 左侧裁剪28%，排除联系人列表
        top_crop = 0.09  # 顶部裁剪9%，排除标题栏
        right_crop = 0.03  # 右侧裁剪3%，排除滚动条
        bottom_crop = 0.14  # 底部裁剪14%，排除输入框

        left = int(width * left_crop)
        top = int(height * top_crop)
        right = int(width * (1 - right_crop))
        bottom = int(height * (1 - bottom_crop))

        chat_area = screenshot.crop((left, top, right, bottom))

        # 详细日志
        self.logger.info(f"聊天区域裁剪参数:")
        self.logger.info(f"  原始尺寸: {width}x{height}")
        self.logger.info(
            f"  裁剪比例: 左{left_crop * 100:.0f}% 上{top_crop * 100:.0f}% 右{right_crop * 100:.0f}% 下{bottom_crop * 100:.0f}%"
        )
        self.logger.info(f"  裁剪坐标: ({left}, {top}, {right}, {bottom})")
        self.logger.info(f"  裁剪后尺寸: {chat_area.size}")

        # 保存调试图
        chat_area.save("debug_after_crop.png")
        self.logger.info(f"裁剪后截图已保存: debug_after_crop.png")

        return chat_area

    def recognize_text(self, image: Any) -> str:
        """OCR识别文字 - 使用可配置预处理"""
        try:
            # OCR识别 - 使用 chi_sim+eng 避免中文被误判
            lang = "chi_sim+eng"
            config = "--oem 3 --psm 6"
            self.logger.debug(f"OCR参数: lang={lang}, config={config}")

            # 使用可配置的预处理
            img = self.preprocess_image(image)

            # 保存预处理后的图像（用于调试）
            debug_path = f"./debug_ocr_{datetime.now().strftime('%H%M%S')}.png"
            img.save(debug_path)
            self.logger.debug(f"预处理后图像已保存: {debug_path}")

            # 保存原始图像用于对比
            img.save(f"./debug_ocr_input_{datetime.now().strftime('%H%M%S')}.png")

            text = pytesseract.image_to_string(img, lang=lang, config=config)

            self.logger.info(f"OCR完成，识别到 {len(text)} 个字符")
            if text.strip():
                self.logger.info(f"OCR文本预览: {text[:200]}...")
            else:
                self.logger.warning("OCR未识别到任何文字")
            return text

        except Exception as e:
            self.logger.error(f"OCR识别失败: {e}", exc_info=True)
            return ""

    def save_screenshot(self, screenshot: Any, filename: str) -> str:
        """保存截图"""
        save_dir = self.config.get("monitor.screenshot.save_directory", "./screenshots")
        if save_dir is None:
            save_dir = "./screenshots"

        save_dir_str = str(save_dir)
        if not os.path.exists(save_dir_str):
            os.makedirs(save_dir_str)

        filepath = os.path.join(save_dir_str, filename)
        screenshot.save(filepath)
        return filepath

    def preprocess_image(self, image: Any) -> Any:
        """
        OCR前图像预处理 - 可配置，保守策略优先保证识别率
        """
        try:
            # 检查预处理是否启用（默认关闭，避免过度处理）
            if not self.config.get("ocr.preprocess.enabled", False):
                self.logger.debug("预处理: 已禁用，使用原图")
                return image

            from PIL import ImageEnhance, ImageFilter, ImageStat

            # 获取原始图像信息
            orig_size = image.size
            self.logger.debug(f"预处理: 原始图像尺寸={orig_size}")

            # 1. 转为灰度图（必须步骤）
            img = image.convert("L")
            self.logger.debug("预处理: 已转换为灰度图")

            # 2. 可选：轻度锐化（默认关闭）
            sharpen_enabled = self.config.get("ocr.preprocess.sharpen", False)
            if sharpen_enabled:
                img = img.filter(ImageFilter.SHARPEN)
                self.logger.debug("预处理: 锐化已应用")

            # 3. 可选：对比度调整（默认关闭，使用保守参数）
            contrast_enabled = self.config.get("ocr.preprocess.contrast", False)
            if contrast_enabled:
                contrast_factor_raw = self.config.get(
                    "ocr.preprocess.contrast_factor", 1.2
                )
                contrast_factor: float = (
                    1.2 if contrast_factor_raw is None else float(contrast_factor_raw)
                )
                # 限制对比度范围，避免过度增强
                contrast_factor = max(0.8, min(2.0, contrast_factor))

                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(contrast_factor)
                self.logger.debug(f"预处理: 对比度调整完成 (factor={contrast_factor})")

            # 4. 可选：放大图像（提升小字识别率，默认1.5倍）
            scale = self.config.get("ocr.preprocess.scale", 1.5)
            if scale and scale > 1.0:
                new_size = (int(img.width * scale), int(img.height * scale))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
                self.logger.debug(f"预处理: 图像已放大到 {new_size} (scale={scale})")

            # 输出处理后图像信息
            stat = ImageStat.Stat(img)
            self.logger.debug(
                f"预处理: 完成 - 尺寸={img.size}, 平均亮度={stat.mean[0]:.1f}, "
                f"标准差={stat.stddev[0]:.1f}"
            )

            return img

        except Exception as e:
            self.logger.warning(f"图像预处理失败，使用原图: {e}")
            return image

    def clean_ocr_text(self, text: str) -> str:
        """
        清洗OCR结果
        去除无意义的全标点行、极短行
        """
        lines = text.split("\n")
        cleaned_lines = []

        for line in lines:
            line = line.strip()

            # 跳过空行
            if not line:
                continue

            # 跳过极短行（长度 < 2）
            if len(line) < 2:
                continue

            # 跳过全标点行（使用Python支持的标点符号范围）
            import re

            # 匹配全标点符号行：包括中英文标点、空格、换行等
            # 不使用 \p{P}，因为Python re模块不支持Unicode属性
            punctuation_pattern = r"^[\s\u0000-\u002F\u003A-\u0040\u005B-\u0060\u007B-\u007E\u2000-\u206F\u3000-\u303F\uFF00-\uFFEF]+$"
            if re.match(punctuation_pattern, line):
                continue

            cleaned_lines.append(line)

        return "\n".join(cleaned_lines)

    def process_messages(self, text: str) -> List[str]:
        """处理OCR文本，提取消息"""
        # 清洗OCR结果
        cleaned_text = self.clean_ocr_text(text)

        # 简单的消息分割（根据换行）
        lines = cleaned_text.split("\n")
        messages = []

        for line in lines:
            line = line.strip()
            # 过滤空行和太短的行
            if len(line) >= 3:
                messages.append(line)

        return messages

    def scan_once(self):
        """执行一次扫描 - 带完整异常处理"""
        assert self.target_window is not None
        assert self.db is not None
        assert self.keyword_filter is not None

        self.stats["total_scans"] += 1
        scan_start_time = datetime.now()
        self.logger.debug(f"开始第 {self.stats['total_scans']} 次扫描")

        try:
            # 阶段1: 窗口状态检查
            current_time = time.time()
            if current_time - self.last_window_check > self.window_check_interval:
                if not self._check_window_valid():
                    self.logger.warning("目标窗口已失效，尝试重新连接...")
                    if not self._try_reconnect_window():
                        self.logger.error("窗口重连失败，跳过本次扫描")
                        return
                self.last_window_check = current_time

            # 阶段2: 截图区域验证
            if self.capture_region is not None:
                if not self._validate_capture_region():
                    self.logger.warning("截图区域无效，跳过本次扫描")
                    return

            # 阶段3: 截图
            self.logger.debug("正在截图...")
            screenshot = None
            chat_area = None

            try:
                # 计算截图bbox（支持相对偏移）
                bbox = self._calculate_capture_bbox()

                if bbox is not None:
                    left, top, right, bottom = bbox
                    width = right - left
                    height = bottom - top

                    # 验证bbox不超出屏幕
                    screen = ImageGrab.grab()
                    if (
                        left < 0
                        or top < 0
                        or right > screen.width
                        or bottom > screen.height
                    ):
                        self.logger.warning(
                            f"[截图阶段] 计算出的bbox超出屏幕范围: "
                            f"({left}, {top}, {right}, {bottom}), "
                            f"屏幕=({screen.width}, {screen.height})"
                        )
                        return

                    screenshot = ImageGrab.grab(bbox=bbox)

                    # 保存原始截图用于调试
                    raw_path = f"./debug_raw_{datetime.now().strftime('%H%M%S')}.png"
                    screenshot.save(raw_path)
                    self.logger.info(
                        f"原始截图已保存: {raw_path}, 尺寸={screenshot.size}"
                    )

                    # 检查截图是否与上次相同
                    if not self._is_screenshot_changed(screenshot):
                        self.logger.info("截图与上次相同，跳过本次处理")
                        return

                    self.logger.info(
                        f"使用配置区域截图: "
                        f"窗口=({self.target_window.element.BoundingRectangle.left}, "
                        f"{self.target_window.element.BoundingRectangle.top}), "
                        f"偏移=({self.capture_region_offset[0] if self.capture_region_offset else 'N/A'}, "
                        f"{self.capture_region_offset[1] if self.capture_region_offset else 'N/A'}), "
                        f"bbox=({left}, {top}, {width}, {height})"
                    )
                    chat_area = screenshot
                else:
                    # 没有配置区域，使用窗口截图
                    screenshot = self.target_window.capture_screenshot()
                    if not screenshot:
                        self.logger.warning("[截图阶段] 截图失败，跳过本次扫描")
                        return
                    self.logger.debug(f"截图成功，尺寸: {screenshot.size}")
                    chat_area = self.extract_chat_area(screenshot)
            except Exception as e:
                self.logger.error(f"[截图阶段] 截图失败: {type(e).__name__}: {e}")
                return

            # 阶段4: OCR识别
            try:
                self.logger.debug("正在进行OCR识别...")
                text = self.recognize_text(chat_area)
                if not text.strip():
                    self.logger.debug("[OCR阶段] 未识别到文字")
                    return
                self.logger.debug(f"OCR识别完成，文本长度: {len(text)}")
            except Exception as e:
                self.logger.error(f"[OCR阶段] OCR失败: {type(e).__name__}: {e}")
                return

            # 阶段5: 处理消息
            try:
                messages = self.process_messages(text)
                self.stats["total_messages"] += len(messages)
                self.logger.info(f"识别到 {len(messages)} 条消息")
            except Exception as e:
                self.logger.error(f"[消息处理阶段] 处理失败: {type(e).__name__}: {e}")
                return

            # 检查关键字
            for msg in messages:
                matched_keyword = self.keyword_filter.check(msg)

                # 打印每条消息的匹配结果
                self.logger.debug(
                    f'检查消息: "{msg[:80]}..." -> 匹配结果: {matched_keyword if matched_keyword else "未命中"}'
                )

                # 无论是否匹配，都记录到数据库（用于调试）
                # 实际匹配的消息标记为匹配，未匹配的标记为 "(未匹配)"
                keyword_to_save = matched_keyword if matched_keyword else "(未匹配)"

                # 去重检查
                msg_hash = f"{self.target_window.name}:{msg}"
                if msg_hash in self.processed_messages:
                    self.logger.debug(f"消息已存在，跳过: {msg[:50]}...")
                    continue

                self.processed_messages.add(msg_hash)

                # 保存截图（仅匹配的消息保存截图）
                screenshot_path = None
                if matched_keyword:
                    save_screenshots = self.config.get(
                        "monitor.screenshot.save_screenshots", True
                    )
                    if save_screenshots:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"{timestamp}_{matched_keyword}.png"
                        screenshot_path = self.save_screenshot(screenshot, filename)

                # 保存到数据库
                try:
                    record = MessageRecord(
                        id=None,
                        window_title=self.target_window.name,
                        window_handle=self.target_window.handle,
                        message_text=msg,
                        matched_keyword=keyword_to_save,
                        screenshot_path=screenshot_path,
                        created_at=datetime.now(),
                    )

                    record_id = self.db.insert_message(record)

                    if matched_keyword:
                        self.stats["matched_messages"] += 1
                        self.logger.info(
                            f"✓ 匹配到关键字 '{matched_keyword}': {msg[:50]}..."
                        )

                    self.logger.info(
                        f"  已写入数据库，ID: {record_id}, 关键字标记: {keyword_to_save}"
                    )

                except Exception as e:
                    self.logger.error(f"写入数据库失败: {e}", exc_info=True)

            # 清理旧截图
            self._cleanup_old_screenshots()

        except Exception as e:
            scan_duration = (datetime.now() - scan_start_time).total_seconds()
            self.logger.error(
                f"[扫描失败] 阶段未知, 耗时{scan_duration:.2f}s, 错误: {type(e).__name__}: {e}",
                exc_info=True,
            )

    def _cleanup_old_screenshots(self):
        """清理过期截图"""
        retention_days = self.config.get("monitor.screenshot.retention_days", 7)
        if retention_days is None:
            retention_days = 7

        if retention_days <= 0:
            return

        try:
            save_dir = self.config.get(
                "monitor.screenshot.save_directory", "./screenshots"
            )
            if save_dir is None:
                return
            save_dir_str = str(save_dir)
            if not os.path.exists(save_dir_str):
                return

            cutoff = datetime.now().timestamp() - (int(retention_days) * 86400)

            for filename in os.listdir(save_dir_str):
                filepath = os.path.join(save_dir_str, filename)
                if os.path.getmtime(filepath) < cutoff:
                    os.remove(filepath)

        except Exception as e:
            self.logger.warning(f"清理旧截图失败: {e}")

    def print_statistics(self):
        """打印统计信息"""
        assert self.db is not None
        stats = self.db.get_statistics()

        print("\n" + "=" * 60)
        print("监控统计")
        print("=" * 60)
        print(f"运行时间: {self.stats['start_time']}")
        print(f"扫描次数: {self.stats['total_scans']}")
        print(f"识别消息: {self.stats['total_messages']}")
        print(f"匹配消息: {self.stats['matched_messages']}")
        print(f"数据库总数: {stats['total_messages']}")
        print(f"今日消息: {stats['today_messages']}")
        print("\n关键字分布:")
        for keyword, count in stats["keyword_distribution"].items():
            print(f"  {keyword}: {count}")
        print("=" * 60)

    def run(self):
        """运行监控服务"""
        # 查找目标窗口
        if not self.find_target_window():
            self.logger.error("无法找到目标窗口，服务退出")
            return

        assert self.target_window is not None

        self.running = True
        self.stats["start_time"] = datetime.now()

        # 获取监控间隔
        interval = self.config.get("monitor.interval", 5)
        if interval is None:
            interval = 5

        self.logger.info("=" * 60)
        self.logger.info("微信消息监控服务启动")
        self.logger.info("=" * 60)
        self.logger.info(f"目标窗口: {self.target_window.name}")
        self.logger.info(f"监控间隔: {interval}秒")
        self.logger.info("=" * 60)
        self.logger.info("按 Ctrl+C 停止服务")

        # 设置定时任务
        schedule.every(int(interval)).seconds.do(self.scan_once)

        try:
            heartbeat_counter = 0
            while self.running:
                schedule.run_pending()
                time.sleep(0.1)

                # 每30秒发送一次心跳
                heartbeat_counter += 1
                if heartbeat_counter >= 300:  # 300 * 0.1s = 30s
                    if self.db is not None:
                        self.db.heartbeat()
                    heartbeat_counter = 0
        except KeyboardInterrupt:
            self.logger.info("\n收到停止信号，正在关闭...")
        finally:
            self.stop()

    def stop(self):
        """停止监控服务"""
        self.running = False

        # 更新监控状态为已停止
        if self.db:
            self.db.update_monitor_status("stopped")

        # 打印统计
        self.print_statistics()

        # 关闭数据库
        assert self.db is not None
        self.db.close()

        self.logger.info("监控服务已停止")


def main():
    """主函数"""
    # 检查配置文件
    config_path = "config.yaml"
    if not os.path.exists(config_path):
        print(f"错误：找不到配置文件 {config_path}")
        print("请确保 config.yaml 存在于当前目录")
        return

    # 创建并运行监控服务
    monitor = WeChatMonitor(config_path)
    monitor.run()


if __name__ == "__main__":
    main()
