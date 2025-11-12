# Lung Nodule Size Extraction Tool

[中文](../README.md) | English

An automated lung nodule size extraction tool based on llama.cpp and Qwen medical model, supporting intelligent extraction of maximum lesion diameter from imaging reports.

> **Platform Support**: Currently only supports Windows platform. Linux/Mac users can run from source code.

## Features

- 🖥️ Both GUI and command-line interfaces
- 🔍 Intelligent text preprocessing and numerical extraction
- 🚀 Single-process/multi-process parallel inference
- 💾 Checkpoint resume functionality
- 📊 Batch processing of Excel data

![GUI Interface](images/gui-screenshot.png)

---

## Quick Start

### 1. Install Dependencies

```bash
# Create virtual environment (recommended)
conda create -n lung-nodule python=3.10
conda activate lung-nodule

# Install dependencies
pip install -r requirements.txt
```

**Windows users need to install VC++ runtime**: https://aka.ms/vs/17/release/vc_redist.x64.exe

### 2. Download Model

```bash
python download_model.py
```

Recommended models:
- **Qwen2.5-3B** (~2GB) - Fast, suitable for testing
- **Qwen2.5-7B** (~4.7GB) - Better performance, recommended

### 3. Run the Program

```bash
# GUI (Recommended)
python gui.py

# Command Line
python main.py
```

---

## Configuration

### Configuration Files

The project supports three-layer configuration override (priority from low to high):

1. **config.py** - Default configuration (committed to git)
2. **config_private.py** - Personal configuration (not committed to git) ⭐ Recommended
3. **External config.py** - Can be created in the same directory as exe after packaging

### Quick Configuration

Copy the example file and edit:

```bash
copy config_private.py.example config_private.py
```

```python
# config_private.py - Only write configuration items you want to override

# Model path
MODEL_PATHS = ["models/qwen2.5-7b-instruct-q4_k_m.gguf"]

# Performance settings
LLAMA_N_THREADS = 8        # CPU threads
LLAMA_N_GPU_LAYERS = 0     # GPU layers (0=CPU only)
PROCESS_POOL_MAX_WORKERS = 1  # Number of processes

# Feature extraction (optional)
ENABLE_FEATURE_EXTRACTION = False
```

### Performance Recommendations

- Low-end (4 cores, 8GB): `PROCESS_POOL_MAX_WORKERS=1, LLAMA_N_THREADS=4`
- Mid-range (8 cores, 16GB): `PROCESS_POOL_MAX_WORKERS=2, LLAMA_N_THREADS=4`
- High-end (16 cores, 32GB): `PROCESS_POOL_MAX_WORKERS=4, LLAMA_N_THREADS=4`

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

Press `Ctrl+C` to interrupt, checkpoint automatically saved to `checkpoints/`, run again to continue from last interruption.

---

## Packaging and Deployment

For detailed packaging instructions, see [Deployment Guide](DEPLOYMENT.md).

### Quick Packaging

```bash
# GUI version (recommended)
build_gui.bat

# Command-line version
build_main.bat
```

Output directory: `dist/医疗影像报告预测工具/`

> **Note**: Release version does not include model files, need to download manually and place in `models/` directory.

---

## Development Guide

### Project Structure

```
.
├── main.py              # Command-line entry
├── gui.py               # GUI entry
├── core.py              # Core logic
├── config.py            # Default configuration
├── config_loader.py     # Configuration loader
├── download_model.py    # Model downloader
├── tests/               # Test files
├── models/              # Model directory
└── checkpoints/         # Checkpoint directory
```

### Run Tests

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

---

## FAQ

**Q: Failed to install llama-cpp-python?**  
A: Make sure VC++ runtime is installed

**Q: Out of memory?**  
A: Set `PROCESS_POOL_MAX_WORKERS = 1`

**Q: How to use GPU?**  
A: Install CUDA version of llama-cpp-python, set `LLAMA_N_GPU_LAYERS = 35`

---

## Changelog

### v1.2.0 (2025-11-12)
- ✅ Optimized packaging process: no longer automatically copies all model files during packaging
- ✅ Improved user experience: users can manually select models to deploy as needed
- ✅ Reduced release package size: avoids packaging unnecessary large model files

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
