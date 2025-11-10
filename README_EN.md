# Lung Nodule Size Extraction Tool

[中文](README.md) | English

An automated lung nodule size extraction tool based on llama.cpp and Qwen medical model, supporting intelligent extraction of maximum lesion diameter from imaging reports.

> **Platform Support**: Currently only supports Windows platform. Linux/Mac users can run from source code, but the packaged exe version is only available for Windows.

## Features

- 🖥️ Both GUI and command-line interfaces
- 🔍 Intelligent text preprocessing and numerical extraction
- 🚀 Single-process/multi-process parallel inference
- 💾 Checkpoint resume (continue processing after interruption)
- 📊 Batch processing of Excel data
- ⚙️ Flexible configuration management
- 📦 Package as standalone exe

---

## Quick Start

### 1. Install VC++ Runtime (Windows Required)

Download and install: https://aka.ms/vs/17/release/vc_redist.x64.exe

Or place it in the `_vcredist/` directory, the program will install it automatically.

### 2. Install Python Dependencies

```bash
# Create virtual environment (recommended)
conda create -n lung-nodule python=3.10
conda activate lung-nodule

# Install dependencies
pip install -r requirements.txt
```

### 3. Download Model

> **Note**: The current Release version does not include model files, they need to be downloaded separately.

```bash
python download_model.py
```

Recommended models:
- **Qwen2.5-3B** (~2GB) - Fast, suitable for testing
- **Qwen2.5-7B** (~4.7GB) - Better performance, recommended

### 4. Run the Program

**GUI (Recommended)**:
```bash
python gui.py
```

**Command Line**:
```bash
python main.py
```

---

## Configuration

Edit `config.py` to modify settings:

```python
# Input/Output
EXCEL_PATH = "tests/test.xlsx"           # Input file
OUTPUT_PATH = "tests/test_results.xlsx"  # Output file

# Model path
MODEL_PATHS = ["models/qwen2.5-7b-instruct-q4_k_m.gguf"]

# Performance settings
LLAMA_N_THREADS = 8               # CPU threads
LLAMA_N_GPU_LAYERS = 0            # GPU layers (0=CPU only)
PROCESS_POOL_MAX_WORKERS = 1      # Number of processes (1=single process)
CHECKPOINT_SAVE_INTERVAL = 5000   # Checkpoint save interval
```

**Performance Recommendations**:
- Low-end (4 cores, 8GB): `PROCESS_POOL_MAX_WORKERS = 1, LLAMA_N_THREADS = 4`
- Mid-range (8 cores, 16GB): `PROCESS_POOL_MAX_WORKERS = 2, LLAMA_N_THREADS = 4`
- High-end (16 cores, 32GB): `PROCESS_POOL_MAX_WORKERS = 4, LLAMA_N_THREADS = 4`

---

## Usage

### Data Format

Excel file must contain `yxbx` column (imaging findings):

| yxbx |
|------|
| Nodule in right upper lobe, size about 8mm |
| Ground-glass opacity in left lower lobe, diameter 1.2cm |

### Output Results

New column `pred_model_name` added:

| yxbx | pred_qwen2.5-7b |
|------|-----------------|
| Nodule in right upper lobe, size about 8mm | 8 |
| Ground-glass opacity in left lower lobe, diameter 1.2cm | 12 |

### Checkpoint Resume

- Press `Ctrl+C` to interrupt, checkpoint automatically saved to `checkpoints/`
- Run again to continue from last interruption
- Checkpoint automatically cleared after completion

---

## Packaging and Deployment

> **Note**: Packaging is only supported on Windows platform.

### Package as exe

```bash
# Run build script (Windows only)
build_gui.bat
```

Package directory structure:
```
dist/医疗影像报告预测工具/
├── 医疗影像报告预测工具.exe
├── _internal/              # Dependencies
├── models/                 # Model files (copy manually)
└── _vcredist/              # VC++ runtime (copy manually)
```

### Deploy to Offline Computer

> **Important**:
> - Release version does not include model files, need to download manually and place in `models/` directory
> - Windows platform only

1. Copy the entire `dist/医疗影像报告预测工具/` folder to target Windows computer
2. **Manually download model files** and place in `models/` directory (not included in Release)
3. Ensure `_vcredist/vc_redist.x64.exe` exists
4. Double-click `医疗影像报告预测工具.exe` to run

### External Configuration

Create `config.py` in the same directory as exe to override default settings without repackaging.

---

## Development Guide

### Install Development Dependencies

```bash
pip install -r requirements-dev.txt
```


### Project Structure

```
.
├── main.py              # Command-line entry
├── gui.py               # GUI entry
├── core.py              # Core logic
├── config.py            # Configuration file
├── config_loader.py     # Configuration loader
├── download_model.py    # Model downloader
├── requirements.txt     # Core dependencies
├── requirements-dev.txt # Development dependencies
├── tests/               # Test files (unit tests, test data, test scripts)
├── models/              # Model directory
└── checkpoints/         # Checkpoint directory
```


### Run Tests

```bash
# Windows
cd tests
run_tests.bat

# Linux/Mac
cd tests
./run_tests.sh

# Or use pytest directly
pytest tests/ -v
```

### Code Formatting

```bash
# Auto format
format_code.bat

# Or manually
black *.py tests/
ruff check . --fix
```

---

## FAQ

**Q: Failed to install llama-cpp-python?**  
A: Make sure VC++ runtime is installed

**Q: Out of memory?**  
A: Set `PROCESS_POOL_MAX_WORKERS = 1`

**Q: How to use GPU?**  
A: Install CUDA version of llama-cpp-python, set `LLAMA_N_GPU_LAYERS = 35`

**Q: Can I delete checkpoint files?**  
A: They are automatically cleared after task completion, or you can manually delete the `checkpoints/` directory

**Q: How to verify installation?**  
A: Run `python verify_setup.py`

---

## Changelog

### v1.1.0 (2025-11-10)
- ✅ Added standard dependency management (requirements.txt)
- ✅ Standardized code style and type annotations
- ✅ Refactored configuration loading logic
- ✅ Added comprehensive unit tests (52 test cases)
- ✅ Improved documentation and development tools

### v1.0.0 (2025-11-06)
- ✅ Initial release
- ✅ GUI and command-line interface
- ✅ Batch prediction and checkpoint resume
- ✅ Multi-process parallel processing

---

## License

This project is licensed under the [MIT License](LICENSE).

**Disclaimer**: This tool is for learning and research purposes only and should not be used for clinical diagnosis. Users assume all risks and responsibilities associated with using this tool.
