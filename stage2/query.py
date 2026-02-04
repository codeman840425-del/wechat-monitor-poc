#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库查询工具
用于查询和导出监控数据

使用示例:
    python query.py recent 60                    # 最近60分钟
    python query.py stats                         # 统计信息
    python query.py filter --keyword 退款         # 按关键字过滤
    python query.py filter --from 2026-02-01 --to 2026-02-03
"""

import argparse
import sqlite3
import sys
from datetime import datetime, timedelta
from typing import Any, List, Optional

from tabulate import tabulate


def query_recent_messages(
    db_path: str = "./wechat_monitor.db",
    minutes: int = 60,
    keyword: Optional[str] = None,
):
    """查询最近的消息"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    start_time = datetime.now() - timedelta(minutes=minutes)

    # 构建查询
    # 注意：数据库中的 created_at 是 'YYYY-MM-DD HH:MM:SS.ssssss' 格式
    # 不是 ISO 格式，所以不能用 isoformat()
    sql = "SELECT * FROM messages WHERE created_at >= ?"
    params = [start_time.strftime("%Y-%m-%d %H:%M:%S.%f")]

    if keyword:
        sql += " AND matched_keyword = ?"
        params.append(keyword)

    sql += " ORDER BY created_at DESC"

    cursor.execute(sql, params)
    rows = cursor.fetchall()

    if not rows:
        filter_info = f" (关键字: {keyword})" if keyword else ""
        print(f"最近 {minutes} 分钟内没有消息{filter_info}")
        return

    # 格式化输出
    data: List[List[Any]] = []
    for row in rows:
        data.append(
            [
                row["id"],
                row["window_title"][:20],
                row["matched_keyword"],
                row["message_text"][:50] + "..."
                if len(row["message_text"]) > 50
                else row["message_text"],
                row["created_at"],
            ]
        )

    headers = ["ID", "会话名", "关键字", "消息内容", "时间"]
    print(tabulate(data, headers=headers, tablefmt="grid"))
    print(f"\n共 {len(rows)} 条消息")


def query_by_date_range(
    db_path: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    keyword: Optional[str] = None,
):
    """按日期范围查询消息"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 构建查询条件
    conditions = []
    params = []

    if start_date:
        conditions.append("created_at >= ?")
        params.append(start_date.strftime("%Y-%m-%d %H:%M:%S.%f"))

    if end_date:
        conditions.append("created_at <= ?")
        params.append(end_date.strftime("%Y-%m-%d %H:%M:%S.%f"))

    if keyword:
        conditions.append("matched_keyword = ?")
        params.append(keyword)

    # 构建SQL
    sql = "SELECT * FROM messages"
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    sql += " ORDER BY created_at DESC"

    cursor.execute(sql, params)
    rows = cursor.fetchall()

    if not rows:
        filter_info = ""
        if keyword:
            filter_info += f" (关键字: {keyword})"
        print(f"未找到匹配的消息{filter_info}")
        return

    # 格式化输出
    data: List[List[Any]] = []
    for row in rows:
        content = row["message_text"]
        if len(content) > 60:
            content = content[:60] + "..."
        data.append(
            [
                row["id"],
                row["window_title"][:18],
                row["matched_keyword"],
                content,
                row["created_at"][:16],
            ]
        )

    headers = ["ID", "会话名", "关键字", "消息内容", "时间"]
    print(tabulate(data, headers=headers, tablefmt="grid"))
    print(f"\n共 {len(rows)} 条消息")


def query_statistics(db_path: str = "./wechat_monitor.db"):
    """查询统计信息"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 总消息数
    cursor.execute("SELECT COUNT(*) as total FROM messages")
    total = cursor.fetchone()["total"]

    # 今日消息
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    cursor.execute(
        "SELECT COUNT(*) as today FROM messages WHERE created_at >= ?", (today,)
    )
    today_count = cursor.fetchone()["today"]

    # 最近7天消息
    week_ago = datetime.now() - timedelta(days=7)
    cursor.execute(
        "SELECT COUNT(*) as week FROM messages WHERE created_at >= ?", (week_ago,)
    )
    week_count = cursor.fetchone()["week"]

    # 关键字分布
    cursor.execute("""
        SELECT matched_keyword, COUNT(*) as count 
        FROM messages 
        GROUP BY matched_keyword 
        ORDER BY count DESC
        LIMIT 10
    """)
    keyword_stats = cursor.fetchall()

    print("=" * 60)
    print("统计信息")
    print("=" * 60)
    print(f"总消息数: {total}")
    print(f"今日消息: {today_count}")
    print(f"最近7天: {week_count}")
    print("\n关键字分布 (Top 10):")
    for row in keyword_stats:
        print(f"  {row['matched_keyword']}: {row['count']}")
    print("=" * 60)


def parse_date(date_str: str) -> datetime:
    """解析日期字符串"""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        try:
            return datetime.strptime(date_str, "%Y-%m-%d %H:%M")
        except ValueError:
            raise ValueError(f"无法解析日期: {date_str}，请使用格式 YYYY-MM-DD")


def main():
    parser = argparse.ArgumentParser(
        description="查询微信监控数据库",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s recent 60                    # 最近60分钟
  %(prog)s recent 60 --keyword 退款     # 最近60分钟，只显示退款
  %(prog)s stats                        # 统计信息
  %(prog)s filter --keyword 订单        # 按关键字过滤
  %(prog)s filter --from 2026-02-01 --to 2026-02-03
        """,
    )

    parser.add_argument(
        "--db",
        default="./wechat_monitor.db",
        help="数据库文件路径 (默认: ./wechat_monitor.db)",
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # recent 命令
    recent_parser = subparsers.add_parser("recent", help="查询最近的消息")
    recent_parser.add_argument(
        "minutes",
        nargs="?",
        type=int,
        default=60,
        help="最近多少分钟 (默认: 60)",
    )
    recent_parser.add_argument(
        "--keyword",
        help="按关键字过滤",
    )

    # stats 命令
    subparsers.add_parser("stats", help="查询统计信息")

    # filter 命令
    filter_parser = subparsers.add_parser("filter", help="按条件过滤消息")
    filter_parser.add_argument(
        "--from",
        dest="start_date",
        help="开始日期 (YYYY-MM-DD)",
    )
    filter_parser.add_argument(
        "--to",
        dest="end_date",
        help="结束日期 (YYYY-MM-DD)",
    )
    filter_parser.add_argument(
        "--keyword",
        help="按关键字过滤",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "recent":
        query_recent_messages(args.db, args.minutes, args.keyword)
    elif args.command == "stats":
        query_statistics(args.db)
    elif args.command == "filter":
        start_date = None
        end_date = None

        if args.start_date:
            start_date = parse_date(args.start_date)
        if args.end_date:
            end_date = (
                parse_date(args.end_date) + timedelta(days=1) - timedelta(seconds=1)
            )

        query_by_date_range(args.db, start_date, end_date, args.keyword)


if __name__ == "__main__":
    main()
