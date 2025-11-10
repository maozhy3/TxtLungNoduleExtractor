# 部署指南 - 离线Windows环境

本指南说明如何将项目打包成独立的可执行程序，部署到没有Python环境的离线Windows电脑。

## 方案概述

使用 **PyInstaller** 将Python程序打包成独立的exe文件，包含所有依赖库，无需目标机器安装Python。

## 打包步骤

### 1. 准备开发环境

确保已安装所有依赖：

```bash
pip install pyinstaller pandas openpyxl llama-cpp-python tqdm
```

### 2. 准备必要文件

#### 2.1 VC++ 运行库（必需）

下载并放置到 `_vcredist/` 目录：
- 下载地址：https://aka.ms/vs/17/release/vc_redist.x64.exe
- 放置位置：`_vcredist/vc_redist.x64.exe`

#### 2.2 模型文件

将 `.gguf` 模型文件放到 `models/` 目录

### 3. 执行打包

运行打包脚本：

```bash
build_gui.bat
```

或手动执行：

```bash
pyinstaller gui.spec --clean
```

### 4. 打包结果

打包完成后，会在 `dist/医疗影像报告预测工具/` 目录生成以下文件：

```
dist/医疗影像报告预测工具/
├── 医疗影像报告预测工具.exe    # 主程序
├── _internal/                   # 依赖库（自动生成）
├── models/                      # 模型文件目录
│   └── *.gguf                  # 需手动复制
├── _vcredist/                   # VC++运行库
│   └── vc_redist.x64.exe       # 需手动复制
├── test.xlsx                    # 示例数据（可选）
└── config_example.py            # 配置示例（可选）
```

## 部署到目标机器

### 方式一：ZIP压缩包（推荐）

1. 将 `dist/医疗影像报告预测工具/` 整个文件夹压缩为 ZIP
2. 上传到目标机器
3. 解压后双击 `医疗影像报告预测工具.exe` 运行

### 方式二：安装包制作（可选）

使用 Inno Setup 或 NSIS 制作安装程序：

#### 使用 Inno Setup

1. 下载安装 Inno Setup：https://jrsoftware.org/isdl.php
2. 创建安装脚本（见下方示例）
3. 编译生成 `.exe` 安装包

**Inno Setup 脚本示例** (`installer.iss`)：

```iss
[Setup]
AppName=医疗影像报告预测工具
AppVersion=1.0
DefaultDirName={pf}\医疗影像报告预测工具
DefaultGroupName=医疗影像报告预测工具
OutputDir=installer_output
OutputBaseFilename=医疗影像报告预测工具_安装包
Compression=lzma2
SolidCompression=yes

[Files]
Source: "dist\医疗影像报告预测工具\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs

[Icons]
Name: "{group}\医疗影像报告预测工具"; Filename: "{app}\医疗影像报告预测工具.exe"
Name: "{commondesktop}\医疗影像报告预测工具"; Filename: "{app}\医疗影像报告预测工具.exe"

[Run]
Filename: "{app}\_vcredist\vc_redist.x64.exe"; Parameters: "/quiet /norestart"; StatusMsg: "正在安装 VC++ 运行库..."; Flags: waituntilterminated
```

## 目标机器使用说明

### 首次运行

1. 解压或安装程序
2. 程序会自动检测并安装 VC++ 运行库（如果需要）
3. 双击 `医疗影像报告预测工具.exe` 启动

### 配置自定义参数

在程序目录创建 `config.py` 文件来覆盖默认配置：

```python
# config.py
from pathlib import Path

# 输入输出
EXCEL_PATH = Path("data/input.xlsx")
OUTPUT_PATH = Path("data/output.xlsx")

# 模型路径
MODEL_PATHS = [
    "models/qwen-medical-lora-251106-q4_k_m.gguf"
]

# 性能配置
LLAMA_N_THREADS = 4          # 根据目标机器CPU核心数调整
PROCESS_POOL_MAX_WORKERS = 1 # 单进程模式（节省内存）
```

## 常见问题

### Q1: 打包后文件很大？

A: 正常现象。PyInstaller会打包所有依赖库，通常在100-500MB。可以：
- 使用 UPX 压缩（已在spec中启用）
- 排除不必要的库
- 使用虚拟环境打包（只安装必需的包）

### Q2: 目标机器提示缺少DLL？

A: 确保：
1. VC++ 运行库已正确安装
2. 使用与目标机器相同架构（x64）打包
3. 在相同或更低版本的Windows上打包

### Q3: 模型文件太大，如何处理？

A: 可以：
1. 单独提供模型文件下载链接
2. 使用分卷压缩
3. 在目标机器上手动复制模型到 `models/` 目录

### Q4: 如何更新模型而不重新打包？

A: 直接替换 `models/` 目录下的 `.gguf` 文件即可

### Q5: 打包失败？

A: 检查：
1. 是否安装了所有依赖：`pip list`
2. PyInstaller版本：`pip install --upgrade pyinstaller`
3. 查看详细错误：`pyinstaller gui.spec --clean --log-level DEBUG`

## 性能优化建议

### 针对不同配置的目标机器

**低配机器（4核，8GB内存）**：
```python
LLAMA_N_THREADS = 4
PROCESS_POOL_MAX_WORKERS = 1
LLAMA_N_GPU_LAYERS = 0
```

**中配机器（8核，16GB内存）**：
```python
LLAMA_N_THREADS = 4
PROCESS_POOL_MAX_WORKERS = 2
LLAMA_N_GPU_LAYERS = 0
```

**高配机器（16核，32GB内存）**：
```python
LLAMA_N_THREADS = 4
PROCESS_POOL_MAX_WORKERS = 4
LLAMA_N_GPU_LAYERS = 0
```

**有NVIDIA GPU**：
```python
LLAMA_N_THREADS = 4
PROCESS_POOL_MAX_WORKERS = 1
LLAMA_N_GPU_LAYERS = 35  # 根据显存调整
```

## 测试清单

打包完成后，在目标环境测试：

- [ ] 程序能正常启动
- [ ] GUI界面显示正常
- [ ] 能选择输入文件
- [ ] 能添加模型
- [ ] 预测功能正常
- [ ] 日志输出正常
- [ ] 结果文件正确保存
- [ ] 中断后能继续（检查点功能）

## 文件大小参考

- 基础程序（不含模型）：~200MB
- 模型文件（Q4量化）：~500MB-2GB
- 总大小：~700MB-2.2GB

## 更新日志

### v1.0
- 初始版本
- 支持GUI界面
- 支持断点续传
- 支持多模型批量预测
