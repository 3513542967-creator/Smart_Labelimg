# Windows 开发、运行与打包

适用于 Windows 10/11 x64。先安装：

- [Python 3.11 x64](https://www.python.org/downloads/windows/)，安装时勾选 `Add Python to PATH`
- [Git for Windows](https://git-scm.com/download/win)

将项目源码解压或克隆到本地后，在项目根目录打开 PowerShell，依次使用以下四条命令：

```powershell
.\setup.ps1
.\run.ps1
.\.venv\Scripts\python.exe -m pytest -q
.\build_app.ps1
```

- `setup.ps1` 创建 `.venv`，并安装界面与 ONNX Runtime DirectML 依赖。
- `run.ps1` 从源码启动应用。
- 测试命令运行完整测试集。修改代码后建议重新执行。
- `build_app.ps1` 安装打包依赖、运行 PyInstaller，并生成发布 ZIP。Windows 可执行文件必须在 Windows 上构建。

主要代码位于 `smart_labelimg\`，测试位于 `tests\`。Windows 智能标注需要保留
`models\mobile_sam_encoder.onnx` 和 `models\mobile_sam_decoder.onnx`。

## 构建产物

- EXE：`dist\Smart LabelImg\Smart LabelImg.exe`
- x64 发布包：`release\Smart-LabelImg-DirectML-Windows-x64.zip`

发布 ZIP 已包含完整 ONNX 模型。解压后运行 `Smart LabelImg\Smart LabelImg.exe` 即可。

## 没有现成 Label 时

- 单张图片或图片文件夹都可以直接打开，缺少 Label 时从空标注开始。
- 仅浏览或切换图片不会生成空 Label 文件。
- 第一次新增、删除、移动、改类或接受智能标注后，会自动在目标位置生成与图片同名的
  `.txt`（YOLO）或 `.xml`（Pascal VOC）。YOLO 同时原子写入 `classes.txt`。
- 用户明确点击 `Save` 时，即使没有框也会生成空 Label，用于表示该图片已检查且没有目标。
- 默认保存在图片旁边；使用 `Save/Target` 可将整个文件夹的 Label 统一保存到独立目录。
- 如果保存失败或检测到文件被其他程序修改，应用不会覆盖外部内容，也不会继续切图。
- 文件夹不会递归扫描；同一目录中不能同时存在 `same.jpg` 与 `same.png`，因为它们会竞争
  同一个 Label 文件。应用会阻止打开并提示先重命名。

程序会在启动时自动检测计算设备：DirectX 12 可用时优先通过 DirectML 使用
NVIDIA、AMD 或 Intel GPU；没有兼容 GPU、驱动不可用或 GPU 初始化失败时会自动回退到 CPU。
因此用户不需要安装独立的 Python 环境，也不要求电脑配有 GPU。CPU 模式首次智能
标注可能较慢，但普通手工标注不受影响。高级排障时可设置
`SMART_LABELIMG_DEVICE=cpu` 强制使用 CPU。

发布目录还会生成同名 `.sha256` 文件。发布到 GitHub Releases 后，用户可用
`Get-FileHash <zip文件> -Algorithm SHA256` 对照校验下载文件。

## PowerShell 阻止脚本时

只为当前 PowerShell 会话放开限制，然后重新执行命令：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

不需要修改系统级执行策略。

## 可选参数

```powershell
.\setup.ps1 -SkipAi
.\setup.ps1 -Cpu
.\build_app.ps1 -SkipInstall
.\build_app.ps1 -NoZip
```

`-SkipAi` 仅安装界面依赖，不能使用智能标注；默认安装 DirectML GPU 运行时，作为
GitHub 主发布版本，没有兼容 GPU 时应用仍会自动使用 CPU；`-Cpu` 用于构建
体积较小的纯 CPU 版本；`-SkipInstall` 复用现有 `.venv`；`-NoZip` 只生成 EXE
目录。
