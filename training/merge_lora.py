#!/usr/bin/env python3
"""
一键把 LoRA 权重合并回基础模型并保存为完整 transformers 模型
零参数版：直接 python merge_lora.py 即可跑
"""
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

# ==========  需要改的只有这里  ==========
BASE_MODEL_PATH = "./models/Qwen2.5-3B-Instruct"   # 原模型目录
LORA_PATH       = "./qwen-medical-lora-nounsloth_251106"  # LoRA 输出目录
SAVE_PATH       = "./qwen-medical-251106-lora-merged"     # 合并后保存目录
TORCH_DTYPE     = torch.bfloat16                  # 可选 torch.float16 / torch.float32
DEVICE_MAP      = "auto"                          # 按需调整
# ========================================

def main():
    print("⏳ 1. 加载 tokenizer")
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_PATH, trust_remote_code=True)

    print("⏳ 2. 加载基础模型")
    base_model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL_PATH,
        torch_dtype=TORCH_DTYPE,
        device_map=DEVICE_MAP,
        trust_remote_code=True,
    )

    print("⏳ 3. 挂 LoRA 并合并")
    model = PeftModel.from_pretrained(base_model, LORA_PATH)
    model = model.merge_and_unload()
    print("✅ 合并完成")

    print("⏳ 4. 保存完整模型")
    model.save_pretrained(SAVE_PATH)
    tokenizer.save_pretrained(SAVE_PATH)
    print(f"✅ 已保存至 {SAVE_PATH}")

if __name__ == "__main__":
    main()