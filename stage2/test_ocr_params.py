#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR预处理参数测试工具
用于测试不同预处理参数对识别效果的影响
"""

import os
import sys
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter, ImageStat
import pytesseract


def preprocess_image(
    image: Image.Image,
    scale: float = 2.0,
    contrast: bool = False,
    contrast_factor: float = 1.2,
    sharpen: bool = False,
) -> Image.Image:
    """OCR前图像预处理"""
    try:
        # 获取原始图像信息
        orig_size = image.size
        print(f"  原始图像尺寸={orig_size}")

        # 1. 转为灰度图（必须步骤）
        img = image.convert("L")

        # 2. 可选：轻度锐化
        if sharpen:
            img = img.filter(ImageFilter.SHARPEN)
            print("  已应用锐化")

        # 3. 可选：对比度调整
        if contrast:
            contrast_factor = max(0.8, min(2.0, contrast_factor))
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(contrast_factor)
            print(f"  已调整对比度 (factor={contrast_factor})")

        # 4. 可选：放大图像
        if scale > 1.0:
            new_size = (int(img.width * scale), int(img.height * scale))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
            print(f"  已放大图像到 {new_size} (scale={scale})")

        # 输出处理后图像信息
        stat = ImageStat.Stat(img)
        print(
            f"  处理后: 尺寸={img.size}, 平均亮度={stat.mean[0]:.1f}, 标准差={stat.stddev[0]:.1f}"
        )

        return img

    except Exception as e:
        print(f"  预处理失败: {e}")
        return image


def test_ocr(image_path: str, params: dict) -> str:
    """使用指定参数测试OCR"""
    print(f"\n测试参数: {params}")

    try:
        # 加载图像
        img = Image.open(image_path)

        # 预处理
        processed = preprocess_image(
            img,
            scale=params.get("scale", 2.0),
            contrast=params.get("contrast", False),
            contrast_factor=params.get("contrast_factor", 1.2),
            sharpen=params.get("sharpen", False),
        )

        # OCR识别
        lang = "chi_sim+eng"
        config = "--oem 3 --psm 6"
        text = pytesseract.image_to_string(processed, lang=lang, config=config)

        print(f"识别结果 ({len(text)} 字符):")
        print("-" * 40)
        print(text[:500] if len(text) > 500 else text)
        print("-" * 40)

        return text

    except Exception as e:
        print(f"OCR测试失败: {e}")
        return ""


def main():
    # 查找测试图片
    test_images = [
        "test_chinese.png",
        "debug_before_crop.png",
        "debug_after_crop.png",
    ]

    # 查找screenshots目录下的最新截图
    screenshot_dir = Path("screenshots")
    if screenshot_dir.exists():
        screenshots = sorted(
            screenshot_dir.glob("*.png"), key=lambda x: x.stat().st_mtime, reverse=True
        )
        if screenshots:
            test_images.append(str(screenshots[0]))

    # 选择测试图片
    image_path = None
    for img in test_images:
        if os.path.exists(img):
            image_path = img
            break

    if not image_path:
        print("错误: 未找到测试图片")
        print(f"请确保以下文件之一存在: {test_images}")
        sys.exit(1)

    print(f"使用测试图片: {image_path}")

    # 定义测试参数组合
    test_cases = [
        {"name": "当前配置", "scale": 2.0, "contrast": False, "sharpen": False},
        {
            "name": "高对比度",
            "scale": 2.0,
            "contrast": True,
            "contrast_factor": 1.5,
            "sharpen": False,
        },
        {"name": "锐化", "scale": 2.0, "contrast": False, "sharpen": True},
        {
            "name": "锐化+对比度",
            "scale": 2.0,
            "contrast": True,
            "contrast_factor": 1.3,
            "sharpen": True,
        },
        {"name": "3倍放大", "scale": 3.0, "contrast": False, "sharpen": False},
        {
            "name": "3倍+对比度",
            "scale": 3.0,
            "contrast": True,
            "contrast_factor": 1.5,
            "sharpen": False,
        },
    ]

    print("\n" + "=" * 60)
    print("OCR预处理参数测试")
    print("=" * 60)

    results = []
    for test_case in test_cases:
        print(f"\n{'=' * 60}")
        print(f"测试: {test_case['name']}")
        print(f"{'=' * 60}")

        params = {k: v for k, v in test_case.items() if k != "name"}
        text = test_ocr(image_path, params)

        results.append(
            {
                "name": test_case["name"],
                "params": params,
                "text_length": len(text),
                "chinese_chars": len([c for c in text if "\u4e00" <= c <= "\u9fff"]),
            }
        )

    # 打印对比结果
    print("\n" + "=" * 60)
    print("测试结果对比")
    print("=" * 60)
    print(f"{'配置':<15} {'总字符':<10} {'中文字符':<10}")
    print("-" * 60)
    for r in results:
        print(f"{r['name']:<15} {r['text_length']:<10} {r['chinese_chars']:<10}")

    print("\n建议:")
    best = max(results, key=lambda x: x["chinese_chars"])
    print(
        f"  识别中文字符最多的配置: {best['name']} ({best['chinese_chars']} 中文字符)"
    )


if __name__ == "__main__":
    main()
