#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信消息监控 - 数据导出工具
支持导出消息记录到 CSV/Excel

使用示例:
    python export.py --from 2026-02-01 --to 2026-02-03 --keywords 退款,订单 --output export.csv
    python export.py --days 7 --format excel --output recent7days.xlsx
"""

import argparse
import csv
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional


def parse_date(date_str: str) -> datetime:
    """解析日期字符串"""
    formats = ["%Y-%m-%d", "%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    raise ValueError(f"无法解析日期: {date_str}")


def query_messages(
    db_path: str,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    keywords: Optional[List[str]] = None,
) -> List[dict]:
    """查询消息记录"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 构建查询条件
    conditions = []
    params = []

    if start_time:
        conditions.append("created_at >= ?")
        params.append(start_time.strftime("%Y-%m-%d %H:%M:%S.%f"))

    if end_time:
        conditions.append("created_at <= ?")
        params.append(end_time.strftime("%Y-%m-%d %H:%M:%S.%f"))

    if keywords:
        keyword_conditions = []
        for keyword in keywords:
            keyword_conditions.append("matched_keyword = ?")
            params.append(keyword)
        if keyword_conditions:
            conditions.append(f"({' OR '.join(keyword_conditions)})")

    # 构建SQL
    sql = "SELECT * FROM messages"
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    sql += " ORDER BY created_at DESC"

    cursor.execute(sql, params)
    rows = cursor.fetchall()

    # 转换为字典列表
    messages = []
    for row in rows:
        messages.append(
            {
                "id": row["id"],
                "时间": row["created_at"],
                "会话名": row["window_title"],
                "消息内容": row["message_text"],
                "命中关键字": row["matched_keyword"],
                "截图路径": row["screenshot_path"] or "",
            }
        )

    conn.close()
    return messages


def export_to_csv(messages: List[dict], output_path: str) -> None:
    """导出到CSV文件"""
    if not messages:
        print("没有数据可导出")
        return

    fieldnames = ["id", "时间", "会话名", "消息内容", "命中关键字", "截图路径"]

    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(messages)

    print(f"成功导出 {len(messages)} 条记录到: {output_path}")


def export_to_excel(messages: List[dict], output_path: str) -> None:
    """导出到Excel文件"""
    try:
        import openpyxl
        from openpyxl.styles import Font, Alignment
    except ImportError:
        print("错误: 导出Excel需要 openpyxl 库")
        print("请运行: pip install openpyxl")
        sys.exit(1)

    if not messages:
        print("没有数据可导出")
        return

    wb = openpyxl.Workbook()
    ws = wb.active

    if ws is None:
        print("错误: 无法创建工作表")
        return

    ws.title = "消息记录"

    # 写入表头
    headers = ["id", "时间", "会话名", "消息内容", "命中关键字", "截图路径"]
    ws.append(headers)

    # 设置表头样式
    first_row = ws[1]
    if first_row:
        for cell in first_row:
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal="center")

    # 写入数据
    for msg in messages:
        ws.append(
            [
                msg["id"],
                msg["时间"],
                msg["会话名"],
                msg["消息内容"],
                msg["命中关键字"],
                msg["截图路径"],
            ]
        )

    # 调整列宽
    if ws.column_dimensions:
        ws.column_dimensions["A"].width = 8
        ws.column_dimensions["B"].width = 20
        ws.column_dimensions["C"].width = 25
        ws.column_dimensions["D"].width = 50
        ws.column_dimensions["E"].width = 15
        ws.column_dimensions["F"].width = 30

    wb.save(output_path)
    print(f"成功导出 {len(messages)} 条记录到: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="导出微信监控消息记录",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --from 2026-02-01 --to 2026-02-03 --output export.csv
  %(prog)s --days 7 --format excel --output week.xlsx
  %(prog)s --keywords 退款,订单 --from 2026-02-01 --output refunds.csv
        """,
    )

    parser.add_argument(
        "--db",
        default="./wechat_monitor.db",
        help="数据库文件路径 (默认: ./wechat_monitor.db)",
    )

    parser.add_argument(
        "--from",
        dest="start_date",
        help="开始日期 (格式: YYYY-MM-DD)",
    )

    parser.add_argument(
        "--to",
        dest="end_date",
        help="结束日期 (格式: YYYY-MM-DD, 默认: 今天)",
    )

    parser.add_argument(
        "--days",
        type=int,
        help="导出最近N天的数据",
    )

    parser.add_argument(
        "--keywords",
        help="按关键字过滤，多个关键字用逗号分隔",
    )

    parser.add_argument(
        "--format",
        choices=["csv", "excel"],
        default="csv",
        help="导出格式 (默认: csv)",
    )

    parser.add_argument(
        "--output",
        "-o",
        required=True,
        help="输出文件路径",
    )

    args = parser.parse_args()

    # 检查数据库文件
    if not Path(args.db).exists():
        print(f"错误: 数据库文件不存在: {args.db}")
        sys.exit(1)

    # 处理时间范围
    start_time = None
    end_time = None

    if args.days:
        # 最近N天
        start_time = datetime.now() - timedelta(days=args.days)
        end_time = datetime.now()
    else:
        # 指定日期范围
        if args.start_date:
            start_time = parse_date(args.start_date)
        if args.end_date:
            # 结束日期设置为当天的23:59:59
            end_time = (
                parse_date(args.end_date) + timedelta(days=1) - timedelta(seconds=1)
            )

    # 处理关键字
    keywords = None
    if args.keywords:
        keywords = [k.strip() for k in args.keywords.split(",")]

    # 查询数据
    print(f"正在查询数据库: {args.db}")
    if start_time:
        print(f"时间范围: {start_time} 至 {end_time or '现在'}")
    if keywords:
        print(f"关键字过滤: {keywords}")

    messages = query_messages(args.db, start_time, end_time, keywords)

    if not messages:
        print("未找到匹配的记录")
        sys.exit(0)

    print(f"找到 {len(messages)} 条记录")

    # 导出数据
    if args.format == "csv":
        export_to_csv(messages, args.output)
    else:
        export_to_excel(messages, args.output)


if __name__ == "__main__":
    main()
