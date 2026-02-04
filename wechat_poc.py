#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信消息监控 PoC - 阶段1：技术验证
基于 Windows UI Automation 技术实现

功能：
1. 枚举系统中运行的微信窗口
2. 选择特定聊天窗口
3. 读取窗口中的消息文本

作者：AI Assistant
日期：2025年
"""

import sys
import time
from typing import List, Optional

# 导入 Windows UI Automation 库
try:
    import uiautomation as auto
except ImportError:
    print("错误：未安装 uiautomation 库")
    print("请运行: pip install uiautomation")
    sys.exit(1)


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
        self.name = window_element.Name  # 窗口标题（通常是聊天对象名称）
        self.handle = window_element.NativeWindowHandle  # 窗口句柄

    def __str__(self):
        return f"[{self.index}] {self.name} (句柄: {self.handle})"


def find_wechat_windows() -> List[WeChatWindow]:
    """
    查找所有微信窗口

    原理：
    - 微信窗口的类名通常是 "WeChatMainWndForPC"
    - 新版本微信可能使用不同的类名
    - 通过遍历所有顶层窗口，使用多种方式匹配微信窗口

    返回:
        微信窗口对象列表
    """
    wechat_windows = []
    index = 1

    # 获取桌面根元素
    desktop = auto.GetRootControl()

    # 定义多种可能的微信窗口特征（按优先级排序）
    wechat_class_names = [
        "WeChatMainWndForPC",  # 传统 PC 版微信类名
        "WeChatMainWnd",  # 可能的简化类名
        "wxWindow",  # wxWidgets 框架类名
    ]

    # Qt 框架微信的类名特征（微信PC 4.0+ 版本）
    # Qt 应用的类名通常是 Qt + 版本号 + QWindowIcon 或类似格式
    qt_wechat_indicators = [
        "Qt",  # Qt 框架标识
        "QWindow",  # Qt 窗口标识
    ]

    # 遍历所有顶层窗口
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

            # 方法3：检测 Qt 框架微信（微信PC 4.0+ 版本）
            # Qt 类名格式如：Qt51514QWindowIcon、Qt5QWindowIcon 等
            elif any(indicator in class_name for indicator in qt_wechat_indicators):
                # 进一步验证：Qt 微信窗口的标题通常包含"微信"或是联系人名称
                # 主窗口标题通常是"微信"，聊天窗口标题是联系人/群名称
                if "微信" in window_name or len(window_name) > 0:
                    is_wechat = True

            # 方法4：检查窗口标题是否包含"微信"（辅助判断）
            # 注意：聊天窗口标题通常是联系人名称，不是"微信"
            # 所以这个方法只能作为辅助
            elif "微信" in window_name and len(window_name) < 10:
                is_wechat = True

            if is_wechat:
                wc_window = WeChatWindow(window, index)
                wechat_windows.append(wc_window)
                index += 1

        except Exception as e:
            # 某些窗口可能无法访问，忽略错误
            continue

    return wechat_windows


def get_chat_messages(window_element) -> List[str]:
    """
    从微信窗口中读取聊天消息

    原理：
    - 微信聊天消息通常位于特定的 UI 控件中
    - 通过遍历控件树，找到包含消息的文本控件
    - 提取控件的 Name 属性（即消息文本）

    参数:
        window_element: 微信窗口元素

    返回:
        消息文本列表
    """
    messages = []
    seen_texts = set()  # 用于去重

    try:
        # 方法1：使用 WalkTree 遍历所有控件（兼容不同版本的 uiautomation 库）
        def walk_controls(control, depth=0):
            """递归遍历控件树"""
            if depth > 10:  # 限制遍历深度，避免过深递归
                return

            try:
                # 获取控件文本
                text = control.Name
                control_type = control.ControlType
                class_name = control.ClassName

                # 检查是否是文本类型的控件
                is_text_control = False

                # 检查控件类型
                if hasattr(auto.ControlType, "TextControl"):
                    if control_type == auto.ControlType.TextControl:
                        is_text_control = True

                # 检查类名特征（Qt 框架微信的消息控件）
                if class_name and isinstance(class_name, str):
                    # Qt 框架的消息控件可能有这些特征
                    if any(
                        keyword in class_name
                        for keyword in ["Text", "Label", "Item", "Chat"]
                    ):
                        is_text_control = True

                # 如果是文本控件且内容有效
                if is_text_control and text and isinstance(text, str):
                    text = text.strip()
                    # 过滤条件
                    if (
                        len(text) > 0
                        and text != window_element.Name
                        and text not in seen_texts
                        and len(text) < 1000
                    ):  # 过滤过长文本
                        messages.append(text)
                        seen_texts.add(text)

                # 递归遍历子控件
                children = control.GetChildren()
                for child in children:
                    walk_controls(child, depth + 1)

            except Exception as e:
                # 某些控件可能无法访问，忽略错误
                pass

        # 开始遍历
        walk_controls(window_element)

        # 方法2：尝试直接获取窗口的所有子控件（备用方案）
        if not messages:
            try:
                children = window_element.GetChildren()
                for child in children:
                    try:
                        text = child.Name
                        if text and isinstance(text, str):
                            text = text.strip()
                            if (
                                len(text) > 0
                                and text != window_element.Name
                                and text not in seen_texts
                            ):
                                messages.append(text)
                                seen_texts.add(text)
                    except:
                        continue
            except:
                pass

        # 方法3：针对 Qt 框架微信的特殊处理
        # Qt 应用的消息可能嵌套在多层容器中
        if not messages:
            try:
                # 尝试查找所有可访问的文本
                all_controls = []

                # 获取直接子控件
                children = window_element.GetChildren()
                all_controls.extend(children)

                # 获取孙子控件
                for child in children:
                    try:
                        grandchildren = child.GetChildren()
                        all_controls.extend(grandchildren)
                    except:
                        continue

                # 检查所有收集到的控件
                for ctrl in all_controls:
                    try:
                        text = ctrl.Name
                        if text and isinstance(text, str):
                            text = text.strip()
                            # 更宽松的过滤条件
                            if (
                                len(text) > 0
                                and len(text) < 2000
                                and text not in seen_texts
                            ):
                                messages.append(text)
                                seen_texts.add(text)
                    except:
                        continue
            except:
                pass

    except Exception as e:
        print(f"读取消息时出错: {e}")

    return messages


def select_window(windows: List[WeChatWindow]) -> Optional[WeChatWindow]:
    """
    让用户选择要监控的微信窗口

    参数:
        windows: 微信窗口列表

    返回:
        用户选择的窗口对象，如果用户取消则返回 None
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


