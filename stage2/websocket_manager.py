#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebSocket 实时推送模块
用于向Web界面实时推送新消息

特性：
1. 基于 Flask-SocketIO
2. 支持多客户端连接
3. 断线自动重连
4. 消息广播

作者：AI Assistant
日期：2026年
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

try:
    from flask_socketio import SocketIO, emit, broadcast

    SOCKETIO_AVAILABLE = True
except ImportError:
    SOCKETIO_AVAILABLE = False
    logging.warning("flask-socketio 未安装，WebSocket功能不可用")

from database import MessageRecord

logger = logging.getLogger(__name__)


class WebSocketManager:
    """WebSocket管理器"""

    def __init__(self, app=None, cors_allowed_origins="*"):
        """
        初始化WebSocket管理器

        参数:
            app: Flask应用实例
            cors_allowed_origins: 允许的跨域来源
        """
        if not SOCKETIO_AVAILABLE:
            raise RuntimeError("flask-socketio 未安装")

        self.socketio = SocketIO(
            app,
            cors_allowed_origins=cors_allowed_origins,
            async_mode="threading",
            logger=False,
            engineio_logger=False,
        )

        self.connected_clients: Dict[str, Dict[str, Any]] = {}
        self._setup_handlers()

        logger.info("WebSocket管理器初始化完成")

    def _setup_handlers(self):
        """设置事件处理器"""

        @self.socketio.on("connect")
        def handle_connect():
            """客户端连接"""
            from flask import request

            sid = request.sid
            self.connected_clients[sid] = {
                "connected_at": datetime.now(),
                "ip": request.remote_addr,
            }
            logger.info(f"WebSocket客户端连接: {sid} from {request.remote_addr}")
            emit("connected", {"status": "ok", "message": "连接成功"})

        @self.socketio.on("disconnect")
        def handle_disconnect():
            """客户端断开"""
            from flask import request

            sid = request.sid
            if sid in self.connected_clients:
                del self.connected_clients[sid]
            logger.info(f"WebSocket客户端断开: {sid}")

        @self.socketio.on("subscribe")
        def handle_subscribe(data):
            """客户端订阅频道"""
            from flask import request

            sid = request.sid
            channel = data.get("channel", "all")

            if sid in self.connected_clients:
                if "subscriptions" not in self.connected_clients[sid]:
                    self.connected_clients[sid]["subscriptions"] = []
                self.connected_clients[sid]["subscriptions"].append(channel)

            logger.info(f"客户端 {sid} 订阅频道: {channel}")
            emit("subscribed", {"channel": channel, "status": "ok"})

        @self.socketio.on("ping")
        def handle_ping():
            """心跳检测"""
            emit("pong", {"timestamp": datetime.now().isoformat()})

    def broadcast_message(self, message: MessageRecord):
        """
        广播新消息到所有连接的客户端

        参数:
            message: 消息记录
        """
        if not self.connected_clients:
            return

        try:
            data = {
                "id": message.id,
                "window_title": message.window_title,
                "message_text": message.message_text,
                "matched_keyword": message.matched_keyword,
                "screenshot_path": message.screenshot_path,
                "created_at": message.created_at.isoformat()
                if message.created_at
                else None,
            }

            self.socketio.emit("new_message", data, broadcast=True)
            logger.debug(f"消息已广播到 {len(self.connected_clients)} 个客户端")

        except Exception as e:
            logger.error(f"广播消息失败: {e}")

    def broadcast_notification(
        self, title: str, content: str, notification_type: str = "info"
    ):
        """
        广播通知

        参数:
            title: 通知标题
            content: 通知内容
            notification_type: 通知类型 (info, warning, error, success)
        """
        if not self.connected_clients:
            return

        try:
            data = {
                "title": title,
                "content": content,
                "type": notification_type,
                "timestamp": datetime.now().isoformat(),
            }

            self.socketio.emit("notification", data, broadcast=True)
            logger.debug(f"通知已广播: {title}")

        except Exception as e:
            logger.error(f"广播通知失败: {e}")

    def broadcast_stats(self, stats: Dict[str, Any]):
        """
        广播统计信息

        参数:
            stats: 统计数据字典
        """
        if not self.connected_clients:
            return

        try:
            self.socketio.emit("stats_update", stats, broadcast=True)
        except Exception as e:
            logger.error(f"广播统计信息失败: {e}")

    def get_connection_count(self) -> int:
        """获取当前连接数"""
        return len(self.connected_clients)

    def get_client_info(self) -> List[Dict[str, Any]]:
        """获取客户端信息列表"""
        return [
            {
                "sid": sid,
                "connected_at": info.get("connected_at").isoformat()
                if info.get("connected_at")
                else None,
                "ip": info.get("ip"),
                "subscriptions": info.get("subscriptions", []),
            }
            for sid, info in self.connected_clients.items()
        ]

    def run(self, host="0.0.0.0", port=5000, debug=False):
        """运行WebSocket服务"""
        logger.info(f"启动WebSocket服务: {host}:{port}")
        self.socketio.run(self.socketio.server, host=host, port=port, debug=debug)


