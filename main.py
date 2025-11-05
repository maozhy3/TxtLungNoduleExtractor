#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import re
import time
import pandas as pd
from tqdm import tqdm
from typing import Optional
from llama_cpp import Llama
from pathlib import Path
from config import LLAMA_N_CTX, LLAMA_N_THREADS, LLAMA_N_GPU_LAYERS, LLAMA_VERBOSE


def filter_segments(text: str) -> str:
    """
    将输入段落按"。"、"；"或";"分割，保留分隔符；
    仅保留同时包含("肺"|"膈"|"肋"|"气")和数字的片段；
    最后按原顺序拼接并返回。
    """
    parts = re.split(r'([。；;])', text)
    segments = [parts[i] + parts[i+1] for i in range(0, len(parts)-1, 2)]
    if len(parts) % 2 == 1:
        segments.append(parts[-1])
    kept = []
    for seg in segments:
        if re.search(r'[肺膈肋气]', seg) and re.search(r'\d', seg):
            kept.append(seg)
    return ''.join(kept)

def remove_img_tags(text: str) -> str:
    """
    删除中英文括号内包含 lm/im/IMG（不区分大小写）+数字 的片段。
    """
    if not text:
        return text
    pattern = r'[（(](?:lm|im|img)\d+[)）]'
    return re.sub(pattern, '', text, flags=re.IGNORECASE)

def preprocessing(input: str) -> str:
    """预处理输入文本"""
    pattern = re.compile(r'(\d+(?:\.\d+)?)×(\d+(?:\.\d+)?)(mm|cm)')
    input = input.replace(" ", "").replace("\n", "").replace("(brn)", "").replace("（brn）", "")
    input = re.sub(r'[xX*\-~]', '×', input)
    def _repl(m: re.Match) -> str:
        n1, n2, unit = m.groups()
        return f"{n1}{unit}×{n2}{unit}"
    return pattern.sub(_repl, input)

import re
from typing import Optional

# 预编译正则：把“数字+可选空白+单位”整体抓出来
_NUM_UNIT_RE = re.compile(r'(\d+\.?\d*)\s*(cm|mm|um|μm|m)?', flags=re.I)

def _normalize(text: str) -> str:
    """统一中英文符号、去掉常见噪音"""
    return (text
            .replace('（', '(').replace('）', ')')
            .replace('×', 'x').replace('X', 'x')
            .replace('~', '-').replace('*', '-'))

def extract_max_value(text: str, raw_text: str = "") -> Optional[float]:
    """提取最大数值，cm×10→mm。若最终结果<2，则乘10。"""
    text = _normalize(text).replace("(brn)", "")
    numbers = []

    # 1) 带单位
    for val_str, unit in _NUM_UNIT_RE.findall(text):
        try:
            val = float(val_str)
        except ValueError:
            continue
        if unit and unit.lower() == "cm":
            val *= 10
        numbers.append(val)

    # 2) 兜底纯数字
    if not numbers:
        numbers = [float(m) for m in re.findall(r"\d+\.?\d*", text)]

    if not numbers:
        return None

    max_val = max(numbers)

    # 3) cm或mm最终校验
    has_cm = bool(re.search(r'cm', raw_text, flags=re.I)) or '厘米' in raw_text
    has_mm = bool(re.search(r'mm', raw_text, flags=re.I)) or '毫米' in raw_text

    if max_val < 3 and has_cm:                        
        max_val *= 10
    elif 3 <= max_val < 5 and has_cm and not has_mm:  
        max_val *= 10


    return int(max_val) if max_val.is_integer() else max_val


