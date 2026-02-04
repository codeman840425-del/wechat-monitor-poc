#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能监控模块
用于监控系统性能指标、数据库查询性能、内存使用等

特性：
1. 监控数据库查询性能
2. 内存使用监控
3. 消息处理速率统计
4. 性能告警
"""

import time
import logging
import functools
import psutil
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from collections import deque

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """性能指标数据类"""

    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    db_query_count: int = 0
    db_query_time_ms: float = 0.0
    messages_processed: int = 0
    messages_per_second: float = 0.0


class PerformanceMonitor:
    """性能监控器"""

    def __init__(self, max_history: int = 1000):
        """
        初始化性能监控器

        参数:
            max_history: 最大历史记录数
        """
        self.max_history = max_history
        self.metrics_history: deque = deque(maxlen=max_history)
        self.db_query_times: deque = deque(maxlen=100)
        self.message_times: deque = deque(maxlen=100)

        # 统计计数器
        self.total_db_queries = 0
        self.total_db_time = 0.0
        self.total_messages = 0

        # 进程信息
        self.process = psutil.Process(os.getpid())

        logger.info("性能监控器初始化完成")

    def record_db_query(self, query_time_ms: float):
        """记录数据库查询时间"""
        self.db_query_times.append(query_time_ms)
        self.total_db_queries += 1
        self.total_db_time += query_time_ms

    def record_message_processed(self):
        """记录消息处理"""
        self.message_times.append(time.time())
        self.total_messages += 1

    def get_current_metrics(self) -> PerformanceMetrics:
        """获取当前性能指标"""
        try:
            # CPU和内存使用
            cpu_percent = self.process.cpu_percent(interval=0.1)
            memory_info = self.process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            memory_percent = self.process.memory_percent()

            # 计算消息处理速率（最近1分钟）
            now = time.time()
            one_minute_ago = now - 60
            recent_messages = sum(1 for t in self.message_times if t > one_minute_ago)
            messages_per_second = recent_messages / 60.0

            # 数据库查询统计（最近100次）
            recent_db_queries = len(self.db_query_times)
            recent_db_time = sum(self.db_query_times) if self.db_query_times else 0.0

            metrics = PerformanceMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_mb=memory_mb,
                db_query_count=recent_db_queries,
                db_query_time_ms=recent_db_time,
                messages_processed=recent_messages,
                messages_per_second=messages_per_second,
            )

            self.metrics_history.append(metrics)
            return metrics

        except Exception as e:
            logger.error(f"获取性能指标失败: {e}")
            return PerformanceMetrics(
                timestamp=datetime.now(),
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_mb=0.0,
            )

    def get_stats(self) -> Dict:
        """获取统计信息"""
        metrics = self.get_current_metrics()

        # 计算平均查询时间
        avg_query_time = (
            self.total_db_time / self.total_db_queries
            if self.total_db_queries > 0
            else 0
        )

        return {
            "current": {
                "cpu_percent": round(metrics.cpu_percent, 2),
                "memory_percent": round(metrics.memory_percent, 2),
                "memory_mb": round(metrics.memory_mb, 2),
                "messages_per_second": round(metrics.messages_per_second, 2),
            },
            "total": {
                "db_queries": self.total_db_queries,
                "avg_query_time_ms": round(avg_query_time, 2),
                "messages_processed": self.total_messages,
            },
            "history_count": len(self.metrics_history),
        }

    def check_performance_issues(self) -> List[str]:
        """检查性能问题，返回告警列表"""
        alerts = []
        metrics = self.get_current_metrics()

        # CPU使用过高
        if metrics.cpu_percent > 80:
            alerts.append(f"CPU使用过高: {metrics.cpu_percent:.1f}%")

        # 内存使用过高
        if metrics.memory_percent > 80:
            alerts.append(f"内存使用过高: {metrics.memory_percent:.1f}%")

        # 数据库查询过慢
        if self.db_query_times:
            avg_time = sum(self.db_query_times) / len(self.db_query_times)
            if avg_time > 100:  # 100ms
                alerts.append(f"数据库查询缓慢: 平均{avg_time:.1f}ms")

        return alerts


def monitor_performance(func: Callable) -> Callable:
    """性能监控装饰器"""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            elapsed_ms = (time.time() - start_time) * 1000
            logger.debug(f"{func.__name__} 执行时间: {elapsed_ms:.2f}ms")

    return wrapper


# 全局性能监控实例
_performance_monitor: Optional[PerformanceMonitor] = None


def init_performance_monitor() -> PerformanceMonitor:
    """初始化全局性能监控器"""
    global _performance_monitor
    _performance_monitor = PerformanceMonitor()
    return _performance_monitor


def get_performance_monitor() -> Optional[PerformanceMonitor]:
    """获取全局性能监控器"""
    return _performance_monitor


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)

    monitor = init_performance_monitor()

    # 模拟一些操作
    for i in range(10):
        monitor.record_db_query(50.0 + i * 10)
        monitor.record_message_processed()
        time.sleep(0.1)

    # 获取统计
    stats = monitor.get_stats()
    print("性能统计:", stats)

    # 检查告警
    alerts = monitor.check_performance_issues()
    if alerts:
        print("性能告警:", alerts)
    else:
        print("系统运行正常")
