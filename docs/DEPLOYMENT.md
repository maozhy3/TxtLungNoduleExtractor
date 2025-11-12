# 打包部署指南

> **注意**：打包功能仅支持 Windows 平台。

## 前置要求

1. Windows 操作系统
2. Conda 环境（已安装并激活 `node_extractor` 环境）
3. PyInstaller（已在环境中安装）
4. VC++ 运行库：`_vcredist/vc_redist.x64.exe`

## 打包方式

### GUI 版本（推荐）

```bash
build_gui.bat
```

**输出目录**：`dist/医疗影像报告预测工具/`

**包含文件**：
- `医疗影像报告预测工具.exe` - 主程序
- `_internal/` - 依赖库
- `models/` - 模型目录（需手动复制模型）
- `_vcredist/` - VC++ 运行库
- `test.xlsx` - 示例数据
- `config_example.py` - 配置示例

### 命令行版本

```bash
build_main.bat
```

**输出目录**：`dist/医疗影像报告预测工具-CLI/`

## 部署到离线电脑

1. 将 `dist/医疗影像报告预测工具/` 整个文件夹复制到目标电脑
2. 手动下载模型文件并放入 `models/` 目录
3. 确保 `_vcredist/vc_redist.x64.exe` 存在
4. 双击 `医疗影像报告预测工具.exe` 运行

## 外部配置

在 exe 同级目录创建 `config.py` 可覆盖默认配置，无需重新打包。

## 打包后测试清单

- [ ] 程序能正常启动
- [ ] 能加载模型文件
- [ ] 能读取 Excel 文件
- [ ] 能正常预测并保存结果
- [ ] 停止功能正常工作
- [ ] 检查点功能正常（中断后继续）
- [ ] 特征提取功能正常（如果启用）
- [ ] 外部配置文件能正常加载

## 常见打包问题

### 1. 打包失败：找不到模块

检查 `.spec` 文件中的 `hiddenimports` 是否包含所有必要模块。

必需模块：`pandas`、`openpyxl`、`llama_cpp`、`tqdm`、`tkinter`、`config_loader`、`core`

### 2. 运行时找不到 DLL

- 确保 `llama_cpp` 的 DLL 文件被正确收集
- 检查 `.spec` 文件中的 `binaries` 配置
- 确保 VC++ 运行库已安装

### 3. 配置文件不生效

- 检查配置文件名是否正确（`config.py` 或 `config_private.py`）
- 检查配置文件位置（exe 同级目录）
- 查看程序启动日志，确认是否加载了配置

### 4. 模型加载失败

- 确保模型文件在 `models/` 目录下
- 检查模型文件路径配置
- 确认模型文件格式正确（.gguf）

## 打包配置文件

### gui.spec

GUI 版本的 PyInstaller 配置文件。

关键配置：
- `console=False` - 不显示控制台窗口
- 包含核心模块：`config.py`、`config_loader.py`、`core.py`
- 自动收集 llama_cpp 的 DLL 文件

### main.spec

命令行版本的 PyInstaller 配置文件。

关键配置：
- `console=True` - 显示控制台窗口
- 包含所有核心模块和依赖
