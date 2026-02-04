#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信窗口诊断工具
用于排查微信窗口识别问题

功能：
1. 列出所有顶层窗口的类名和标题
2. 尝试多种方式识别微信窗口
3. 输出诊断信息供分析
"""

import sys

try:
    import uiautomation as auto
except ImportError:
    print("错误：未安装 uiautomation 库")
    print("请运行: pip install uiautomation")
    sys.exit(1)


def list_all_windows():
    """
    列出系统中所有顶层窗口的类名和标题
    """
    print("=" * 80)
    print("诊断信息 1：系统中所有顶层窗口")
    print("=" * 80)
    print(f"{'序号':<6} {'窗口句柄':<12} {'类名(ClassName)':<40} {'窗口标题(Name)'}")
    print("-" * 80)

    desktop = auto.GetRootControl()
    index = 1

    for window in desktop.GetChildren():
        try:
            class_name = window.ClassName or "(空)"
            window_name = window.Name or "(空)"
            handle = window.NativeWindowHandle

            # 只显示有标题或类名的窗口
            if class_name != "(空)" or window_name != "(空)":
                # 截断过长的字符串
                class_display = (
                    class_name[:38]
                    if len(class_name) <= 40
                    else class_name[:37] + "..."
                )
                name_display = (
                    window_name[:30]
                    if len(window_name) <= 32
                    else window_name[:29] + "..."
                )

                print(f"{index:<6} {handle:<12} {class_display:<40} {name_display}")
                index += 1
        except Exception as e:
            # 某些窗口可能无法访问，跳过
            continue

    print("-" * 80)
    print(f"共找到 {index - 1} 个窗口")
    print("=" * 80)


def find_wechat_by_keywords():
    """
    使用多种关键词尝试识别微信窗口
    """
    print("\n" + "=" * 80)
    print("诊断信息 2：尝试用不同方式识别微信窗口")
    print("=" * 80)

    desktop = auto.GetRootControl()

    # 定义多种可能的微信窗口特征
    wechat_keywords = [
        ("类名包含", "WeChat"),
        ("类名包含", "wechat"),
        ("类名包含", "WX"),
        ("标题包含", "微信"),
        ("类名等于", "WeChatMainWndForPC"),
        ("类名包含", "Chat"),
        ("类名包含", "chat"),
    ]

    found_any = False

    for check_type, keyword in wechat_keywords:
        matches = []

        for window in desktop.GetChildren():
            try:
                if check_type == "类名包含":
                    if keyword in window.ClassName:
                        matches.append(window)
                elif check_type == "标题包含":
                    if keyword in window.Name:
                        matches.append(window)
                elif check_type == "类名等于":
                    if window.ClassName == keyword:
                        matches.append(window)
            except:
                continue

        if matches:
            found_any = True
            print(f"\n✓ 通过 '{check_type}:{keyword}' 找到 {len(matches)} 个窗口：")
            for i, window in enumerate(matches, 1):
                print(
                    f"  [{i}] 类名: {window.ClassName}, 标题: {window.Name}, 句柄: {window.NativeWindowHandle}"
                )

    if not found_any:
        print("\n✗ 未找到任何匹配的微信窗口")
        print("\n可能原因：")
        print("  1. 微信确实没有运行")
        print("  2. 微信窗口被其他方式隐藏或保护")
        print("  3. 微信使用了特殊的窗口技术（如 Electron 的透明窗口）")

    print("=" * 80)


def check_wechat_process():
    """
    检查微信进程是否存在（使用 uiautomation 的进程信息）
    """
    print("\n" + "=" * 80)
    print("诊断信息 3：检查微信相关进程")
    print("=" * 80)

    try:
        # 尝试通过进程名查找
        import os
        import subprocess

        # 使用 tasklist 命令查找微信进程
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq WeChat.exe", "/FO", "CSV"],
            capture_output=True,
            text=True,
            encoding="gbk",  # Windows 中文系统默认编码
        )

        if "WeChat.exe" in result.stdout:
            print("✓ 发现 WeChat.exe 进程正在运行：")
            print(result.stdout)
        else:
            print("✗ 未找到 WeChat.exe 进程")
            print("\n请确认：")
            print("  1. 微信是否已经启动")
            print("  2. 微信进程名是否为 WeChat.exe")
    except Exception as e:
        print(f"检查进程时出错: {e}")

    print("=" * 80)


def test_window_access():
    """
    测试窗口访问能力
    """
    print("\n" + "=" * 80)
    print("诊断信息 4：测试窗口访问能力")
    print("=" * 80)

    desktop = auto.GetRootControl()
    accessible_count = 0
    error_count = 0

    for window in desktop.GetChildren()[:10]:  # 只测试前10个窗口
        try:
            _ = window.ClassName
            _ = window.Name
            accessible_count += 1
        except Exception as e:
            error_count += 1

    print(f"测试了 10 个窗口：")
    print(f"  成功访问: {accessible_count} 个")
    print(f"  访问失败: {error_count} 个")

    if error_count > 5:
        print("\n警告：大量窗口无法访问，可能存在权限问题")
        print("建议：尝试以管理员身份运行此脚本")

    print("=" * 80)


def main():
    """
    主函数 - 运行所有诊断
    """
    print("=" * 80)
    print("微信窗口诊断工具")
    print("=" * 80)
    print("\n本工具用于诊断为什么找不到微信窗口")
    print("请确保微信已经启动并登录，然后查看下面的诊断信息\n")

    # 运行所有诊断
    list_all_windows()
    find_wechat_by_keywords()
    check_wechat_process()
    test_window_access()

    print("\n" + "=" * 80)
    print("诊断完成")
    print("=" * 80)
    print("\n请复制以下信息给我：")
    print("  1. '诊断信息 1' 中所有包含 'WeChat'、'微信' 或类似关键词的行")
    print("  2. '诊断信息 2' 中的所有匹配结果")
    print("  3. '诊断信息 3' 中的进程检查结果")
    print("\n这样我就能帮你调整窗口识别逻辑了。")

    input("\n按回车键退出...")


if __name__ == "__main__":
    main()
