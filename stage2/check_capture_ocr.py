#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
后台截图和OCR能力自检报告
生成详细的自检报告，包括截图能力和OCR识别能力
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from PIL import Image, ImageStat
import pytesseract


def check_background_capture():
    """检查后台截图能力"""
    results = {
        "module_available": False,
        "win32_available": False,
        "window_found": False,
        "capture_success": False,
        "image_valid": False,
        "details": {},
    }

    try:
        from background_capture import BackgroundCapture, WIN32_AVAILABLE

        results["module_available"] = True
        results["win32_available"] = WIN32_AVAILABLE

        if not WIN32_AVAILABLE:
            results["details"]["error"] = "Win32 API不可用"
            return results

        # 查找微信窗口
        hwnd = BackgroundCapture.find_window("微信")
        if not hwnd:
            hwnd = BackgroundCapture.find_window("WeChat")

        if hwnd:
            results["window_found"] = True
            results["details"]["window_handle"] = hwnd

            # 尝试截图
            capture = BackgroundCapture(hwnd)
            image = capture.capture()

            if image:
                results["capture_success"] = True
                results["details"]["image_size"] = image.size

                # 检查图像有效性
                stat = ImageStat.Stat(image)
                mean_brightness = sum(stat.mean) / len(stat.mean)
                std_dev = sum(stat.stddev) / len(stat.stddev)

                results["details"]["mean_brightness"] = round(mean_brightness, 2)
                results["details"]["std_dev"] = round(std_dev, 2)

                # 判断图像是否有效
                if mean_brightness > 20 and std_dev > 10:
                    results["image_valid"] = True
                    results["details"]["status"] = "截图正常"
                elif mean_brightness < 10:
                    results["details"]["status"] = "截图可能是黑屏（硬件加速）"
                else:
                    results["details"]["status"] = "截图内容可能不完整"
            else:
                results["details"]["error"] = "截图返回None"
        else:
            results["details"]["error"] = "未找到微信窗口"

    except Exception as e:
        results["details"]["error"] = str(e)

    return results


def check_ocr_capability():
    """检查OCR能力"""
    results = {
        "tesseract_available": False,
        "language_available": False,
        "recognition_test": False,
        "details": {},
    }

    try:
        # 检查Tesseract
        version = pytesseract.get_tesseract_version()
        results["tesseract_available"] = True
        results["details"]["version"] = str(version)

        # 检查语言包
        langs = pytesseract.get_languages()
        if "chi_sim" in langs:
            results["language_available"] = True
            results["details"]["languages"] = langs
        else:
            results["details"]["warning"] = "缺少中文语言包(chi_sim)"

        # 测试识别（如果截图成功）
        from background_capture import BackgroundCapture

        hwnd = BackgroundCapture.find_window("微信")
        if hwnd:
            capture = BackgroundCapture(hwnd)
            image = capture.capture()
            if image:
                text = pytesseract.image_to_string(image, lang="chi_sim+eng")
                results["recognition_test"] = True
                results["details"]["text_length"] = len(text)
                results["details"]["chinese_chars"] = len(
                    [c for c in text if "\u4e00" <= c <= "\u9fff"]
                )
                results["details"]["preview"] = text[:200] if len(text) > 200 else text

    except Exception as e:
        results["details"]["error"] = str(e)

    return results


def generate_report():
    """生成自检报告"""
    print("=" * 70)
    print("后台截图和OCR能力自检报告")
    print("=" * 70)
    print(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 1. 后台截图检查
    print("【1. 后台截图能力检查】")
    print("-" * 70)
    capture_results = check_background_capture()

    print(
        f"模块可用性: {'✅ 通过' if capture_results['module_available'] else '❌ 失败'}"
    )
    print(
        f"Win32 API: {'✅ 可用' if capture_results['win32_available'] else '❌ 不可用'}"
    )
    print(f"窗口查找: {'✅ 找到' if capture_results['window_found'] else '❌ 未找到'}")
    print(f"截图功能: {'✅ 成功' if capture_results['capture_success'] else '❌ 失败'}")
    print(f"图像有效性: {'✅ 正常' if capture_results['image_valid'] else '⚠️ 异常'}")

    if capture_results["details"]:
        print("\n详细信息:")
        for key, value in capture_results["details"].items():
            print(f"  - {key}: {value}")

    print()

    # 2. OCR检查
    print("【2. OCR识别能力检查】")
    print("-" * 70)
    ocr_results = check_ocr_capability()

    print(
        f"Tesseract: {'✅ 已安装' if ocr_results['tesseract_available'] else '❌ 未安装'}"
    )
    if ocr_results["tesseract_available"]:
        print(f"  版本: {ocr_results['details'].get('version', '未知')}")

    print(
        f"中文语言包: {'✅ 已安装' if ocr_results['language_available'] else '⚠️ 未安装'}"
    )
    if ocr_results["language_available"]:
        langs = ocr_results["details"].get("languages", [])
        print(f"  可用语言: {', '.join(langs[:5])}...")

    print(f"识别测试: {'✅ 通过' if ocr_results['recognition_test'] else '⚠️ 未测试'}")
    if ocr_results["recognition_test"]:
        print(f"  识别字符数: {ocr_results['details'].get('text_length', 0)}")
        print(f"  中文字符数: {ocr_results['details'].get('chinese_chars', 0)}")

    print()

    # 3. 总体评估
    print("【3. 总体评估】")
    print("-" * 70)

    score = 0
    max_score = 5

    if capture_results["module_available"]:
        score += 1
    if capture_results["win32_available"]:
        score += 1
    if capture_results["capture_success"]:
        score += 1
    if ocr_results["tesseract_available"]:
        score += 1
    if ocr_results["recognition_test"]:
        score += 1

    percentage = (score / max_score) * 100

    if percentage >= 100:
        status = "✅ 优秀 - 所有功能正常"
    elif percentage >= 80:
        status = "✅ 良好 - 核心功能正常"
    elif percentage >= 60:
        status = "⚠️ 一般 - 部分功能受限"
    else:
        status = "❌ 较差 - 需要修复"

    print(f"评分: {score}/{max_score} ({percentage:.0f}%)")
    print(f"状态: {status}")

    # 4. 建议
    print("\n【4. 建议】")
    print("-" * 70)

    if not capture_results["window_found"]:
        print("• 请确保微信已启动并登录")

    if capture_results["capture_success"] and not capture_results["image_valid"]:
        print("• 截图返回黑屏，这是已知问题（微信使用硬件加速）")
        print("• 建议：保持微信窗口可见，使用前台截图")

    if not ocr_results["language_available"]:
        print("• 建议安装Tesseract中文语言包:")
        print("  下载: https://github.com/UB-Mannheim/tesseract/wiki")
        print("  安装时勾选 Chinese (Simplified) 语言包")

    if score >= 4:
        print("• 系统截图和OCR能力良好，可以正常使用")

    print()
    print("=" * 70)
    print("报告生成完成")
    print("=" * 70)


if __name__ == "__main__":
    generate_report()
