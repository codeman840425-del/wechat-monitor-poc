#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通知功能测试脚本
测试 notification_system 和 monitor_v2 集成
"""

import sys
import os
import time
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager, MessageRecord
from notification_system import (
    NotificationSystem,
    NotificationMessage,
    NotificationPriority,
    init_notification_system,
)


def test_notification_system():
    """测试通知系统基础功能"""
    print("=" * 60)
    print("测试1: 通知系统基础功能")
    print("=" * 60)

    # 测试配置
    test_config = {
        "notification": {
            "enabled": True,
            "default_channels": ["console", "file"],
            "rules": [
                {
                    "name": "测试规则",
                    "keywords": ["测试", "退款"],
                    "channels": ["console", "file"],
                    "priority": "NORMAL",
                    "cooldown": 0,  # 测试时关闭冷却
                }
            ],
            "channels": {
                "console": {"enabled": True},
                "file": {"enabled": True, "path": "./test_notifications.log"},
            },
        }
    }

    try:
        # 初始化通知系统
        notification_system = init_notification_system(test_config)
        print("[OK] 通知系统初始化成功")

        # 测试发送通知
        import asyncio

        async def send_test():
            msg = NotificationMessage(
                title="测试通知",
                content="这是一条测试消息，关键字：退款",
                keyword="退款",
                source="测试",
            )
            results = await notification_system.notify(msg)
            print(f"[OK] 通知发送结果: {results}")

        asyncio.run(send_test())
        print("[OK] 通知系统基础功能测试通过")
        return True

    except Exception as e:
        print(f"[FAIL] 通知系统测试失败: {e}")
        return False


def test_monitor_v2_integration():
    """测试 monitor_v2 集成"""
    print("\n" + "=" * 60)
    print("测试2: monitor_v2 集成")
    print("=" * 60)

    try:
        from monitor_v2 import MultiSourceMonitor, NOTIFICATION_AVAILABLE

        print(f"[INFO] 通知系统可用: {NOTIFICATION_AVAILABLE}")

        # 创建监控实例
        monitor = MultiSourceMonitor("config.yaml")
        print("[OK] monitor_v2 初始化成功")

        # 检查通知系统是否初始化
        if monitor.notification_system:
            print("[OK] 通知系统已集成到 monitor_v2")
        else:
            print("[INFO] 通知系统未启用（配置中可能禁用了）")

        # 测试 _send_notification 方法
        from database import MessageRecord

        test_record = MessageRecord(
            id=1,
            window_title="测试窗口",
            window_handle=0,
            message_text="测试消息，包含关键字：退款",
            matched_keyword="退款",
            screenshot_path=None,
            created_at=None,
        )

        # 调用发送通知方法（在后台线程中）
        monitor._send_notification(test_record)
        time.sleep(1)  # 等待通知发送完成

        print("[OK] _send_notification 方法调用成功")
        return True

    except Exception as e:
        print(f"[FAIL] monitor_v2 集成测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_config_loading():
    """测试配置加载"""
    print("\n" + "=" * 60)
    print("测试3: 配置加载")
    print("=" * 60)

    try:
        import yaml

        with open("config.yaml", "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        notification_config = config.get("notification", {})
        print(f"[INFO] 通知系统启用: {notification_config.get('enabled', False)}")
        print(f"[INFO] 通知规则数: {len(notification_config.get('rules', []))}")
        print(
            f"[INFO] 通知渠道: {list(notification_config.get('channels', {}).keys())}"
        )

        print("[OK] 配置加载成功")
        return True

    except Exception as e:
        print(f"[FAIL] 配置加载失败: {e}")
        return False


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("通知功能集成测试")
    print("=" * 60 + "\n")

    results = []

    # 运行测试
    results.append(("通知系统基础功能", test_notification_system()))
    results.append(("monitor_v2 集成", test_monitor_v2_integration()))
    results.append(("配置加载", test_config_loading()))

    # 打印汇总
    print("\n" + "=" * 60)
    print("测试汇总")
    print("=" * 60)

    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {name}")

    passed = sum(1 for _, r in results if r)
    total = len(results)

    print(f"\n总计: {passed}/{total} 通过")

    if passed == total:
        print("\n[OK] 所有测试通过！通知功能集成成功。")
        return 0
    else:
        print("\n[WARNING] 部分测试失败，请检查错误信息。")
        return 1


if __name__ == "__main__":
    exit(main())
