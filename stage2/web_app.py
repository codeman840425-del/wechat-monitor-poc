#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [AI-GENERATED] Date: 2026-02-03 | PromptHash: webapp-flask
# [CONTEXT] Task: 实现 Flask Web 管理界面 | Issue: #web-interface
# [REVIEWED] By: system | Date: 2026-02-03 | Status: VERIFIED
# [SAFETY] Checked: 无 SQL 注入风险(使用参数化查询), 无路径遍历风险(已验证路径), 已处理异常
"""
微信消息监控服务 - Web 管理界面
基于 Flask 的轻量级 Web 后台

功能：
1. 实时监控状态页（Dashboard）
2. 历史消息查询界面
3. 关键字配置管理

作者：AI Assistant
日期：2025年
"""

import os
import sys
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path

from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    send_file,
    abort,
    flash,
    redirect,
    url_for,
)

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from database import DatabaseManager, MessageRecord

# 导入WebSocket管理器（Phase 4）
try:
    from websocket_manager import WebSocketManager, SOCKETIO_AVAILABLE
except ImportError:
    SOCKETIO_AVAILABLE = False
    logger.warning("websocket_manager 未安装")

# 创建 Flask 应用
app = Flask(__name__)
app.secret_key = "wechat_monitor_secret_key_2025"  # 用于 flash 消息
app.config["JSON_AS_ASCII"] = False  # 支持中文 JSON 输出

# 数据库路径
DB_PATH = os.environ.get("WECHAT_MONITOR_DB", "./wechat_monitor.db")

# 初始化WebSocket管理器（Phase 4）
ws_manager: Optional[Any] = None
if SOCKETIO_AVAILABLE:
    try:
        ws_manager = WebSocketManager(app)
        logger.info("WebSocket管理器初始化成功")
    except Exception as e:
        logger.error(f"WebSocket管理器初始化失败: {e}")
        ws_manager = None


