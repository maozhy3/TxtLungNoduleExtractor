# 肺结节尺寸提取工具

中文 | [English](docs/README_EN.md)

基于 llama.cpp 和 Qwen 医疗模型的肺结节尺寸自动提取工具，支持从影像报告中智能提取病灶最大直径。

> **平台支持**：目前仅提供 Windows 平台支持。Linux/Mac 用户可以从源码运行。

## 功能特性

- 🖥️ 图形化界面和命令行两种使用方式
- 🔍 智能文本预处理和数值提取
- 🚀 支持单进程/多进程并行推理
- 💾 断点续传功能
- 📊 批量处理 Excel 数据

![GUI界面](docs/images/gui-screenshot.png)

---

## 快速开始

### 1. 安装依赖

```bash
# 创建虚拟环境（推荐）
conda create -n lung-nodule python=3.10
conda activate lung-nodule

# 安装依赖
pip install -r requirements.txt
```

**Windows 用户需要安装 VC++ 运行库**：https://aka.ms/vs/17/release/vc_redist.x64.exe

### 2. 下载模型

```bash
python download_model.py
```

推荐模型：
- **Qwen2.5-3B** (~2GB) - 快速，适合测试
- **Qwen2.5-7B** (~4.7GB) - 效果更好，推荐使用

### 3. 运行程序

```bash
# 图形界面（推荐）
python gui.py

# 命令行
python main.py
```

---

## 配置说明

### 配置文件

项目支持三层配置覆盖（优先级从低到高）：

1. **config.py** - 默认配置（提交到 git）
2. **config_private.py** - 个人配置（不提交到 git）⭐ 推荐
3. **外部 config.py** - 打包后可在 exe 同级目录创建

### 快速配置

复制示例文件并编辑：

```bash
copy config_private.py.example config_private.py
```

```python
# config_private.py - 只需写要覆盖的配置项

# 模型路径
MODEL_PATHS = ["models/qwen2.5-7b-instruct-q4_k_m.gguf"]

# 性能配置
LLAMA_N_THREADS = 8        # CPU 线程数
LLAMA_N_GPU_LAYERS = 0     # GPU 层数（0=纯CPU）
PROCESS_POOL_MAX_WORKERS = 1  # 进程数

# 特征提取（可选）
ENABLE_FEATURE_EXTRACTION = False
```

### 性能建议

- 低配机器（4核8GB）：`PROCESS_POOL_MAX_WORKERS=1, LLAMA_N_THREADS=4`
- 中配机器（8核16GB）：`PROCESS_POOL_MAX_WORKERS=2, LLAMA_N_THREADS=4`
- 高配机器（16核32GB）：`PROCESS_POOL_MAX_WORKERS=4, LLAMA_N_THREADS=4`

---

## 使用说明

### 数据格式

Excel 文件需包含 `yxbx` 列（影像表现）：

| yxbx |
|------|
| 右肺上叶见结节影，大小约8mm |
| 左肺下叶磨玻璃影，直径1.2cm |

### 结果输出

新增 `pred_模型名` 列：

| yxbx | pred_qwen2.5-7b |
|------|-----------------|
| 右肺上叶见结节影，大小约8mm | 8 |
| 左肺下叶磨玻璃影，直径1.2cm | 12 |

### 断点续传

按 `Ctrl+C` 中断后，检查点自动保存到 `checkpoints/`，再次运行会从上次中断处继续。

---

## 打包部署

详细打包说明请参考 [部署文档](docs/DEPLOYMENT.md)。

### 快速打包

```bash
# GUI 版本（推荐）
build_gui.bat

# 命令行版本
build_main.bat
```

输出目录：`dist/医疗影像报告预测工具/`

> **注意**：Release 版本不包含模型文件，需手动下载并放入 `models/` 目录。

---

## 开发指南

### 项目结构

```
.
├── main.py              # 命令行入口
├── gui.py               # GUI 入口
├── core.py              # 核心逻辑
├── config.py            # 默认配置
├── config_loader.py     # 配置加载
├── download_model.py    # 模型下载
├── tests/               # 测试文件
├── models/              # 模型目录
└── checkpoints/         # 检查点目录
```

### 运行测试

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

---

## 常见问题

**Q: 安装 llama-cpp-python 失败？**  
A: 确保已安装 VC++ 运行库

**Q: 内存不足？**  
A: 设置 `PROCESS_POOL_MAX_WORKERS = 1`

**Q: 如何使用 GPU？**  
A: 安装 CUDA 版本的 llama-cpp-python，设置 `LLAMA_N_GPU_LAYERS = 35`

---

## 更新日志

### v1.2.0 (2025-11-12)
- ✅ 优化打包流程：打包时不再自动复制所有模型文件
- ✅ 改进用户体验：用户可根据需要手动选择要部署的模型
- ✅ 减小发布包体积：避免打包不必要的大型模型文件

### v1.1.0 (2025-11-10)
- ✅ 添加标准依赖管理（requirements.txt）
- ✅ 规范化代码风格和类型注解
- ✅ 重构配置加载逻辑
- ✅ 添加完整单元测试（52个测试用例）
- ✅ 改进文档和开发工具

### v1.0.0 (2025-11-06)
- ✅ 初始版本发布
- ✅ GUI 和命令行界面
- ✅ 批量预测和断点续传
- ✅ 多进程并行处理

---

## 许可证

本项目采用 [MIT License](LICENSE) 开源协议。

**免责声明**：本工具仅供学习和研究使用，不应用于临床诊断。使用者需自行承担使用本工具的风险和责任。