def predict_single(llm: Llama, input_text: str) -> tuple[Optional[float], float]:
    """
    对单个输入进行预测
    
    Returns:
        (预测结果, 推理耗时)
    """
    # 预处理
    processed_input = input_text
    processed_input = preprocessing(processed_input)
    processed_input = remove_img_tags(processed_input)
    processed_input = filter_segments(processed_input)
    
    # 构建prompt
    prompt = f"""<|im_start|>system
你是医疗信息提取助手。我需要你从影像表现的报告中，找到肺部病灶（包括结节、磨玻璃结节、团块、局灶影，不包括空洞）的最长径。如果有多个病灶，只需要最长的。请注意单位，我希望返回的结果以mm为单位，如果是cm你需要进行转换，1cm=10mm。报告中其他部位和系统（如肝，肾，脾）的病灶请无视。如果报告中没有肺部病灶，或者没有具体的尺寸信息，请输出0。你的输出结果只需要输出最终的数字，不需要任何的单位或者前置描述。<|im_end|>
<|im_start|>user
影像报告：{processed_input}

请提取报告中最大的病灶尺寸（mm）：<|im_end|>
<|im_start|>assistant
"""
    
    # 推理
    t0 = time.perf_counter()
    try:
        response = llm(
            prompt,
            max_tokens=10,
            temperature=0.1,
            top_p=0.9,
            stop=["<|im_end|>", "\n", "cm", "。"],
            echo=False,
        )
        t1 = time.perf_counter()
        
        raw_result = response['choices'][0]['text'].strip()
        final_result = extract_max_value(raw_result, input_text)
        
        return final_result, t1 - t0
    except Exception as e:
        print(f"预测失败: {e}")
        return None, 0.0


def batch_predict(df: pd.DataFrame, model_path: str) -> tuple[list, float, str]:
    """
    Args:
        df: 包含测试数据的DataFrame
        model_path: 模型文件路径
    Returns:
        (预测结果列表, 总耗时, 模型名称)
    """
    # 获取模型名称
    model_name = Path(model_path).stem
    
    print(f"\n{'=' * 80}")
    print(f"正在测试模型: {model_name}")
    print(f"{'=' * 80}")
    
    # 加载模型
    print("正在加载模型...")
    try:
        llm = Llama(
            model_path=model_path,
            n_ctx=LLAMA_N_CTX,
            n_threads=LLAMA_N_THREADS,
            n_gpu_layers=LLAMA_N_GPU_LAYERS,
            verbose=LLAMA_VERBOSE,
        )
        print("✓ 模型加载成功")
    except Exception as e:
        print(f"❌ 模型加载失败: {e}")
        return None, 0.0, model_name
    
    # 批量预测
    print(f"正在进行批量预测（共 {len(df)} 条）...")
    print("-" * 80)
    
    predictions = []
    total_time = 0
    

    for idx, row in tqdm(df.iterrows(), total=len(df), desc="预测进度"):
        input_text = str(row['yxbx'])
        
        # 预测
        pred_value, infer_time = predict_single(llm, input_text)
        predictions.append(pred_value)
        total_time += infer_time

    avg_time = total_time / len(df)
    print("-" * 80)
    print(f"✓ 预测完成！总耗时: {total_time:.2f}s，平均耗时: {avg_time:.3f}s")
        
    return predictions, total_time, model_name



def batch_run(excel_path: str, model_paths: list[str], output_path: Optional[str] = None) -> bool:
    # 保存结果
    print(f"\n正在保存结果到 {output_path}...")
    try:
        df.to_excel(output_path, index=False)
        print(f"✓ 结果已保存到: {output_path}")
    except Exception as e:
        print(f"❌ 保存失败: {e}")
        return False
    
    print("\n" + "=" * 80)
    print("测试完成！")
    print("=" * 80)
    
    return True


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from config import (EXCEL_PATH, MODEL_PATHS, OUTPUT_PATH,
                        LLAMA_N_CTX, LLAMA_N_THREADS, LLAMA_N_GPU_LAYERS,
                        LLAMA_VERBOSE)

    df = pd.read_excel(EXCEL_PATH)

    for model_path in MODEL_PATHS:
        preds, total_time, model_name = batch_predict(df, model_path)

        col_name = f"pred_{model_name}"
        df[col_name] = preds

        print(f"[{model_name}] 平均单条耗时: {total_time/len(df):.3f}s\n")


    df.to_excel(OUTPUT_PATH, index=False)
    print(f"✓ 全部预测完成，结果已保存至：{OUTPUT_PATH}")