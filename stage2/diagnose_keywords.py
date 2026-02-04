#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
关键字加载诊断脚本
用于排查监控程序关键字加载问题
"""

import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager


def diagnose_keywords():
    """诊断关键字加载问题"""
    print("=" * 60)
    print("关键字加载诊断")
    print("=" * 60)

    # 1. 检查数据库连接
    db = DatabaseManager("./wechat_monitor.db")
    print("\n1. 数据库连接: OK")

    # 2. 检查 keywords 表
    conn = db._get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM keywords")
    count = cursor.fetchone()[0]
    print(f"\n2. keywords 表记录数: {count}")

    # 3. 获取所有关键字
    cursor.execute("SELECT id, word, enabled, created_at FROM keywords ORDER BY id")
    rows = cursor.fetchall()

    print("\n3. 所有关键字:")
    for row in rows:
        status = "启用" if row["enabled"] else "禁用"
        print(f"   ID:{row['id']} | {row['word']} | {status} | {row['created_at']}")

    # 4. 获取启用的关键字
    enabled_keywords = db.get_keywords_from_db(enabled_only=True)
    print(f"\n4. 启用的关键字 ({len(enabled_keywords)} 个):")
    for kw in enabled_keywords:
        print(f"   - {kw}")

    # 5. 测试匹配
    if enabled_keywords:
        print(f"\n5. 匹配测试:")
        test_messages = [
            "我要退款，这个订单有问题",
            "价格太贵了",
            "我要投诉你们",
            "这个没有关键字",
            "我想异常处理",
        ]

        # 模拟 monitor_v2 的 KeywordFilter
        from monitor_v2 import KeywordFilter

        kf = KeywordFilter(enabled_keywords, case_sensitive=False)

        for msg in test_messages:
            matched = kf.check(msg)
            status = f"[OK] 匹配: {matched}" if matched else "[X] 未匹配"
            print(f'   "{msg}" -> {status}')

    # 6. 检查配置文件
    print(f"\n6. 配置文件关键字 (config.yaml):")
    try:
        import yaml

        with open("config.yaml", "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        cfg_keywords = config.get("keywords", {}).get("list", [])
        print(f"   数量: {len(cfg_keywords)}")
        for kw in cfg_keywords:
            print(f"   - {kw}")
    except Exception as e:
        print(f"   读取失败: {e}")

    print("\n" + "=" * 60)
    print("诊断完成")
    print("=" * 60)
    print("\n建议:")
    print("- 如果数据库关键字列表正确但监控程序不加载，请检查：")
    print("  1. 是否运行的是 monitor_v2.py 而不是 monitor.py")
    print("  2. 监控程序启动日志中是否显示 '从数据库加载 X 个关键字'")
    print("- 如果新关键字无法匹配，请检查关键字是否包含特殊字符或空格")


if __name__ == "__main__":
    diagnose_keywords()