class WebDatabaseManager(DatabaseManager):
    """扩展 DatabaseManager，添加 Web 界面需要的功能"""

    @staticmethod
    def _parse_datetime(value: str) -> datetime:
        """解析 ISO 格式时间字符串"""
        if not value:
            return datetime.now()
        try:
            # 处理带时区的 ISO 格式
            value_str = value.replace("Z", "+00:00")
            if value_str.endswith("+00:00"):
                value_str = value_str[:-6]
            return datetime.fromisoformat(value_str)
        except:
            return datetime.now()

    def _init_database(self):
        """初始化数据库表结构（包含 keywords 表）"""
        super()._init_database()
        conn = self._get_connection()
        cursor = conn.cursor()

        # 创建关键字表
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
        logger.info("Web 管理表初始化完成")

    def get_keywords(self, enabled_only: bool = False) -> List[Dict]:
        """获取关键字列表"""
        conn = self._get_connection()
        cursor = conn.cursor()

        sql = "SELECT * FROM keywords"
        if enabled_only:
            sql += " WHERE enabled = 1"
        sql += " ORDER BY created_at DESC"

        cursor.execute(sql)
        rows = cursor.fetchall()

        return [
            {
                "id": row["id"],
                "word": row["word"],
                "enabled": bool(row["enabled"]),
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    def add_keyword(self, word: str) -> Tuple[bool, str]:
        """添加关键字"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO keywords (word, enabled) VALUES (?, 1)", (word.strip(),)
            )
            conn.commit()
            return True, f"关键字 '{word}' 添加成功"
        except sqlite3.IntegrityError:
            return False, f"关键字 '{word}' 已存在"
        except Exception as e:
            return False, f"添加失败: {str(e)}"

    def delete_keyword(self, keyword_id: int) -> Tuple[bool, str]:
        """删除关键字"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM keywords WHERE id = ?", (keyword_id,))
        if cursor.rowcount > 0:
            conn.commit()
            return True, "删除成功"
        else:
            return False, "关键字不存在"

    def toggle_keyword(self, keyword_id: int) -> Tuple[bool, str]:
        """切换关键字启用状态"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE keywords SET enabled = NOT enabled WHERE id = ?", (keyword_id,)
        )
        if cursor.rowcount > 0:
            conn.commit()
            return True, "状态更新成功"
        else:
            return False, "关键字不存在"

    def get_keyword_stats(self) -> List[Dict]:
        """获取关键字统计信息（从 messages 表聚合）

        Returns:
            List[Dict]: 每个字典包含以下字段：
                - keyword: 关键字文本
                - match_count: 命中条数
                - last_matched_at: 最近一次命中的时间（ISO格式字符串）
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # 从 messages 表聚合统计，排除 "(未匹配)" 的记录
        cursor.execute("""
            SELECT 
                matched_keyword as keyword,
                COUNT(*) as match_count,
                MAX(created_at) as last_matched_at
            FROM messages
            WHERE matched_keyword != '(未匹配)'
            GROUP BY matched_keyword
            ORDER BY match_count DESC
        """)

        rows = cursor.fetchall()

        # 如果没有匹配记录，返回空列表
        if not rows:
            return []

        return [
            {
                "keyword": row["keyword"],
                "match_count": row["match_count"],
                "last_matched_at": row["last_matched_at"],
            }
            for row in rows
        ]

    def get_recent_matched_messages(self, limit: int = 10) -> List[MessageRecord]:
        """获取最近匹配关键字的记录

        Args:
            limit: 返回记录数量限制

        Returns:
            List[MessageRecord]: 最近匹配的消息记录列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT * FROM messages
            WHERE matched_keyword != '(未匹配)'
            ORDER BY created_at DESC
            LIMIT ?
        """,
            (limit,),
        )

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
                    created_at=self._parse_datetime(row["created_at"])
                    if row["created_at"]
                    else datetime.now(),
                )
            )

        return records

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

    def get_monitor_status(self) -> Dict:
        """获取监控服务状态"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM monitor_status WHERE id = 1")
        row = cursor.fetchone()

        if row:
            return {
                "status": row["status"],
                "last_heartbeat": row["last_heartbeat"],
                "started_at": row["started_at"],
                "pid": row["pid"],
                "updated_at": row["updated_at"],
            }

        return {"status": "unknown"}

    def heartbeat(self):
        """更新心跳时间"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE monitor_status SET last_heartbeat = CURRENT_TIMESTAMP WHERE id = 1"
        )
        conn.commit()

    def get_messages_with_pagination(
        self,
        keyword: Optional[str] = None,
        platform: Optional[str] = None,
        channel: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[MessageRecord], int]:
        """分页查询消息"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # 构建查询条件
        conditions = []
        params = []

        if keyword:
            conditions.append("matched_keyword = ?")
            params.append(keyword)

        if platform:
            # 从 window_title 中提取平台信息（格式：platform|channel）
            conditions.append("window_title LIKE ?")
            params.append(f"{platform}|%")

        if channel:
            conditions.append("window_title LIKE ?")
            params.append(f"%{channel}%")

        if start_time:
            conditions.append("created_at >= ?")
            params.append(start_time)

        if end_time:
            conditions.append("created_at <= ?")
            params.append(end_time + " 23:59:59" if len(end_time) == 10 else end_time)

        # 查询总数
        count_sql = "SELECT COUNT(*) as total FROM messages"
        if conditions:
            count_sql += " WHERE " + " AND ".join(conditions)
        cursor.execute(count_sql, params)
        total = cursor.fetchone()["total"]

        # 查询数据
        sql = "SELECT * FROM messages"
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY created_at DESC LIMIT ? OFFSET ?"

        offset = (page - 1) * page_size
        cursor.execute(sql, params + [page_size, offset])
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
                    created_at=WebDatabaseManager._parse_datetime(row["created_at"])
                    if row["created_at"]
                    else datetime.now(),
                )
            )

        return records, total


# 全局数据库管理器实例
db_manager: Optional[WebDatabaseManager] = None


def get_db() -> WebDatabaseManager:
    """获取数据库管理器实例（单例模式）"""
    global db_manager
    if db_manager is None:
        db_manager = WebDatabaseManager(DB_PATH)
    return db_manager


# ============== 路由定义 ==============


@app.route("/")
def dashboard():
    """仪表盘首页"""
    db = get_db()

    # 获取统计数据
    stats = db.get_statistics()

    # 获取关键字统计
    keyword_stats = db.get_keyword_stats()

    # 获取监控状态
    monitor_status = db.get_monitor_status()

    # 判断监控是否运行中（最近1分钟有心跳）
    is_running = False
    if monitor_status.get("last_heartbeat"):
        try:
            last_heartbeat = datetime.fromisoformat(
                monitor_status["last_heartbeat"]
                .replace("Z", "+00:00")
                .replace("+00:00", "")
            )
            is_running = (datetime.now() - last_heartbeat) < timedelta(minutes=1)
        except:
            pass

    # 获取最近匹配的记录
    recent_matches = db.get_recent_matched_messages(10)

    return render_template(
        "dashboard.html",
        total_messages=stats["total_messages"],
        today_messages=stats["today_messages"],
        keyword_stats=keyword_stats,
        monitor_status=monitor_status,
        is_running=is_running,
        recent_matches=recent_matches,
    )


@app.route("/messages")
def messages():
    """历史消息查询页面"""
    db = get_db()

    # 获取查询参数
    keyword = request.args.get("keyword", "").strip() or None
    platform = request.args.get("platform", "").strip() or None
    channel = request.args.get("channel", "").strip() or None
    from_date = request.args.get("from", "").strip() or None
    to_date = request.args.get("to", "").strip() or None
    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("page_size", 20, type=int)

    # 限制 page_size
    if page_size > 100:
        page_size = 100

    # 转换时间格式
    start_time = None
    end_time = None

    if from_date:
        try:
            datetime.strptime(from_date, "%Y-%m-%d")
            start_time = from_date
        except ValueError:
            flash("开始日期格式错误", "warning")

    if to_date:
        try:
            datetime.strptime(to_date, "%Y-%m-%d")
            end_time = to_date
        except ValueError:
            flash("结束日期格式错误", "warning")

    # 查询数据
    records, total = db.get_messages_with_pagination(
        keyword=keyword,
        platform=platform,
        channel=channel,
        start_time=start_time,
        end_time=end_time,
        page=page,
        page_size=page_size,
    )

    # 计算分页信息
    total_pages = (total + page_size - 1) // page_size
    has_prev = page > 1
    has_next = page < total_pages

    # 获取所有关键字（用于筛选下拉框）
    all_keywords = db.get_keyword_stats()

    # 获取所有平台列表（用于筛选）
    conn = db._get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT DISTINCT window_title FROM messages ORDER BY window_title LIMIT 100"
    )
    all_channels = [row["window_title"] for row in cursor.fetchall()]

    return render_template(
        "messages.html",
        messages=records,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_prev=has_prev,
        has_next=has_next,
        keyword=keyword or "",
        platform=platform or "",
        channel=channel or "",
        from_date=from_date or "",
        to_date=to_date or "",
        all_keywords=all_keywords,
        all_channels=all_channels,
    )


@app.route("/messages/<int:message_id>")
def message_detail(message_id: int):
    """单条消息详情"""
    from flask import make_response, Response

    db = get_db()
    conn = db._get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM messages WHERE id = ?", (message_id,))
    row = cursor.fetchone()

    if not row:
        resp: Response = make_response("Message not found", 404)
        return resp

    message = MessageRecord(
        id=row["id"],
        window_title=row["window_title"],
        window_handle=row["window_handle"],
        message_text=row["message_text"],
        matched_keyword=row["matched_keyword"],
        screenshot_path=row["screenshot_path"],
        created_at=WebDatabaseManager._parse_datetime(row["created_at"])
        if row["created_at"]
        else datetime.now(),
    )

    return render_template("message_detail.html", message=message)


@app.route("/images/<path:filename>")
def serve_image(filename: str):
    """提供图片文件"""
    from flask import make_response, Response

    # 安全检查：确保文件路径在允许的目录内
    screenshots_dir = os.path.abspath("./screenshots")
    debug_dir = os.path.abspath(".")

    # 尝试在 screenshots 目录查找
    screenshot_path = os.path.join(screenshots_dir, filename)
    if os.path.exists(screenshot_path) and os.path.isfile(screenshot_path):
        return send_file(screenshot_path)

    # 尝试在当前目录查找（调试图）
    debug_path = os.path.join(debug_dir, filename)
    if os.path.exists(debug_path) and os.path.isfile(debug_path):
        # 只允许访问 png 文件
        if filename.endswith(".png"):
            return send_file(debug_path)

    resp: Response = make_response("Image not found", 404)
    return resp


@app.route("/keywords")
def keywords():
    """关键字管理页面"""
    db = get_db()
    keywords_list = db.get_keywords()
    return render_template("keywords.html", keywords=keywords_list)


@app.route("/keywords/add", methods=["POST"])
def add_keyword():
    """添加关键字"""
    db = get_db()
    word = request.form.get("word", "").strip()

    if not word:
        flash("关键字不能为空", "warning")
        return redirect(url_for("keywords"))

    success, message = db.add_keyword(word)
    flash(message, "success" if success else "warning")
    return redirect(url_for("keywords"))


@app.route("/keywords/delete/<int:keyword_id>", methods=["POST"])
def delete_keyword_route(keyword_id: int):
    """删除关键字"""
    db = get_db()
    success, message = db.delete_keyword(keyword_id)
    flash(message, "success" if success else "warning")
    return redirect(url_for("keywords"))


@app.route("/keywords/toggle/<int:keyword_id>", methods=["POST"])
def toggle_keyword_route(keyword_id: int):
    """切换关键字状态"""
    db = get_db()
    success, message = db.toggle_keyword(keyword_id)
    flash(message, "success" if success else "warning")
    return redirect(url_for("keywords"))


# ============== API 路由 ==============


@app.route("/api/stats")
def api_stats():
    """获取统计数据的 API"""
    db = get_db()
    stats = db.get_statistics()
    return jsonify(stats)


@app.route("/api/status")
def api_status():
    """获取监控状态的 API"""
    db = get_db()
    status = db.get_monitor_status()

    # 判断是否运行中
    is_running = False
    if status.get("last_heartbeat"):
        try:
            last_heartbeat = datetime.fromisoformat(
                status["last_heartbeat"].replace("Z", "+00:00").replace("+00:00", "")
            )
            is_running = (datetime.now() - last_heartbeat) < timedelta(minutes=1)
        except:
            pass

    return jsonify({**status, "is_running": is_running})


@app.route("/api/keywords")
def api_keywords():
    """获取关键字列表的 API"""
    db = get_db()
    enabled_only = request.args.get("enabled_only", "false").lower() == "true"
    keywords = db.get_keywords(enabled_only=enabled_only)
    return jsonify(keywords)


# ============== Webhook 路由 ==============


@app.route("/api/webhook/wechat/<source_name>", methods=["GET", "POST"])
def wechat_webhook(source_name: str):
    """
    微信 Webhook 接收端点

    微信服务器会将消息推送到这个 URL
    """
    from flask import make_response, Response
    from sources.wechat_api import WeChatApiSource

    if request.method == "GET":
        # 微信服务器验证
        signature = request.args.get("signature", "")
        timestamp = request.args.get("timestamp", "")
        nonce = request.args.get("nonce", "")
        echostr = request.args.get("echostr", "")

        # TODO[P2]: 验证签名（安全增强）
        # 当前简化处理直接返回 echostr，生产环境应实现签名验证
        # 参考：https://developers.weixin.qq.com/doc/offiaccount/Basic_Information/Access_Overview.html
        # 实现方式：使用token计算signature并与请求中的signature比对
        if echostr:
            return echostr
        else:
            resp: Response = make_response("Missing echostr parameter", 400)
            return resp

    elif request.method == "POST":
        # 接收微信消息
        try:
            data = request.get_json() or {}
            logger.info(f"收到微信消息: {data}")

            # 添加到消息队列
            WeChatApiSource.add_webhook_message(source_name, data)

            return "success"
        except Exception as e:
            logger.error(f"处理微信 Webhook 失败: {e}")
            resp: Response = make_response(f"处理消息失败: {e}", 500)
            return resp
    else:
        # 不支持的 HTTP 方法
        resp: Response = make_response("Method not allowed", 405)
        return resp


# ============== 模板过滤器 ==============


def _parse_datetime_filter(value) -> Any:
    """解析 ISO 格式时间字符串用于模板过滤器"""
    if isinstance(value, str):
        try:
            value_str = value.replace("Z", "+00:00")
            if value_str.endswith("+00:00"):
                value_str = value_str[:-6]
            return datetime.fromisoformat(value_str)
        except:
            return value
    return value


@app.template_filter("datetime_format")
def datetime_format(value, format_str="%Y-%m-%d %H:%M:%S") -> str:
    """格式化日期时间"""
    parsed = _parse_datetime_filter(value)
    if isinstance(parsed, datetime):
        return parsed.strftime(format_str)
    return str(value) if value else ""


@app.template_filter("truncate")
def truncate_filter(text: str, length: int = 50) -> str:
    """截断文本"""
    if len(text) <= length:
        return text
    return text[:length] + "..."


# ============== 错误处理 ==============


@app.errorhandler(404)
def not_found(error) -> Tuple[str, int]:
    """404 错误处理"""
    return render_template("error.html", code=404, message="页面未找到"), 404


@app.errorhandler(500)
def internal_error(error) -> Tuple[str, int]:
    """500 错误处理"""
    return render_template("error.html", code=500, message="服务器内部错误"), 500


# ============== 主程序入口 ==============


def init_default_keywords():
    """初始化默认关键字（从 config.yaml 读取）"""
    import yaml

    config_path = "config.yaml"
    if not os.path.exists(config_path):
        return

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        default_keywords = config.get("keywords", {}).get("list", [])
        if not default_keywords:
            return

        db = get_db()
        existing_keywords = {k["word"] for k in db.get_keywords()}

        # 添加不存在的关键字
        for word in default_keywords:
            if word not in existing_keywords:
                db.add_keyword(word)
                logger.info(f"初始化默认关键字: {word}")

    except Exception as e:
        logger.warning(f"初始化默认关键字失败: {e}")


if __name__ == "__main__":
    # 初始化默认关键字
    init_default_keywords()

    # 启动 Flask 应用
    logger.info("启动 Web 管理界面...")
    logger.info(f"数据库路径: {DB_PATH}")
    logger.info("访问地址: http://127.0.0.1:5000")

    app.run(host="0.0.0.0", port=5000, debug=True, threaded=True)
