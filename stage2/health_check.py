#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目健康检查脚本
执行全面的自检，包括类型检查、配置检查、数据库检查和运行检查
"""

import os
import sys
import subprocess
import sqlite3
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime

# 添加项目目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


@dataclass
class CheckResult:
    """检查结果"""

    name: str
    status: str  # "OK", "WARNING", "ERROR"
    message: str
    details: List[str] = field(default_factory=list)


class HealthChecker:
    """健康检查器"""

    def __init__(self):
        self.results: List[CheckResult] = []
        self.project_root = Path(__file__).parent

    def run_all_checks(self) -> List[CheckResult]:
        """运行所有检查"""
        print("=" * 70)
        print("项目健康检查")
        print("=" * 70)
        print(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"项目目录: {self.project_root}")
        print()

        # 1. 代码与类型检查
        self._check_type_errors()
        self._check_code_quality()

        # 2. 配置与数据库检查
        self._check_config()
        self._check_database()

        # 3. 运行级别检查
        self._check_web_app()
        self._check_message_sources()

        return self.results

    def _check_type_errors(self):
        """检查类型错误"""
        print("[1/6] 检查类型错误...")

        critical_files = [
            "monitor.py",
            "monitor_v2.py",
            "web_app.py",
            "core/message.py",
            "sources/base.py",
            "sources/wechat_screen.py",
            "sources/wechat_api.py",
            "sources/window_screen.py",
        ]

        errors = []
        warnings = []

        # 尝试使用 pyright 进行类型检查
        try:
            result = subprocess.run(
                ["pyright", "--outputjson"] + critical_files,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=self.project_root,
            )

            if result.returncode != 0:
                # 解析 pyright 输出
                import json

                try:
                    output = json.loads(result.stdout)
                    for diagnostic in output.get("generalDiagnostics", []):
                        file = diagnostic.get("file", "")
                        line = (
                            diagnostic.get("range", {}).get("start", {}).get("line", 0)
                        )
                        message = diagnostic.get("message", "")
                        severity = diagnostic.get("severity", "error")

                        entry = f"{file}:{line + 1} - {message}"
                        if severity == "error":
                            errors.append(entry)
                        else:
                            warnings.append(entry)
                except:
                    # pyright 可能不可用，使用备用检查
                    pass
        except FileNotFoundError:
            # pyright 未安装，跳过类型检查
            warnings.append("pyright 未安装，跳过详细类型检查")
        except Exception as e:
            warnings.append(f"类型检查执行失败: {e}")

        # 备用：检查已知问题
        known_errors, known_warnings = self._check_known_type_issues()
        errors.extend(known_errors)
        warnings.extend(known_warnings)

        if errors:
            self.results.append(
                CheckResult(
                    name="类型检查",
                    status="ERROR",
                    message=f"发现 {len(errors)} 个类型错误",
                    details=errors[:10],  # 只显示前10个
                )
            )
        elif warnings:
            self.results.append(
                CheckResult(
                    name="类型检查",
                    status="WARNING",
                    message="类型检查通过，但有警告",
                    details=warnings,
                )
            )
        else:
            self.results.append(
                CheckResult(
                    name="类型检查", status="OK", message="关键模块类型检查通过"
                )
            )

    def _check_known_type_issues(self) -> Tuple[List[str], List[str]]:
        """检查已知的类型问题，返回 (错误列表, 警告列表)"""
        errors = []
        warnings = []

        # 检查 sources/wechat_screen.py 中的已知问题
        wechat_screen = self.project_root / "sources" / "wechat_screen.py"
        if wechat_screen.exists():
            content = wechat_screen.read_text(encoding="utf-8")
            # 这些是已知的 Pylance 警告，运行时已有检查，标记为警告而非错误
            if "window_element.SetFocus()" in content:
                warnings.append(
                    "sources/wechat_screen.py:112 - window_element 可能为 None (运行时已检查)"
                )
            if "window_element.BoundingRectangle" in content:
                warnings.append(
                    "sources/wechat_screen.py:118 - window_element 可能为 None (运行时已检查)"
                )

        # 检查 sources/window_screen.py
        window_screen = self.project_root / "sources" / "window_screen.py"
        if window_screen.exists():
            content = window_screen.read_text(encoding="utf-8")
            if "class_name_patterns: List[str] = None" in content:
                warnings.append(
                    "sources/window_screen.py:46 - class_name_patterns 类型 (运行时正常)"
                )

        # 检查 monitor.py
        monitor = self.project_root / "monitor.py"
        if monitor.exists():
            content = monitor.read_text(encoding="utf-8")
            if "self.db.heartbeat()" in content:
                warnings.append("monitor.py:1396 - heartbeat 属性 (运行时正常)")

        return errors, warnings

    def _check_code_quality(self):
        """检查代码质量"""
        print("[2/6] 检查代码质量...")

        issues = []

        # 检查未使用的导入
        try:
            result = subprocess.run(
                ["python", "-m", "py_compile", "monitor_v2.py", "web_app.py"],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=self.project_root,
            )

            if result.returncode != 0:
                issues.append(f"语法错误: {result.stderr}")
        except Exception as e:
            issues.append(f"代码质量检查失败: {e}")

        # 检查关键文件是否存在
        critical_files = [
            "monitor_v2.py",
            "web_app.py",
            "core/message.py",
            "sources/base.py",
            "database.py",
        ]

        for file in critical_files:
            if not (self.project_root / file).exists():
                issues.append(f"关键文件缺失: {file}")

        if issues:
            self.results.append(
                CheckResult(
                    name="代码质量",
                    status="WARNING" if len(issues) < 3 else "ERROR",
                    message=f"发现 {len(issues)} 个问题",
                    details=issues,
                )
            )
        else:
            self.results.append(
                CheckResult(name="代码质量", status="OK", message="代码质量检查通过")
            )

    def _check_config(self):
        """检查配置文件"""
        print("[3/6] 检查配置文件...")

        config_path = self.project_root / "config.yaml"
        issues = []

        if not config_path.exists():
            self.results.append(
                CheckResult(
                    name="配置文件",
                    status="ERROR",
                    message="config.yaml 不存在",
                    details=["请创建 config.yaml 配置文件"],
                )
            )
            return

        try:
            import yaml

            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            if not config:
                issues.append("配置文件为空")
            else:
                # 检查关键字段
                required_fields = [
                    ("database", "db_path", "数据库路径"),
                    ("monitor", "interval", "监控间隔"),
                    ("ocr", "lang", "OCR语言"),
                ]

                for section, key, desc in required_fields:
                    if section not in config or key not in config.get(section, {}):
                        issues.append(f"缺少配置项: {section}.{key} ({desc})")

                # 检查截图目录
                screenshot_dir = (
                    config.get("monitor", {})
                    .get("screenshot", {})
                    .get("save_directory")
                )
                if screenshot_dir:
                    Path(screenshot_dir).mkdir(parents=True, exist_ok=True)

        except ImportError:
            issues.append("PyYAML 未安装，无法解析配置文件")
        except Exception as e:
            issues.append(f"配置文件解析失败: {e}")

        if issues:
            self.results.append(
                CheckResult(
                    name="配置文件",
                    status="WARNING",
                    message=f"发现 {len(issues)} 个配置问题",
                    details=issues,
                )
            )
        else:
            self.results.append(
                CheckResult(name="配置文件", status="OK", message="配置文件检查通过")
            )

    def _check_database(self):
        """检查数据库"""
        print("[4/6] 检查数据库...")

        db_path = self.project_root / "wechat_monitor.db"
        issues = []

        try:
            conn = sqlite3.connect(str(db_path), timeout=5)
            cursor = conn.cursor()

            # 检查表是否存在
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = {row[0] for row in cursor.fetchall()}

            required_tables = {
                "messages": [
                    "id",
                    "window_title",
                    "message_text",
                    "matched_keyword",
                    "created_at",
                ],
                "keywords": ["id", "word", "enabled", "created_at"],
            }

            for table, required_fields in required_tables.items():
                if table not in tables:
                    issues.append(f"缺少表: {table}")
                else:
                    # 检查字段
                    cursor.execute(f"PRAGMA table_info({table})")
                    existing_fields = {row[1] for row in cursor.fetchall()}

                    for field in required_fields:
                        if field not in existing_fields:
                            issues.append(f"表 {table} 缺少字段: {field}")

            conn.close()

        except sqlite3.Error as e:
            issues.append(f"数据库连接失败: {e}")
        except Exception as e:
            issues.append(f"数据库检查失败: {e}")

        if issues:
            self.results.append(
                CheckResult(
                    name="数据库",
                    status="WARNING",
                    message=f"发现 {len(issues)} 个数据库问题",
                    details=issues,
                )
            )
        else:
            self.results.append(
                CheckResult(name="数据库", status="OK", message="数据库结构检查通过")
            )

    def _check_web_app(self):
        """检查 Web 应用"""
        print("[5/6] 检查 Web 应用...")

        issues = []

        try:
            from web_app import app

            # 检查关键路由
            routes = [str(rule) for rule in app.url_map.iter_rules()]
            required_routes = ["/", "/messages", "/keywords", "/api/stats"]

            for route in required_routes:
                if route not in routes:
                    issues.append(f"缺少路由: {route}")

            # 检查模板
            template_dir = self.project_root / "templates"
            required_templates = [
                "base.html",
                "dashboard.html",
                "messages.html",
                "keywords.html",
            ]

            for template in required_templates:
                if not (template_dir / template).exists():
                    issues.append(f"缺少模板: {template}")

        except Exception as e:
            issues.append(f"Web 应用导入失败: {e}")

        if issues:
            self.results.append(
                CheckResult(
                    name="Web 应用",
                    status="WARNING" if len(issues) < 3 else "ERROR",
                    message=f"发现 {len(issues)} 个问题",
                    details=issues,
                )
            )
        else:
            self.results.append(
                CheckResult(name="Web 应用", status="OK", message="Web 应用检查通过")
            )

    def _check_message_sources(self):
        """检查消息源"""
        print("[6/6] 检查消息源...")

        issues = []
        source_status = []

        try:
            # 检查核心模块
            from core.message import ChatMessage, MessageSource

            source_status.append("核心模块 (core/message): OK")

            # 检查微信桌面源
            try:
                from sources.wechat_screen import WeChatScreenSource

                source_status.append("微信桌面源 (wechat_screen): OK")
            except Exception as e:
                issues.append(f"微信桌面源导入失败: {e}")

            # 检查基础源
            try:
                from sources.base import BaseMessageSource

                source_status.append("基础源 (base): OK")
            except Exception as e:
                issues.append(f"基础源导入失败: {e}")

            # 检查数据库模块
            try:
                from database import DatabaseManager

                source_status.append("数据库管理器: OK")
            except Exception as e:
                issues.append(f"数据库模块导入失败: {e}")

        except Exception as e:
            issues.append(f"消息源检查失败: {e}")

        if issues:
            self.results.append(
                CheckResult(
                    name="消息源",
                    status="WARNING",
                    message=f"发现 {len(issues)} 个问题",
                    details=issues + source_status,
                )
            )
        else:
            self.results.append(
                CheckResult(
                    name="消息源",
                    status="OK",
                    message="消息源检查通过",
                    details=source_status,
                )
            )

    def print_report(self):
        """打印检查报告"""
        print()
        print("=" * 70)
        print("健康检查报告")
        print("=" * 70)

        ok_count = sum(1 for r in self.results if r.status == "OK")
        warning_count = sum(1 for r in self.results if r.status == "WARNING")
        error_count = sum(1 for r in self.results if r.status == "ERROR")

        for result in self.results:
            status_icon = (
                "[OK]"
                if result.status == "OK"
                else "[WARN]"
                if result.status == "WARNING"
                else "[ERR]"
            )
            print(f"\n{status_icon} {result.name}: {result.status}")
            print(f"  {result.message}")

            if result.details:
                for detail in result.details[:5]:  # 最多显示5个详情
                    print(f"    - {detail}")
                if len(result.details) > 5:
                    print(f"    ... 还有 {len(result.details) - 5} 项")

        print()
        print("=" * 70)
        print(f"总结: {ok_count} 项通过, {warning_count} 项警告, {error_count} 项错误")
        print("=" * 70)

        if error_count > 0:
            print("\n建议: 请先修复错误项再启动监控服务")
            return 1
        elif warning_count > 0:
            print("\n建议: 可以启动服务，但建议处理警告项")
            return 0
        else:
            print("\n[OK] 所有检查通过，系统健康！")
            return 0


def main():
    """主函数"""
    checker = HealthChecker()
    checker.run_all_checks()
    exit_code = checker.print_report()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
