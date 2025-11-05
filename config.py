# config.py
import os
from pathlib import Path

# ===== 输入输出 =====
EXCEL_PATH      = Path(__file__).with_name("test.xlsx")      # 待预测文件
OUTPUT_PATH     = Path(__file__).with_name("test_results4.xlsx")  # 结果保存

# ===== 模型列表 =====
# 支持单个字符串或列表；也可使用通配符，由脚本自动展开
_ROOT = Path(__file__).parent
MODEL_PATHS = [
    (_ROOT / "models" / "qwen-medical-q4km.gguf").as_posix()
]
# ===== llama.cpp 推理参数 =====
LLAMA_N_CTX        = 2048   # 上下文长度
LLAMA_N_THREADS    = 8      # CPU 线程数
LLAMA_N_GPU_LAYERS = 0      # 0 表示纯 CPU；>0 表示 offload 到 GPU 的层数
LLAMA_VERBOSE      = False  # 是否打印 llama.cpp 的 debug 信息
LLAMA_N_PARALLEL = 6          # 同时 6 条
LLAMA_BATCH_TIMEOUT = 60      # 60 s 超时