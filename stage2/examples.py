#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多源监控使用示例
演示如何使用新的消息源架构
"""

import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from monitor_v2 import MultiSourceMonitor
from sources.wechat_screen import create_wechat_screen_source
from sources.window_screen import create_window_screen_source
from sources.wechat_api import create_wechat_api_source


def example_single_source():
    """示例1：单消息源（微信桌面）"""
    print("=" * 60)
    print("示例1：单消息源监控")
    print("=" * 60)

    # 创建监控器
    monitor = MultiSourceMonitor()

    # 添加微信桌面消息源
    source = create_wechat_screen_source(
        name="微信-叶亮", window_title_pattern="叶亮", poll_interval=5
    )
    monitor.add_source(source)

    print("配置完成，消息源：")
    for s in monitor.sources:
        print(f"  - {s.name} (平台: {s.platform})")

    # 运行（按 Ctrl+C 停止）
    # monitor.run()


def example_multi_window():
    """示例2：多窗口监控"""
    print("\n" + "=" * 60)
    print("示例2：多窗口监控")
    print("=" * 60)

    monitor = MultiSourceMonitor()

    # 添加多个微信窗口
    source1 = create_wechat_screen_source(
        name="微信-叶亮", window_title_pattern="叶亮", poll_interval=5
    )
    monitor.add_source(source1)

    source2 = create_wechat_screen_source(
        name="微信-客服群", window_title_pattern="客服", poll_interval=5
    )
    monitor.add_source(source2)

    # 添加 QQ 窗口
    qq_source = create_window_screen_source(
        name="QQ-工作群", app_type="qq", title_contains="工作群", poll_interval=5
    )
    monitor.add_source(qq_source)

    print("配置完成，消息源：")
    for s in monitor.sources:
        print(f"  - {s.name} (平台: {s.platform})")

    # monitor.run()


def example_mixed_sources():
    """示例3：混合消息源（桌面 + API）"""
    print("\n" + "=" * 60)
    print("示例3：混合消息源（桌面 + API）")
    print("=" * 60)

    monitor = MultiSourceMonitor()

    # 桌面端微信
    screen_source = create_wechat_screen_source(
        name="微信桌面", window_title_pattern="", poll_interval=5
    )
    monitor.add_source(screen_source)

    # 微信小程序客服 API
    # 注意：需要先在 config.yaml 中配置 app_id 和 app_secret
    api_source = create_wechat_api_source(
        name="小程序客服",
        app_id="wx1234567890abcdef",  # 替换为你的 AppID
        app_secret="your_secret_here",  # 替换为你的 AppSecret
        token="your_token_here",  # 替换为你的 Token
        poll_interval=5,
    )
    monitor.add_source(api_source)

    print("配置完成，消息源：")
    for s in monitor.sources:
        print(f"  - {s.name} (平台: {s.platform})")

    print("\n说明：")
    print("  - 微信桌面：通过截图+OCR获取消息")
    print("  - 小程序客服：通过 Webhook 接收消息")
    print("  - 所有消息统一存储，支持平台过滤")

    # monitor.run()


def example_from_config():
    """示例4：从配置文件加载"""
    print("\n" + "=" * 60)
    print("示例4：从配置文件加载")
    print("=" * 60)

    from monitor_v2 import create_default_monitor

    monitor = create_default_monitor()

    print("从 config.yaml 加载的配置：")
    for s in monitor.sources:
        print(f"  - {s.name} (平台: {s.platform})")

    # monitor.run()


if __name__ == "__main__":
    # 运行示例
    example_single_source()
    example_multi_window()
    example_mixed_sources()
    example_from_config()

    print("\n" + "=" * 60)
    print("提示：取消注释 monitor.run() 来启动监控")
    print("=" * 60)
