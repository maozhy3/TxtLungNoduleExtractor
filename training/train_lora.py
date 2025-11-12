
#!/usr/bin/env python3
"""
LoRA 微调 Qwen2.5-3B-Instruct
不依赖 unsloth，纯官方组件
"""
import json, os, torch
from datasets import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TrainingArguments,
    BitsAndBytesConfig,
)
from peft import LoraConfig, get_peft_model, TaskType
from trl import SFTTrainer, SFTConfig

MODEL_NAME = "./models/Qwen2.5-3B-Instruct"   # 本地路径或 HuggingFace hub
DATA_PATH  = "./train_data.jsonl"
OUTPUT_DIR = "./qwen-medical-lora-nounsloth_251106"

# ---------- 1. 4-bit 量化 ----------
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True,
)

# ---------- 2. 加载模型 / Tokenizer ----------
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
tokenizer.pad_token = tokenizer.eos_token
assert tokenizer is not None, "tokenizer 加载失败"

model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    quantization_config=bnb_config,
    device_map="auto",
    trust_remote_code=True,
    use_cache=False,               # 开启 gradient checkpoint 时需关闭
    attn_implementation="sdpa",  # 若安装过 flash-attn
)

# ---------- 3. LoRA 配置 ----------
lora_config = LoraConfig(
    task_type=TaskType.CAUSAL_LM,
    r=16,
    lora_alpha=16,
    lora_dropout=0.05,
    target_modules=[
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj",
    ],
)

model = get_peft_model(model, lora_config)
model.print_trainable_parameters()

# ---------- 4. 数据 ----------
def load_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f]

def format_chat(sample):
    """与 unsloth 脚本保持一致的 chat template"""
    msgs = sample["messages"]
    text = ""
    for m in msgs:
        text += f"<|im_start|>{m['role']}\n{m['content']}<|im_end|>\n"
    return {"text": text}

raw_ds = Dataset.from_list(load_jsonl(DATA_PATH))
train_ds = raw_ds.map(format_chat, remove_columns=raw_ds.column_names)

# ---------- 5. 训练参数 ----------
training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    per_device_train_batch_size=2,
    gradient_accumulation_steps=4,
    num_train_epochs=10,
    learning_rate=2e-4,
    warmup_steps=10,
    logging_steps=5,
    save_steps=50,
    save_total_limit=3,
    bf16=torch.cuda.is_bf16_supported(),
    fp16=not torch.cuda.is_bf16_supported(),
    optim="adamw_8bit",
    weight_decay=0.01,
    lr_scheduler_type="cosine",
    report_to="none",
    gradient_checkpointing=True,      # 省显存
)

# ---------- 6. 训练 ----------
trainer = SFTTrainer(
    model=model,
    args=training_args,
    train_dataset=train_ds,
    # tokenizer=tokenizer,
    # max_seq_length=2048,
    # dataset_text_field="text",
)
trainer.train()

# ---------- 7. 保存 ----------
trainer.save_model(OUTPUT_DIR)          # LoRA 权重
tokenizer.save_pretrained(OUTPUT_DIR)
