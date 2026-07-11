# Smart_labelimg

Smart_labelimg is an open-source Windows image annotation application inspired by
LabelImg, with local MobileSAM-assisted bounding boxes. It supports NVIDIA, AMD,
and Intel GPUs through ONNX Runtime DirectML and automatically falls back to CPU.

Smart_labelimg 是一款面向 Windows 用户的开源图像标注工具，支持 YOLO TXT、
Pascal VOC XML 和本地 MobileSAM 智能框选。AI 推理完全在本地完成，不上传图片。

## Download / 一键下载

[**Download Smart_labelimg for Windows 10/11 x64**](https://github.com/3513542967-creator/Smart_labelimg/releases/latest/download/Smart-LabelImg-DirectML-Windows-x64.zip)

> 请下载上面的 Windows ZIP，不要下载 GitHub 自动生成的 `Source code` 压缩包；
> Source code 不包含可直接运行的 EXE。

## Install / 安装

1. 点击上面的下载链接。
2. 完整解压 `Smart-LabelImg-DirectML-Windows-x64.zip`。
3. 打开解压后的 `Smart LabelImg` 文件夹。
4. 双击 `Smart LabelImg.exe`。

无需安装 Python、CUDA Toolkit 或模型文件。不要从 ZIP 预览窗口直接运行 EXE，
也不要只复制 EXE；`_internal` 文件夹是程序运行所必需的。

Windows SmartScreen 可能提示未知发布者，因为当前版本尚未购买代码签名证书。请确认文件来自
本仓库 Release，并使用 Release 中的 `.sha256` 文件核验下载内容。

## Main features / 主要功能

- 打开单张图片或整个图片文件夹。
- 支持 JPG、JPEG、PNG、BMP、WebP，包括中文路径和中文文件名。
- 手动画框和 MobileSAM 智能点击/粗框细化。
- DirectML 优先使用 NVIDIA、AMD 或 Intel DirectX 12 GPU。
- GPU 不可用或驱动初始化失败时自动回退 CPU。
- 保存 YOLO TXT 或 Pascal VOC XML。
- 自动保存、撤销/重做、类别管理、上一张/下一张和智能传播。
- 本地离线推理，不需要账号，不上传用户数据。

## Quick user guide / 简易使用手册

1. 点击 `Open`，选择 `Image` 或 `Folder`。
2. 在 `Save Format` 选择 `YOLO TXT` 或 `Pascal VOC XML`。
3. 选择类别；普通模式拖动画框，智能模式点击目标或先画粗框。
4. 第一次编辑后，应用自动生成与图片同名的 Label。
5. 使用 `Save/Target` 可把所有 Label 保存到单独的标签目录。
6. 使用图片列表或 `A` / `D` 切换图片。

没有现成 Label 也可以直接开始：纯浏览不会生成空文件；第一次新增、删除、移动或修改
标注后才自动生成 Label。明确按 `Ctrl+S` 会生成空 Label，用于表示“已检查但没有目标”。

常用快捷键：

| Shortcut | Action |
|---|---|
| `W` | 普通手动画框 |
| `S` | 智能标注模式 |
| `A` / `D` | 上一张 / 下一张 |
| `Ctrl+S` | 明确保存当前标注 |
| `Ctrl+Z` / `Ctrl+Y` | 撤销 / 重做 |
| `Delete` | 删除选中的框 |
| `Ctrl+A` | 选择全部框 |

更详细的 Windows 构建和数据保存说明见
[`docs/windows-install-build.md`](docs/windows-install-build.md)。

## Image and label layout / 数据目录

Label 可以与图片放在同一目录：

```text
dataset/
  image001.jpg
  image001.txt
  classes.txt
```

也可以分开存放：

```text
dataset/
  images/
    image001.jpg
  labels/
    image001.txt
    classes.txt
```

文件夹打开只扫描当前层，不递归扫描子目录。同一目录不要同时放置 `same.jpg` 和
`same.png`，否则二者会竞争相同的 `same.txt`；应用会提示先重命名。

## Build from source / 从源码构建

要求 Windows 10/11 x64、Python 3.11：

```powershell
git clone https://github.com/3513542967-creator/Smart_labelimg.git
cd Smart_labelimg
.\setup.ps1
.\run.ps1
.\.venv\Scripts\python.exe -m pytest -q
.\build_app.ps1
```

构建产物位于：

```text
dist\Smart LabelImg\Smart LabelImg.exe
release\Smart-LabelImg-DirectML-Windows-x64.zip
```

## Privacy and security / 隐私与安全

- 图片、标注和模型推理均保留在用户电脑上。
- 应用不会自动联网、上传数据或执行下载的代码。
- 标注采用临时文件与原子替换方式保存，并检测外部文件冲突。
- 发布包附带 SHA-256 校验文件。
- 安全问题请通过 GitHub Issues 报告，避免在公开 Issue 中附带私人数据集。

## Attribution / 引用与致谢

本项目的标注工作流和格式兼容设计参考了
[LabelImg](https://github.com/HumanSignal/labelImg)，LabelImg 使用 MIT License。

智能框选基于
[MobileSAM](https://github.com/ChaoningZhang/MobileSAM)，MobileSAM 使用 Apache License 2.0。
Windows 发布版将 MobileSAM 转换为 ONNX 编码器与解码器，并通过 ONNX Runtime
DirectML 本地运行。

Smart_labelimg 是独立社区项目，不是 LabelImg、MobileSAM、Microsoft 或其维护者的
官方产品，也不暗示任何上游项目对本项目的背书。完整第三方声明见
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)。

## License

Smart_labelimg source code is released under the [MIT License](LICENSE).
Third-party components and model artifacts remain subject to their respective licenses.

