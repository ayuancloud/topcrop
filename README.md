# TopCrop

一个用来**批量裁掉图片顶部像素**的小工具：选一批尺寸一致的竖版图片，统一削掉顶部固定的几条像素，输出到每张原图所在目录下的 `cropped` 文件夹。

典型场景：手机/相机导出的图片是 `1200 × 2608`，某个平台要求 `1200 × 2486`，而需要去掉的正好是最上面的 `122` 像素（`2608 - 2486 = 122`）。手动一张张裁太慢，这个脚本一次搞定。

## 特性

- **多选批量处理**：弹出系统文件选择窗口，按住 `Ctrl` 多选，一次处理整批图片。
- **原地就近输出**：来源图片在哪个目录，就在那个目录下创建 `cropped` 子文件夹存放结果，不做跨目录搬运。
- **尺寸校验**：只处理尺寸恰好匹配的图片，尺寸不符的直接跳过，避免误裁剪。
- **不覆盖已有文件**：目标文件重名时自动追加 `_1`、`_2`，不会悄悄盖掉你之前的结果。
- **自动摆正**：读取 EXIF 方向信息，手机竖拍的照片不会被裁错方向。
- **单张失败不中断**：某张图片损坏或格式异常，会记录原因后继续处理其余图片。
- **结果汇总**：控制台打印每张图的处理结果，结束时弹窗汇总成功 / 跳过 / 失败的数量与原因。

## 环境要求

- Python 3.9 及以上（脚本使用了 `tuple[int, int] | None` 这样的类型标注）
- [Pillow](https://python-pillow.org/)（图像处理库）
- 需要图形界面（脚本用 `tkinter` 弹出选图窗口；`tkinter` 随官方 Python 安装包一起提供）

## 安装

```bash
pip install pillow
```

如果 `pip` 命令不可用，见下方[常见问题](#常见问题)。

## 使用

1. 在脚本所在目录打开 PowerShell / 终端：

   ```powershell
   py .\batch_crop_top.py
   ```

2. 在弹出的窗口中按住 `Ctrl` 多选图片，确认。
3. 控制台会逐张打印处理结果，结束时弹窗汇总。

处理完成后，目录结构大致如下：

```text
C:\photos\
├── IMG_0001.jpg          # 原图，不动
├── IMG_0002.jpg
└── cropped\              # 自动创建
    ├── IMG_0001.jpg      # 1200x2486
    └── IMG_0002.jpg
```

如果多选的图片分散在不同目录，那么每个目录下都会各自生成一个 `cropped` 文件夹。

## 配置

脚本顶部有一小块配置区，改常量即可适配别的尺寸，无需改动逻辑：

| 常量 | 默认值 | 说明 |
| --- | --- | --- |
| `EXPECTED_SIZE` | `(1200, 2608)` | 期望的原始尺寸 `(宽, 高)`；设为 `None` 表示不校验尺寸 |
| `CROP_TOP` | `122` | 裁掉的顶部像素数；设为 `None` 时按「原高 − 目标高」自动计算 |
| `TARGET_SIZE` | `(1200, 2486)` | 目标尺寸 `(宽, 高)`，用于二次校验裁剪结果 |
| `OUTPUT_DIR_NAME` | `"cropped"` | 输出子目录名，想叫 `裁剪后的` 也可以直接改这里 |
| `JPEG_QUALITY` | `95` | JPEG 保存质量（1–100） |

例如想把 1080×2400 的图裁成 1080×2280：

```python
EXPECTED_SIZE = (1080, 2400)
CROP_TOP = 120
TARGET_SIZE = (1080, 2280)
```

## 工作原理

脚本对每张图片执行 `Image.crop((0, top, width, height))`，也就是保留 `top` 以下的全部区域，宽度和底部边缘完全不变。裁剪量由 `CROP_TOP` 直接给定，或由 `EXPECTED_SIZE` 与 `TARGET_SIZE` 的高度差推出。

保存时沿用原文件的扩展名；不在支持列表里的格式统一存为 PNG。JPEG 会先转成 `RGB`，避免带透明通道的图片保存报错。

## 项目结构

```text
topcrop/
├── batch_crop_top.py    # 主脚本，含配置区与裁剪逻辑
├── requirements.txt
├── tests/
│   └── test_crop.py     # 核心逻辑单元测试
├── LICENSE
└── README.md
```

## 测试

```bash
python -m unittest discover -s tests -v
```

测试覆盖输出尺寸、裁剪起点是否正确落在 y=122、尺寸不符时跳过、同名文件不被覆盖、RGBA 图片保存，以及文件不存在时的错误处理。裁剪逻辑函数 `crop_one()` 不依赖 `tkinter`，可以单独导入复用。

## 常见问题

### `pip` 不是可识别的命令

```
pip : 无法将“pip”项识别为 cmdlet、函数、脚本文件或可运行程序的名称。
```

这通常是 Windows 找不到独立的 `pip` 命令，也就是 Python 或其 `Scripts` 目录没进系统 `PATH`。先不用改环境变量，直接在 PowerShell 里按顺序试：

```powershell
py -m pip install pillow
```

如果提示 `py` 也找不到，再试：

```powershell
python -m pip install pillow
```

Windows 官方更推荐 `py -m pip` 或 `python -m pip`，因为它能保证 `pip` 对应的是当前运行脚本的那套 Python。

### 提示没有 pip

先执行：

```powershell
py -m ensurepip --upgrade
```

然后：

```powershell
py -m pip install --upgrade pip
py -m pip install pillow
```

`ensurepip` 是 Python 自带的 pip 修复/安装模块。

### `py`、`python` 都不存在

大概率是还没正确安装 Python，或安装时没有加入 PATH。

1. 从 [Python 官网下载页](https://www.python.org/downloads/) 安装 Python。
2. 安装界面务必勾选底部的 `Add python.exe to PATH`。
3. 安装完成后**关闭当前 PowerShell 窗口并重新打开**。
4. 检查：`py --version`
5. 安装依赖：`py -m pip install pillow`

### 脚本名称和文档不一致

把命令里的文件名换成实际名称即可：

```powershell
py .\你的脚本名.py
```

### 图片全被跳过

说明尺寸和 `EXPECTED_SIZE` 不匹配。控制台的 `[跳过]` 行会打印实际尺寸，照着改配置区即可。若某些图片被旋转过（例如手机竖拍存成 2608×1200），脚本会先按 EXIF 摆正再判断尺寸，因此一般不会误判。

### 想要中文文件夹名

把 `OUTPUT_DIR_NAME` 改成 `"裁剪后的"` 即可。

## 许可证

[MIT](LICENSE)
