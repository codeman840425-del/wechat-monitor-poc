#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
后台窗口截图模块
使用 Win32 API PrintWindow 实现后台窗口截图

功能：
1. 截取最小化或后台窗口的内容
2. 无需窗口可见即可截图
3. 支持窗口恢复和状态检查

作者：AI Assistant
日期：2026年
"""

import logging
from typing import Optional, Tuple
from dataclasses import dataclass

from PIL import Image

# Win32 API imports - 使用类型守卫模式
WIN32_AVAILABLE = False
try:
    import win32gui
    import win32ui
    import win32con
    from win32api import GetSystemMetrics
    import ctypes
    from ctypes import wintypes

    WIN32_AVAILABLE = True

    # 定义 Windows API 函数
    user32 = ctypes.windll.user32
    PW_CLIENTONLY = 0x00000001
    PW_RENDERFULLCONTENT = 0x00000002

    PrintWindow = user32.PrintWindow
    PrintWindow.argtypes = [wintypes.HWND, wintypes.HDC, wintypes.UINT]
    PrintWindow.restype = wintypes.BOOL

except ImportError:
    logging.warning("pywin32 未安装，后台截图功能不可用")


logger = logging.getLogger(__name__)


@dataclass
class WindowInfo:
    """窗口信息"""

    hwnd: int
    title: str
    rect: Tuple[int, int, int, int]  # left, top, right, bottom
    is_minimized: bool
    is_visible: bool


class BackgroundCapture:
    """
    后台窗口截图器

    使用 Win32 API PrintWindow 截取窗口内容，
    即使窗口被最小化或遮挡也能捕获。
    """

    def __init__(self, hwnd: int):
        """
        初始化后台截图器

        参数:
            hwnd: 窗口句柄 (Window Handle)
        """
        if not WIN32_AVAILABLE:
            raise RuntimeError("pywin32 未安装，无法使用后台截图功能")

        self.hwnd = hwnd
        self._last_screenshot: Optional[Image.Image] = None

    @classmethod
    def find_window(cls, title_pattern: str) -> Optional[int]:
        """
        根据标题查找窗口句柄

        参数:
            title_pattern: 窗口标题（部分匹配）

        返回:
            窗口句柄，如果未找到返回 None
        """
        if not WIN32_AVAILABLE:
            return None

        def callback(hwnd, extra):
            if win32gui.IsWindow(hwnd) and win32gui.IsWindowEnabled(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title_pattern in title:
                    extra.append(hwnd)
            return True

        handles = []
        win32gui.EnumWindows(callback, handles)

        if handles:
            logger.info(f"找到窗口 '{title_pattern}': {len(handles)} 个")
            return handles[0]  # 返回第一个匹配的窗口

        return None

    def get_window_info(self) -> Optional[WindowInfo]:
        """获取窗口信息"""
        if not win32gui.IsWindow(self.hwnd):
            return None

        try:
            title = win32gui.GetWindowText(self.hwnd)
            rect = win32gui.GetWindowRect(self.hwnd)
            is_minimized = win32gui.IsIconic(self.hwnd)
            is_visible = win32gui.IsWindowVisible(self.hwnd)

            return WindowInfo(
                hwnd=self.hwnd,
                title=title,
                rect=rect,
                is_minimized=is_minimized,
                is_visible=is_visible,
            )
        except Exception as e:
            logger.error(f"获取窗口信息失败: {e}")
            return None

    def is_minimized(self) -> bool:
        """检查窗口是否最小化"""
        try:
            return win32gui.IsIconic(self.hwnd)
        except:
            return False

    def restore_window(self) -> bool:
        """
        恢复最小化的窗口

        返回:
            是否成功恢复
        """
        try:
            if win32gui.IsIconic(self.hwnd):
                win32gui.ShowWindow(self.hwnd, win32con.SW_RESTORE)
                logger.info(f"恢复窗口: {win32gui.GetWindowText(self.hwnd)}")
                return True
            return True  # 窗口未最小化，也算成功
        except Exception as e:
            logger.error(f"恢复窗口失败: {e}")
            return False

    def capture(self, client_area_only: bool = True) -> Optional[Image.Image]:
        """
        截取窗口内容

        参数:
            client_area_only: 是否只截取客户区（排除标题栏和边框）

        返回:
            PIL Image 对象，失败返回 None
        """
        if not WIN32_AVAILABLE:
            logger.error("pywin32 未安装")
            return None

        try:
            # 获取窗口信息
            window_info = self.get_window_info()
            if not window_info:
                logger.error("窗口无效")
                return None

            logger.debug(
                f"截图窗口: {window_info.title}, 最小化: {window_info.is_minimized}"
            )

            # 获取窗口DC
            hwndDC = win32gui.GetWindowDC(self.hwnd)
            if not hwndDC:
                logger.error("无法获取窗口DC")
                return None

            try:
                # 创建内存DC
                mfcDC = win32ui.CreateDCFromHandle(hwndDC)
                saveDC = mfcDC.CreateCompatibleDC()

                # 获取窗口尺寸
                if client_area_only:
                    # 获取客户区尺寸
                    left, top, right, bottom = win32gui.GetClientRect(self.hwnd)
                    width = right - left
                    height = bottom - top
                else:
                    # 获取整个窗口尺寸
                    left, top, right, bottom = window_info.rect
                    width = right - left
                    height = bottom - top

                logger.debug(f"截图尺寸: {width}x{height}")

                # 创建位图
                saveBitMap = win32ui.CreateBitmap()
                saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
                saveDC.SelectObject(saveBitMap)

                # 使用 PrintWindow 截图
                # PW_RENDERFULLCONTENT = 2 (Windows 8+)
                result = PrintWindow(
                    self.hwnd, saveDC.GetSafeHdc(), PW_RENDERFULLCONTENT
                )

                if result == 0:
                    logger.warning("PrintWindow 返回 0，可能截图失败")

                # 获取位图信息
                bmpinfo = saveBitMap.GetInfo()
                bmpstr = saveBitMap.GetBitmapBits(True)

                # 转换为 PIL Image
                image = Image.frombuffer(
                    "RGB",
                    (bmpinfo["bmWidth"], bmpinfo["bmHeight"]),
                    bmpstr,
                    "raw",
                    "BGRX",
                    0,
                    1,
                )

                self._last_screenshot = image
                logger.info(f"后台截图成功: {image.size}")
                return image

            finally:
                # 清理资源
                try:
                    win32gui.DeleteObject(saveBitMap.GetHandle())
                except:
                    pass
                try:
                    saveDC.DeleteDC()
                except:
                    pass
                try:
                    mfcDC.DeleteDC()
                except:
                    pass
                win32gui.ReleaseDC(self.hwnd, hwndDC)

        except Exception as e:
            logger.error(f"后台截图失败: {e}", exc_info=True)
            return None

    def capture_with_fallback(
        self, foreground_capture_func=None
    ) -> Optional[Image.Image]:
        """
        带fallback的截图

        先尝试后台截图，如果失败则使用前台截图（如果提供）

        参数:
            foreground_capture_func: 前台截图函数（可选）

        返回:
            PIL Image 对象
        """
        # 尝试后台截图
        image = self.capture()
        if image:
            return image

        logger.warning("后台截图失败，尝试前台截图")

        # 恢复窗口
        if self.is_minimized():
            self.restore_window()

        # 使用前台截图（如果提供）
        if foreground_capture_func:
            try:
                return foreground_capture_func()
            except Exception as e:
                logger.error(f"前台截图也失败: {e}")

        return None


def test_background_capture():
    """测试后台截图功能"""
    import time

    print("=" * 60)
    print("后台截图功能测试")
    print("=" * 60)

    if not WIN32_AVAILABLE:
        print("错误: pywin32 未安装")
        print("请运行: pip install pywin32")
        return

    # 查找微信窗口
    print("\n1. 查找微信窗口...")
    hwnd = BackgroundCapture.find_window("微信")
    if not hwnd:
        hwnd = BackgroundCapture.find_window("WeChat")

    if not hwnd:
        print("未找到微信窗口，请确保微信已启动")
        return

    print(f"找到窗口，句柄: {hwnd}")

    # 创建截图器
    capture = BackgroundCapture(hwnd)

    # 获取窗口信息
    print("\n2. 窗口信息:")
    info = capture.get_window_info()
    if info:
        print(f"  标题: {info.title}")
        print(f"  位置: {info.rect}")
        print(f"  最小化: {info.is_minimized}")
        print(f"  可见: {info.is_visible}")

    # 测试截图
    print("\n3. 测试截图...")
    image = capture.capture(client_area_only=True)

    if image:
        print(f"  截图成功: {image.size}")

        # 保存截图
        filename = f"background_capture_test_{time.strftime('%H%M%S')}.png"
        image.save(filename)
        print(f"  已保存: {filename}")

        # 测试OCR
        print("\n4. 测试OCR识别...")
        try:
            import pytesseract

            text = pytesseract.image_to_string(image, lang="chi_sim+eng")
            print(f"  识别结果 ({len(text)} 字符):")
            print("  " + "-" * 40)
            preview = text[:200] if len(text) > 200 else text
            for line in preview.split("\n")[:5]:
                print(f"  {line}")
            if len(text) > 200 or len(preview.split("\n")) > 5:
                print("  ...")
            print("  " + "-" * 40)
        except Exception as e:
            print(f"  OCR测试失败: {e}")
    else:
        print("  截图失败")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    test_background_capture()
