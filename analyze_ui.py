#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信 UI 结构分析工具
用于分析 Qt 框架微信的控件结构，帮助调试消息读取问题

功能：
1. 列出微信窗口的所有子控件
2. 显示控件的类名、类型和文本内容
3. 帮助理解 Qt 框架微信的 UI 结构
"""

import sys

try:
    import uiautomation as auto
except ImportError:
    print("错误：未安装 uiautomation 库")
    print("请运行: pip install uiautomation")
    sys.exit(1)


def analyze_wechat_window():
    """
    分析微信窗口的 UI 结构
    """
    print("=" * 80)
    print("微信 UI 结构分析工具")
    print("=" * 80)
    print("\n本工具将列出微信窗口的所有子控件，帮助你理解 UI 结构")
    print("请确保微信已经打开一个聊天窗口\n")

    # 查找微信窗口
    desktop = auto.GetRootControl()
    wechat_window = None

    for window in desktop.GetChildren():
        try:
            class_name = window.ClassName or ""
            window_name = window.Name or ""

            # 检测微信窗口（支持 Qt 框架）
            if (
                ("Qt" in class_name and "微信" in window_name)
                or ("WeChat" in class_name)
                or ("微信" in window_name and len(window_name) < 20)
            ):
                wechat_window = window
                print(f"找到微信窗口:")
                print(f"  标题: {window_name}")
                print(f"  类名: {class_name}")
                print(f"  句柄: {window.NativeWindowHandle}")
                break
        except:
            continue

    if not wechat_window:
        print("未找到微信窗口，请确保微信已启动")
        return

    print("\n" + "=" * 80)
    print("控件结构分析（前3层）")
    print("=" * 80)

    # 遍历控件树
    def print_control_tree(control, depth=0, max_depth=3):
        if depth > max_depth:
            return

        try:
            # 获取控件信息
            indent = "  " * depth
            control_type = str(control.ControlType).replace("ControlType.", "")
            class_name = control.ClassName or "(无类名)"
            name = control.Name or "(无文本)"

            # 截断过长的文本
            name_display = name[:50] + "..." if len(name) > 50 else name
            class_display = (
                class_name[:30] + "..." if len(class_name) > 30 else class_name
            )

            print(f"{indent}[{control_type}] {class_display}")
            if name and len(name) > 0:
                print(f"{indent}  文本: {name_display}")

            # 递归子控件
            children = control.GetChildren()
            for child in children:
                print_control_tree(child, depth + 1, max_depth)

        except Exception as e:
            indent = "  " * depth
            print(f"{indent}[无法访问] {e}")

    print_control_tree(wechat_window)

    print("\n" + "=" * 80)
    print("分析完成")
    print("=" * 80)
    print("\n说明：")
    print("- 如果看到包含消息文本的控件，请记录它的 ControlType 和 ClassName")
    print("- 这些控件信息将帮助优化消息读取逻辑")
    print("- 通常消息会显示在 TextControl、EditControl 或自定义控件中")

    input("\n按回车键退出...")


if __name__ == "__main__":
    analyze_wechat_window()
