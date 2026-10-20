#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
batch_crop_top.py —— 批量裁掉图片顶部若干像素。

场景：一批 1200x2608 的竖版图片，需要统一裁成 1200x2486，
      裁掉的是最上面的 122 像素（2608 - 2486 = 122）。

行为：
  1. 弹窗多选图片；
  2. 在「每张原图所在的目录」下创建 cropped 文件夹；
  3. 把裁剪后的图片按原文件名保存进去（同名文件自动加序号，不会覆盖）；
  4. 只处理尺寸符合预期的图片，尺寸不符的跳过，避免误裁剪。

依赖：pip install pillow
"""

from __future__ import annotations

import os
import sys

try:
    from PIL import Image, ImageOps
except ImportError:  # pragma: no cover
    sys.stderr.write(
        "缺少 Pillow 依赖，请先安装：\n"
        "    py -m pip install pillow\n"
    )
    raise SystemExit(1)

# ---------------------------------------------------------------------------
# 配置区：改这里就能适配别的尺寸
# ---------------------------------------------------------------------------

# 期望的原始尺寸（宽, 高）。设为 None 表示不校验尺寸。
EXPECTED_SIZE: tuple[int, int] | None = (1200, 2608)

# 需要裁掉的顶部像素数。设成 None 时，自动按「原高 - 目标高」计算。
CROP_TOP: int | None = 122

# 目标尺寸（宽, 高）。设成 None 时，自动按「原尺寸 - 顶部裁剪」计算。
TARGET_SIZE: tuple[int, int] | None = (1200, 2486)

# 输出子目录名
OUTPUT_DIR_NAME = "cropped"

# JPEG 保存质量（1-100）
JPEG_QUALITY = 95

# 支持选择的图片扩展名
IMAGE_EXTENSIONS = (
    "*.jpg", "*.jpeg", "*.png", "*.bmp", "*.webp", "*.tif", "*.tiff",
)

# 输出时保持原格式的映射；不在表里的格式统一存为 PNG
SAVE_FORMAT_MAP = {
    ".jpg": "JPEG",
    ".jpeg": "JPEG",
    ".png": "PNG",
    ".bmp": "BMP",
    ".webp": "WEBP",
    ".tif": "TIFF",
    ".tiff": "TIFF",
}


def unique_path(path: str) -> str:
    """若目标文件已存在，追加 _1、_2 … 直到不冲突。"""
    if not os.path.exists(path):
        return path
    stem, ext = os.path.splitext(path)
    index = 1
    while True:
        candidate = f"{stem}_{index}{ext}"
        if not os.path.exists(candidate):
            return candidate
        index += 1


def crop_one(src_path: str) -> tuple[str, str]:
    """
    处理单张图片。

    返回 (状态, 说明)，状态取值为 "ok" / "skip" / "fail"。
    """
    try:
        with Image.open(src_path) as img:
            # 按 EXIF 方向摆正，避免手机照片横竖颠倒
            img = ImageOps.exif_transpose(img)

            width, height = img.size

            if EXPECTED_SIZE is not None and (width, height) != EXPECTED_SIZE:
                return "skip", f"尺寸为 {width}x{height}，不是 {EXPECTED_SIZE[0]}x{EXPECTED_SIZE[1]}，已跳过"

            top = CROP_TOP
            if top is None:
                if TARGET_SIZE is None:
                    return "fail", "未配置 CROP_TOP 或 TARGET_SIZE，无法确定裁剪量"
                top = height - TARGET_SIZE[1]

            if top < 0:
                return "fail", "裁剪量计算结果为负数，请检查配置"
            if top == 0:
                return "skip", "无需裁剪（顶部裁剪量为 0）"

            target_height = height - top
            if TARGET_SIZE is not None and (width, target_height) != TARGET_SIZE:
                return (
                    "fail",
                    f"裁剪后尺寸为 {width}x{target_height}，与目标 "
                    f"{TARGET_SIZE[0]}x{TARGET_SIZE[1]} 不一致",
                )

            # 只裁顶部，宽度和底部保持不变
            cropped = img.crop((0, top, width, height))

            # 统一转成 RGB 存 JPEG，避免透明通道导致保存失败
            ext = os.path.splitext(src_path)[1].lower()
            save_format = SAVE_FORMAT_MAP.get(ext, "PNG")
            if save_format == "JPEG" and cropped.mode not in ("RGB", "L"):
                cropped = cropped.convert("RGB")

            out_dir = os.path.join(os.path.dirname(os.path.abspath(src_path)), OUTPUT_DIR_NAME)
            os.makedirs(out_dir, exist_ok=True)

            filename = os.path.basename(src_path)
            if save_format != SAVE_FORMAT_MAP.get(ext, "PNG"):
                filename = os.path.splitext(filename)[0] + ".png"

            out_path = unique_path(os.path.join(out_dir, filename))

            save_kwargs: dict = {}
            if save_format == "JPEG":
                save_kwargs = {"quality": JPEG_QUALITY, "subsampling": 0}
            cropped.save(out_path, format=save_format, **save_kwargs)

            return "ok", f"{width}x{height} -> {cropped.size[0]}x{cropped.size[1]}"

    except Exception as exc:  # noqa: BLE001 - 单张失败不应中断整批
        return "fail", f"{type(exc).__name__}: {exc}"


def main() -> int:
    # tkinter 只在这里按需导入：裁剪逻辑本身不依赖 GUI，方便被其他脚本复用
    try:
        import tkinter as tk
        from tkinter import filedialog, messagebox
    except ImportError:
        sys.stderr.write(
            "当前 Python 缺少 tkinter，无法弹出选图窗口。\n"
            "Windows 请重新运行官方安装包并勾选 tcl/tk 组件；\n"
            "Linux 可安装 python3-tk。\n"
        )
        return 1

    root = tk.Tk()
    root.withdraw()

    paths = filedialog.askopenfilenames(
        title="选择要裁剪的图片（可按住 Ctrl 多选）",
        filetypes=[("图片文件", " ".join(IMAGE_EXTENSIONS)), ("所有文件", "*.*")],
    )

    if not paths:
        print("没有选择任何图片，程序退出。")
        return 0

    ok, skipped, failed = [], [], []
    total = len(paths)

    for index, path in enumerate(paths, start=1):
        status, detail = crop_one(path)
        print(f"[{index}/{total}] {os.path.basename(path)} -> {status}: {detail}")
        if status == "ok":
            ok.append((path, detail))
        elif status == "skip":
            skipped.append((path, detail))
        else:
            failed.append((path, detail))

    summary = (
        f"共选择 {total} 张图片\n"
        f"成功裁剪：{len(ok)} 张\n"
        f"跳过：{len(skipped)} 张\n"
        f"失败：{len(failed)} 张\n\n"
        f"裁剪后的图片保存在各自原图目录下的 {OUTPUT_DIR_NAME} 文件夹中。"
    )

    if failed or skipped:
        summary += "\n\n—— 详情 ——\n"
        for path, detail in skipped:
            summary += f"[跳过] {os.path.basename(path)}：{detail}\n"
        for path, detail in failed:
            summary += f"[失败] {os.path.basename(path)}：{detail}\n"

    print("\n" + summary)
    messagebox.showinfo("批量裁剪完成", summary)

    root.destroy()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
