# Smart_labelimg

Smart_labelimg 是一款面向 Windows 10/11 x64 用户的开源图像标注工具，支持
YOLO TXT、Pascal VOC XML 和本地 MobileSAM 智能标注。程序通过 DirectML 优先
使用 NVIDIA、AMD 或 Intel GPU，GPU 不可用时自动切换到 CPU。

## 一键下载

[**点击下载 Smart_labelimg Windows 版**](https://github.com/3513542967-creator/Smart_Labelimg/releases/latest/download/Smart-LabelImg-DirectML-Windows-x64.zip)

## 智能标注使用说明

### 智能点击标注

切换到智能标注模式并选择类别，然后在目标物体内部点击。MobileSAM 会分析点击位置，
自动生成贴合目标的标注框。AI 推理在本地完成。

### 画框后自动校准

在智能标注模式下，先围绕目标画一个粗略矩形框。松开鼠标后，MobileSAM 会根据目标
轮廓自动调整矩形边界，使标注框更贴近物体。校准结果会按照当前选择的 YOLO TXT 或
Pascal VOC XML 格式自动保存。

### 快捷键

| 快捷键 | 功能 |
|---|---|
| `W` | 普通手动画框 |
| `S` | 智能标注模式 |
| `A` / `D` | 上一张 / 下一张 |
| `Shift+D` | 智能传播到下一张 |
| `Ctrl+S` | 保存当前标注 |
| `Ctrl+Z` / `Ctrl+Y` | 撤销 / 重做 |
| `Delete` | 删除选中的标注框 |
| `Ctrl+A` | 选择全部标注框 |
| `Ctrl+D` | 复制选中的标注框 |
| `Ctrl+V` | 复制上一张图片的标注 |

## 引用与致谢

本项目的标注工作流和格式兼容设计参考了
[LabelImg](https://github.com/HumanSignal/labelImg)。LabelImg 使用 MIT License。

智能点击和画框后自动校准基于
[MobileSAM](https://github.com/ChaoningZhang/MobileSAM)。MobileSAM 使用
Apache License 2.0。Windows 版本将 MobileSAM 转换为 ONNX 模型，并通过
ONNX Runtime DirectML 在本地运行。

Smart_labelimg 是独立社区项目，不是 LabelImg、MobileSAM、Microsoft 或其维护者的
官方产品。完整第三方声明见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

## License

Smart_labelimg 源代码使用 [MIT License](LICENSE)。第三方组件与模型继续受各自许可证约束。