def display_messages(messages: List[str], window_name: str):
    """
    在终端显示读取到的消息

    参数:
        messages: 消息文本列表
        window_name: 窗口名称（聊天对象）
    """
    print("\n" + "=" * 60)
    print(f"窗口 [{window_name}] 中的消息：")
    print("=" * 60)

    if not messages:
        print("未读取到任何消息")
        print("可能原因：")
        print("  1. 该窗口不是聊天窗口（可能是主界面、通讯录等）")
        print("  2. 微信版本较新，UI 结构发生变化")
        print("  3. 聊天窗口中没有消息")
    else:
        for i, msg in enumerate(messages, 1):
            # 限制显示长度，避免终端输出过长
            display_msg = msg[:200] + "..." if len(msg) > 200 else msg
            print(f"{i}. {display_msg}")

    print("=" * 60)
    print(f"共读取到 {len(messages)} 条消息")
    print("=" * 60)


def main():
    """
    主函数 - 程序入口
    """
    print("=" * 60)
    print("微信消息监控 PoC - 阶段1：技术验证")
    print("=" * 60)
    print("\n功能说明：")
    print("  1. 自动查找所有微信窗口")
    print("  2. 选择要读取的聊天窗口")
    print("  3. 提取并显示窗口中的消息文本")
    print("\n注意：")
    print("  - 请确保微信已登录并打开聊天窗口")
    print("  - 本工具仅供技术学习使用")
    print("=" * 60)

    # 步骤1：查找微信窗口
    print("\n正在查找微信窗口...")
    wechat_windows = find_wechat_windows()

    if not wechat_windows:
        print("\n未找到微信窗口，请检查：")
        print("  1. 微信是否已启动")
        print("  2. 是否已登录微信")
        print("  3. 微信版本是否兼容（当前支持 PC 版微信）")
        print("\n提示：可以运行 diagnose.py 查看详细的窗口诊断信息")
        print("      命令: python diagnose.py")
        input("\n按回车键退出...")
        return

    print(f"找到 {len(wechat_windows)} 个微信窗口")

    # 步骤2：选择窗口
    selected_window = select_window(wechat_windows)

    if not selected_window:
        print("用户取消选择，程序退出")
        return

    print(f"\n已选择窗口: {selected_window.name}")
    print("正在读取消息...")

    # 步骤3：读取消息
    # 先尝试将窗口置为前台（某些情况下需要）
    try:
        selected_window.element.SetFocus()
        time.sleep(0.5)  # 等待窗口响应
    except:
        pass  # 如果无法置为前台，继续尝试读取

    messages = get_chat_messages(selected_window.element)

    # 步骤4：显示结果
    display_messages(messages, selected_window.name)

    # 提示用户
    print("\n操作完成！")
    print("\n当前限制说明：")
    print("  - 只能读取当前可见窗口的消息")
    print("  - 无法自动检测新消息（需要重新运行脚本）")
    print("  - 无法区分消息发送者和接收者")
    print("  - 微信更新后可能需要调整代码")

    input("\n按回车键退出...")


if __name__ == "__main__":
    main()
