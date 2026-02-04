#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信消息监控服务 - 阶段2：持续监控 + 数据存储
数据库模块：负责SQLite数据库操作

作者：AI Assistant
日期：2025年
"""

import sqlite3
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class MessageRecord:
    """消息记录数据类"""

    id: Optional[int]  # 数据库自增ID
    window_title: str  # 窗口标题（作为账号标识）
    window_handle: int  # 窗口句柄
    message_text: str  # 消息文本
    matched_keyword: str  # 匹配到的关键字
    screenshot_path: Optional[str]  # 截图文件路径
    created_at: datetime  # 创建时间


class DatabaseManager:
    """
    SQLite数据库管理器

    数据库表结构：
    - messages: 存储匹配的消息记录
    """

    def __init__(self, db_path: str = "./wechat_monitor.db"):
        """
        初始化数据库管理器

        参数:
            db_path: SQLite数据库文件路径
        """
        self.db_path = db_path
        self.connection: Optional[sqlite3.Connection] = None

        # 确保目录存在
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)

        # 初始化数据库
        self._init_database()

    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接（带连接池）"""
        if self.connection is None:
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            # 启用外键支持
            self.connection.execute("PRAGMA foreign_keys = ON")
            # 设置行工厂为字典类型
            self.connection.row_factory = sqlite3.Row
        return self.connection

    def _init_database(self):
        """初始化数据库表结构"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # 创建消息记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                window_title TEXT NOT NULL,
                window_handle INTEGER NOT NULL,
                message_text TEXT NOT NULL,
                matched_keyword TEXT NOT NULL,
                screenshot_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 创建索引（SQLite需要单独创建）
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_window_title ON messages(window_title)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_created_at ON messages(created_at)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_keyword ON messages(matched_keyword)"
        )

        # 创建统计视图
        cursor.execute("""
            CREATE VIEW IF NOT EXISTS message_stats AS
            SELECT 
                window_title,
                matched_keyword,
                COUNT(*) as count,
                MAX(created_at) as last_seen
            FROM messages
            GROUP BY window_title, matched_keyword
        """)

        # 创建关键字表（用于Web管理界面）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT UNIQUE NOT NULL,
                enabled BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 创建监控状态表（用于记录服务状态）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS monitor_status (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                status TEXT DEFAULT 'stopped',
                last_heartbeat TIMESTAMP,
                started_at TIMESTAMP,
                pid INTEGER,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 初始化状态记录
        cursor.execute("""
            INSERT OR IGNORE INTO monitor_status (id, status) VALUES (1, 'stopped')
        """)

        conn.commit()
        logger.info("数据库初始化完成")

    def insert_message(self, record: MessageRecord) -> int:
        """
        插入一条消息记录

        参数:
            record: 消息记录对象

        返回:
            插入记录的ID
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO messages 
            (window_title, window_handle, message_text, matched_keyword, screenshot_path, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                record.window_title,
                record.window_handle,
                record.message_text,
                record.matched_keyword,
                record.screenshot_path,
                record.created_at,
            ),
        )

        conn.commit()
        record_id = cursor.lastrowid
        logger.debug(f"插入消息记录，ID: {record_id}")
        return record_id if record_id is not None else -1

    def get_messages(
        self,
        window_title: Optional[str] = None,
        keyword: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[MessageRecord]:
        """
        查询消息记录

        参数:
            window_title: 窗口标题过滤
            keyword: 关键字过滤
            start_time: 开始时间
            end_time: 结束时间
            limit: 返回数量限制
            offset: 分页偏移

        返回:
            消息记录列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # 构建查询条件
        conditions = []
        params = []

        if window_title:
            conditions.append("window_title = ?")
            params.append(window_title)

        if keyword:
            conditions.append("matched_keyword = ?")
            params.append(keyword)

        if start_time:
            conditions.append("created_at >= ?")
            params.append(start_time)

        if end_time:
            conditions.append("created_at <= ?")
            params.append(end_time)

        # 构建SQL
        sql = "SELECT * FROM messages"
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(sql, params)
        rows = cursor.fetchall()

        records = []
        for row in rows:
            records.append(
                MessageRecord(
                    id=row["id"],
                    window_title=row["window_title"],
                    window_handle=row["window_handle"],
                    message_text=row["message_text"],
                    matched_keyword=row["matched_keyword"],
                    screenshot_path=row["screenshot_path"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                )
            )

        return records

    def get_recent_messages(self, minutes: int = 60) -> List[MessageRecord]:
        """
        获取最近N分钟的消息

        参数:
            minutes: 最近多少分钟

        返回:
            消息记录列表
        """
        start_time = datetime.now() - timedelta(minutes=minutes)
        return self.get_messages(start_time=start_time, limit=1000)

    def get_statistics(self) -> Dict:
        """
        获取统计信息

        返回:
            统计字典
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # 总消息数
        cursor.execute("SELECT COUNT(*) as total FROM messages")
        total = cursor.fetchone()["total"]

        # 今日消息数
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        cursor.execute(
            "SELECT COUNT(*) as today FROM messages WHERE created_at >= ?", (today,)
        )
        today_count = cursor.fetchone()["today"]

        # 关键字分布
        cursor.execute("""
            SELECT matched_keyword, COUNT(*) as count 
            FROM messages 
            GROUP BY matched_keyword 
            ORDER BY count DESC
        """)
        keyword_stats = {
            row["matched_keyword"]: row["count"] for row in cursor.fetchall()
        }

        # 窗口分布
        cursor.execute("""
            SELECT window_title, COUNT(*) as count 
            FROM messages 
            GROUP BY window_title 
            ORDER BY count DESC
        """)
        window_stats = {row["window_title"]: row["count"] for row in cursor.fetchall()}

        return {
            "total_messages": total,
            "today_messages": today_count,
            "keyword_distribution": keyword_stats,
            "window_distribution": window_stats,
        }

    def clean_old_data(self, retention_days: int):
        """
        清理过期数据

        参数:
            retention_days: 数据保留天数
        """
        if retention_days <= 0:
            return

        conn = self._get_connection()
        cursor = conn.cursor()

        cutoff_date = datetime.now() - timedelta(days=retention_days)

        cursor.execute("DELETE FROM messages WHERE created_at < ?", (cutoff_date,))

        deleted_count = cursor.rowcount
        conn.commit()

        # 执行VACUUM优化数据库
        cursor.execute("VACUUM")
        conn.commit()

        logger.info(f"清理了 {deleted_count} 条过期数据")

    def check_duplicate(
        self,
        window_title: str,
        message_text: str,
        time_window: int = 60,
        similarity_threshold: float = 0.85,
    ) -> bool:
        """
        检查消息是否重复

        参数:
            window_title: 窗口标题
            message_text: 消息文本
            time_window: 时间窗口（秒）
            similarity_threshold: 相似度阈值

        返回:
            True表示存在重复，False表示不重复
        """
        import difflib

        # 获取时间窗口内的消息
        start_time = datetime.now() - timedelta(seconds=time_window)
        recent_messages = self.get_messages(
            window_title=window_title, start_time=start_time, limit=100
        )

        for record in recent_messages:
            # 计算相似度
            similarity = difflib.SequenceMatcher(
                None, message_text, record.message_text
            ).ratio()

            if similarity >= similarity_threshold:
                return True

        return False

    def get_keywords_from_db(self, enabled_only: bool = False) -> List[str]:
        """从数据库获取关键字列表"""
        conn = self._get_connection()
        cursor = conn.cursor()

        sql = "SELECT word FROM keywords"
        if enabled_only:
            sql += " WHERE enabled = 1"
        sql += " ORDER BY created_at DESC"

        cursor.execute(sql)
        return [row["word"] for row in cursor.fetchall()]

    def update_monitor_status(self, status: str, pid: Optional[int] = None):
        """更新监控服务状态"""
        conn = self._get_connection()
        cursor = conn.cursor()

        if status == "running":
            cursor.execute(
                """
                INSERT OR REPLACE INTO monitor_status
                (id, status, last_heartbeat, started_at, pid, updated_at)
                VALUES (1, ?, CURRENT_TIMESTAMP, COALESCE(
                    (SELECT started_at FROM monitor_status WHERE id = 1), CURRENT_TIMESTAMP
                ), ?, CURRENT_TIMESTAMP)
            """,
                (status, pid),
            )
        else:
            cursor.execute(
                """
                UPDATE monitor_status
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = 1
            """,
                (status,),
            )

        conn.commit()

    def heartbeat(self):
        """更新心跳时间"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE monitor_status SET last_heartbeat = CURRENT_TIMESTAMP WHERE id = 1"
        )
        conn.commit()

    def close(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("数据库连接已关闭")

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()
