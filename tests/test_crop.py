# -*- coding: utf-8 -*-
"""batch_crop_top 的核心裁剪逻辑测试。运行：python -m unittest discover -s tests"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    raise unittest.SkipTest("需要 Pillow：pip install pillow")

import batch_crop_top as crop


def make_gradient(path: str, size: tuple[int, int], fmt: str = "JPEG", mode: str = "RGB") -> None:
    """生成一张每行颜色唯一、便于校验偏移量的图。"""
    img = Image.new(mode, size)
    px = img.load()
    for y in range(size[1]):
        color = (y % 256, (y // 256) % 256, 7) if mode == "RGB" else (y % 256, 0, 0, 255)
        for x in range(size[0]):
            px[x, y] = color
    img.save(path, format=fmt)


class CropTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = self._tmp.name

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_output_size(self) -> None:
        src = os.path.join(self.tmp, "a.jpg")
        make_gradient(src, (1200, 2608))
        status, _ = crop.crop_one(src)
        self.assertEqual(status, "ok")
        with Image.open(os.path.join(self.tmp, "cropped", "a.jpg")) as out:
            self.assertEqual(out.size, (1200, 2486))

    def test_crops_from_top(self) -> None:
        """首行应对应原图 y=122，末行仍是原图 y=2607。"""
        src = os.path.join(self.tmp, "b.png")
        make_gradient(src, (1200, 2608), fmt="PNG")
        crop.crop_one(src)
        with Image.open(os.path.join(self.tmp, "cropped", "b.png")) as out:
            self.assertEqual(out.getpixel((0, 0)), (122, 0, 7))
            self.assertEqual(out.getpixel((0, out.size[1] - 1)), (2607 % 256, 2607 // 256, 7))

    def test_skips_wrong_size(self) -> None:
        src = os.path.join(self.tmp, "c.jpg")
        Image.new("RGB", (1200, 2400), "white").save(src)
        status, _ = crop.crop_one(src)
        self.assertEqual(status, "skip")
        self.assertFalse(os.path.exists(os.path.join(self.tmp, "cropped", "c.jpg")))

    def test_does_not_overwrite(self) -> None:
        src = os.path.join(self.tmp, "d.jpg")
        make_gradient(src, (1200, 2608))
        crop.crop_one(src)
        crop.crop_one(src)
        files = sorted(os.listdir(os.path.join(self.tmp, "cropped")))
        self.assertEqual(files, ["d.jpg", "d_1.jpg"])

    def test_rgba_png(self) -> None:
        src = os.path.join(self.tmp, "e.png")
        Image.new("RGBA", (1200, 2608), (255, 0, 0, 128)).save(src)
        status, _ = crop.crop_one(src)
        self.assertEqual(status, "ok")
        with Image.open(os.path.join(self.tmp, "cropped", "e.png")) as out:
            self.assertEqual(out.size, (1200, 2486))

    def test_missing_file(self) -> None:
        status, _ = crop.crop_one(os.path.join(self.tmp, "nope.jpg"))
        self.assertEqual(status, "fail")


if __name__ == "__main__":
    unittest.main()
