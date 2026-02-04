#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信消息监控 PoC - 阶段1：技术验证（截图+OCR方案）
基于屏幕截图和OCR技术实现，适用于Qt框架微信（PC 4.0+）

功能：
1. 枚举当前系统中运行的桌面微信窗口
2. 截取微信聊天区域
3. 使用OCR识别消息文本
4. 在终端里打印出来

作者：AI Assistant
日期：2025年
"""

import sys
import time
from typing import List, Optional, Tuple

# 尝试导入 UI Automation 库
try:
    import uiautomation as auto
except ImportError:
    print("错误：未安装 uiautomation 库")
    print("请运行: pip install uiautomation")
    sys.exit(1)

# 尝试导入图像处理库
try:
    from PIL import Image, ImageGrab
except ImportError:
    print("错误：未安装 Pillow 库")
    print("请运行: pip install Pillow")
    sys.exit(1)

# 尝试导入 OCR 库
try:
    import pytesseract
except ImportError:
    print("错误：未安装 pytesseract 库")
    print("请运行: pip install pytesseract")
    print("注意：还需要安装 Tesseract-OCR 引擎")
    print("下载地址：https://github.com/UB-Mannheim/tesseract/wiki")
    sys.exit(1)

# 在这里配置 Tesseract 可执行文件路径（你已经安装在这个位置）
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


class WeChatWindow:
    """微信窗口信息类"""

    def __init__(self, window_element, index: int):
        """
        初始化微信窗口对象

        参数:
            window_element: uiautomation 窗口元素对象
            index: 窗口编号（用于用户选择）
        """
        self.element = window_element
        self.index = index
        self.name = window_element.Name
        self.handle = window_element.NativeWindowHandle

        # 获取窗口位置和大小
        try:
            rect = window_element.BoundingRectangle
            self.left = rect.left
            self.top = rect.top
            self.right = rect.right
            self.bottom = rect.bottom
            self.width = rect.right - rect.left
            self.height = rect.bottom - rect.top
        except:
            self.left = self.top = self.right = self.bottom = 0
            self.width = self.height = 0

    def __str__(self):
        return f"[{self.index}] {self.name} (句柄: {self.handle}, 大小: {self.width}x{self.height})"


def find_wechat_windows() -> List[WeChatWindow]:
    """
    查找所有微信窗口

    支持传统微信和Qt框架微信（PC 4.0+）

    返回:
        微信窗口对象列表
    """
    wechat_windows = []
    index = 1

    desktop = auto.GetRootControl()

    # 定义多种可能的微信窗口特征
    wechat_class_names = [
        "WeChatMainWndForPC",
        "WeChatMainWnd",
        "wxWindow",
    ]

    qt_wechat_indicators = ["Qt", "QWindow"]

    for window in desktop.GetChildren():
        try:
            class_name = window.ClassName or ""
            window_name = window.Name or ""

            is_wechat = False

            # 方法1：检查类名是否匹配已知微信类名
            if class_name in wechat_class_names:
                is_wechat = True

            # 方法2：检查类名是否包含 WeChat 关键词
            elif "WeChat" in class_name or "wechat" in class_name.lower():
                is_wechat = True

            # 方法3：检测 Qt 框架微信
            elif any(indicator in class_name for indicator in qt_wechat_indicators):
                if "微信" in window_name or len(window_name) > 0:
                    is_wechat = True

            # 方法4：检查窗口标题是否包含"微信"
            elif "微信" in window_name and len(window_name) < 10:
                is_wechat = True

            if is_wechat:
                wc_window = WeChatWindow(window, index)
                # 只添加有效的窗口（有大小）
                if wc_window.width > 0 and wc_window.height > 0:
                    wechat_windows.append(wc_window)
                    index += 1

        except Exception:
            continue

    return wechat_windows


def capture_window_screenshot(window: WeChatWindow) -> Optional[Image.Image]:
    """
    截取微信窗口的屏幕截图

    参数:
        window: 微信窗口对象

    返回:
        PIL Image 对象，如果失败返回 None
    """
    try:
        # 将窗口置为前台（确保窗口可见）
        try:
            window.element.SetFocus()
            time.sleep(0.5)
        except:
            pass

        # 截取窗口区域
        screenshot = ImageGrab.grab(
            bbox=(window.left, window.top, window.right, window.bottom)
        )

        return screenshot

    except Exception as e:
        print(f"截图失败: {e}")
        return None


def extract_chat_area(image: Image.Image) -> Image.Image:
    """
    从截图中提取聊天区域

    简化假设：左边是联系人列表，右边是聊天区域

    参数:
        image: 完整窗口截图

    返回:
        聊天区域的截图
    """
    width, height = image.size

    left = int(width * 0.3)      # 去掉左侧 30%（联系人列表）
    top = int(height * 0.1)      # 上方留 10% 边距
    right = width
    bottom = int(height * 0.9)   # 下方留 10% 边距

    chat_area = image.crop((left, top, right, bottom))
    return chat_area


def recognize_text_with_ocr(image: Image.Image) -> str:
    """
    使用 OCR 识别图片中的文字

    参数:
        image: 要识别的图片

    返回:
        识别出的文字
    """
    try:
        # 使用中文 + 英文识别
        custom_config = r"--oem 3 --psm 6 -l chi_sim+eng"
        text = pytesseract.image_to_string(image, config=custom_config)
        return text
    except Exception as e:
        print(f"OCR识别失败: {e}")
        return ""


def select_window(windows: List[WeChatWindow]) -> Optional[WeChatWindow]:
    """
    让用户选择要监控的微信窗口
    """
    if not windows:
        print("未找到任何微信窗口")
        return None

    print("\n" + "=" * 60)
    print("找到以下微信窗口：")
    print("=" * 60)

    for window in windows:
        print(f"  {window}")

    print("=" * 60)

    while True:
        try:
            choice = input(
                f"\n请选择要读取的窗口编号 (1-{len(windows)})，输入 0 退出: "
            ).strip()

            if choice == "0":
                return None

            index = int(choice)
            if 1 <= index <= len(windows):
                return windows[index - 1]
            else:
                print(f"请输入 1 到 {len(windows)} 之间的数字")

        except ValueError:
            print("请输入有效的数字")


def main():
    """
    主函数 - 程序入口
    """
    print("=" * 60)
    print("微信消息监控 PoC - 阶段1：技术验证（截图+OCR方案）")
    print("=" * 60)
    print("\n功能说明：")
    print("  1. 自动查找所有微信窗口")
    print("  2. 截取微信窗口屏幕")
    print("  3. 使用 OCR 识别消息文本")
    print("\n注意：")
    print("  - 请确保微信已登录并打开聊天窗口")
    print("  - 需要安装 Tesseract-OCR 引擎")
    print("  - 本工具仅供技术学习使用")
    print("=" * 60)

    # 检查 Tesseract 是否可用
    try:
        _ = pytesseract.get_tesseract_version()
    except Exception:
        print("\n警告：Tesseract-OCR 未正确安装或配置")
        print("请确认安装路径为 C:\\Program Files\\Tesseract-OCR，或根据实际路径修改脚本中的 tesseract_cmd 设置。")
        input("\n按回车键退出...")
        return

    # 步骤1：查找微信窗口
    print("\n正在查找微信窗口...")
    wechat_windows = find_wechat_windows()

    if not wechat_windows:
        print("\n未找到微信窗口，请检查：")
        print("  1. 微信是否已启动")
        print("  2. 是否已登录微信")
        print("  3. 微信版本是否兼容")
        input("\n按回车键退出...")
        return

    print(f"找到 {len(wechat_windows)} 个微信窗口")

    # 步骤2：选择窗口
    selected_window = select_window(wechat_windows)

    if not selected_window:
        print("用户取消选择，程序退出")
        return

    print(f"\n已选择窗口: {selected_window.name}")
    print("正在截图并识别文字...")
    print("（请确保微信窗口可见，不要最小化）")

    # 步骤3：截图
    screenshot = capture_window_screenshot(selected_window)

    if not screenshot:
        print("截图失败，程序退出")
        input("\n按回车键退出...")
        return

    screenshot_path = "wechat_screenshot.png"
    screenshot.save(screenshot_path)
    print(f"已保存完整截图: {screenshot_path}")

    # 步骤4：提取聊天区域
    chat_area = extract_chat_area(screenshot)
    chat_area_path = "wechat_chat_area.png"
    chat_area.save(chat_area_path)
    print(f"已保存聊天区域截图: {chat_area_path}")

    # 步骤5：OCR识别
    print("\n正在进行 OCR 识别...")
    recognized_text = recognize_text_with_ocr(chat_area)

    # 步骤6：显示结果
    print("\n" + "=" * 60)
    print("OCR 识别结果：")
    print("=" * 60)

    if recognized_text.strip():
        print(recognized_text)
    else:
        print("未能识别到文字")
        print("\n可能原因：")
        print("  1. 聊天区域没有消息")
        print("  2. 图片质量不佳")
        print("  3. 没有安装中文语言包（chi_sim）")
        print("  4. OCR 引擎配置问题")

    print("=" * 60)
    print("\n操作完成！")
    input("\n按回车键退出...")


if __name__ == "__main__":
    main()