# 全局WebSocket管理器实例
_ws_manager: Optional[WebSocketManager] = None


def init_websocket_manager(app=None) -> Optional[WebSocketManager]:
    """初始化全局WebSocket管理器"""
    global _ws_manager

    if not SOCKETIO_AVAILABLE:
        logger.warning("flask-socketio 未安装，跳过WebSocket初始化")
        return None

    _ws_manager = WebSocketManager(app)
    return _ws_manager


def get_websocket_manager() -> Optional[WebSocketManager]:
    """获取全局WebSocket管理器"""
    return _ws_manager


def broadcast_message(message: MessageRecord):
    """快捷广播消息"""
    manager = get_websocket_manager()
    if manager:
        manager.broadcast_message(message)


def broadcast_notification(title: str, content: str, notification_type: str = "info"):
    """快捷广播通知"""
    manager = get_websocket_manager()
    if manager:
        manager.broadcast_notification(title, content, notification_type)


# 测试代码
if __name__ == "__main__":
    from flask import Flask

    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    if not SOCKETIO_AVAILABLE:
        print("错误: flask-socketio 未安装")
        print("请运行: pip install flask-socketio")
        exit(1)

    # 创建Flask应用
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "test-secret-key"

    # 初始化WebSocket
    ws_manager = init_websocket_manager(app)

    @app.route("/")
    def index():
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>WebSocket测试</title>
            <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
            <script>
                const socket = io();
                
                socket.on('connect', function() {
                    console.log('已连接');
                    document.getElementById('status').innerHTML = '已连接';
                    socket.emit('subscribe', {channel: 'messages'});
                });
                
                socket.on('disconnect', function() {
                    console.log('已断开');
                    document.getElementById('status').innerHTML = '已断开';
                });
                
                socket.on('new_message', function(data) {
                    console.log('新消息:', data);
                    const div = document.createElement('div');
                    div.innerHTML = `<hr><p><strong>${data.matched_keyword}</strong>: ${data.message_text}</p>`;
                    document.getElementById('messages').appendChild(div);
                });
                
                socket.on('notification', function(data) {
                    console.log('通知:', data);
                    alert(`[${data.type}] ${data.title}: ${data.content}`);
                });
            </script>
        </head>
        <body>
            <h1>WebSocket实时推送测试</h1>
            <p>状态: <span id="status">连接中...</span></p>
            <div id="messages"></div>
        </body>
        </html>
        """

    print("=" * 60)
    print("WebSocket测试服务器")
    print("=" * 60)
    print("访问: http://127.0.0.1:5000")
    print("按 Ctrl+C 停止")
    print("=" * 60)

    # 启动服务
    ws_manager.run(host="127.0.0.1", port=5000, debug=True)
