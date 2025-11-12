#!/usr/bin/env python3
"""
准备Qwen模型微调数据
功能：
1. 读取train.xlsx
2. 应用预处理函数
3. 转换为Qwen对话格式
4. 添加负样本（无病灶的情况）
5. 保存为JSONL格式
"""

import pandas as pd
import json
import re
from typing import List, Dict

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
    删除中英文括号内包含 lm/im/img（不区分大小写）的片段，
    但仅当整个括号片段长度 ≤ 20 字符。
    """
    if not text:
        return text

    def replacer(match: re.Match) -> str:
        # match.group(0) 是整个括号片段，如 "(IMG79/80)" 或 "（img123）"
        if len(match.group(0)) <= 20:
            return ""
        return match.group(0)  # 太长，保留原样

    # 匹配最内层或外层括号均可，这里用非贪婪匹配括号内容
    pattern = r'[（(][^)）]*?(?:lm|im|img)[^)）]*?[)）]'
    return re.sub(pattern, replacer, text, flags=re.IGNORECASE)

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

# 预编译正则：把"数字+可选空白+单位"整体抓出来
_NUM_UNIT_RE = re.compile(r'(\d+\.?\d*)\s*(cm|mm|um|μm|m)?', flags=re.I)



def create_negative_samples() -> List[Dict]:
    """
    创建负样本（没有肺部病灶或没有尺寸信息的情况）
    """
    negative_samples = [
        {
            "input": "肝脏形态大小正常，肝实质密度均匀，肝内外胆管未见扩张。门静脉主干及属支显示清晰，管径正常。",
            "output": "0"
        },
        {
            "input": "脾脏形态大小正常，密度均匀。胰腺形态大小正常，胰管未见扩张。",
            "output": "0"
        },
        {
            "input": "双肾形态、大小正常，肾盂、肾盏无扩张。双侧输尿管未见扩张。膀胱充盈好，壁光滑。",
            "output": "0"
        },
        {
            "input": "气管居中，两肺纹理清晰，未见明确异常密度影。双侧胸膜未见增厚，胸腔未见积液。",
            "output": "0"
        },
        {
            "input": "双肺纹理清晰，肺野清晰，未见异常密度影。气管及支气管通畅。纵隔居中，心影大小形态正常。",
            "output": "0"
        },
        {
            "input": "两肺透亮度正常，肺纹理走行自然，未见明显异常。肺门不大，纵隔无移位。",
            "output": "0"
        },
        {
            "input": "胸廓对称，气管居中。两肺散在斑片影及条索影，考虑炎症。未见明确占位性病变。",
            "output": "0"
        },
        {
            "input": "双肺未见明显实性结节影。两肺少许纤维条索影。肺门及纵隔淋巴结未见肿大。",
            "output": "0"
        },
        {
            "input": "平扫显示胸廓对称，两肺纹理增多、紊乱，双肺散在斑片状模糊影，考虑炎性病变。所示支气管通畅。",
            "output": "0"
        },
        {
            "input": "两肺散在少许炎症，未见明确结节或肿块。胸膜未见增厚，胸腔未见积液。心影大小正常。",
            "output": "0"
        },
        {
            "input": "肝脏内见多发类圆形低密度影，较大者位于右肝，大小约30×25mm，考虑囊肿。",
            "output": "0"
        },
        {
            "input": "右肾见结石影，大小约8mm。左肾未见明显异常。",
            "output": "0"
        },
    ]
    
    return negative_samples


def convert_to_qwen_format(input_text: str, output_value: str, system_prompt: str) -> Dict:
    """
    转换为Qwen模型的对话格式
    """
    return {
        "messages": [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": f"影像报告：{input_text}\n\n请提取报告中最大的病灶尺寸（mm）："
            },
            {
                "role": "assistant",
                "content": output_value
            }
        ]
    }


def main():
    print("=" * 60)
    print("准备Qwen模型微调数据")
    print("=" * 60)
    
    # 系统提示词
    system_prompt = """
你是医疗信息提取助手。我需要你从影像表现的报告中，找到肺部病灶（包括肺上叶中叶下叶的结节、磨玻璃结节、团块或局灶影，不包括空洞，不包括纵隔肿物）的最大直径，可能是“长径”、“直径”、“大小”中的最大一项。如果有多个病灶，只需要最长的。返回的结果以mm为单位，如果是cm你需要进行转换，1cm=10mm。忽略CT值（HU）。  报告中其他部位和系统（如肝，肾，脾）的病灶请无视。如果报告中没有肺部病灶，或者没有具体的尺寸信息，请输出0。你的输出结果只需要输出最终的数字，不需要任何的单位或者前置描述。
"""



    # 1. 读取原始数据
    print("\n1. 读取训练数据...")
    df = pd.read_excel('./train_new.xlsx')
    print(f"   ✓ 读取成功: {len(df)} 条正样本")
    
    # 2. 预处理并转换格式
    print("\n2. 预处理数据...")
    training_data = []
    
    for idx, row in df.iterrows():
        # 预处理输入文本
        processed_input = filter_segments(remove_img_tags(preprocessing(row['yxbx'])))

        # 确保输出是标准格式（整数或一位小数）
        output_value = row['max_nodule']
        if output_value == int(output_value):
            output_str = str(int(output_value))
        else:
            output_str = f"{output_value:.1f}"
        
        # 转换为对话格式
        sample = convert_to_qwen_format(processed_input, output_str, system_prompt)
        training_data.append(sample)
    
    print(f"   ✓ 预处理完成: {len(training_data)} 条")
    
    # 3. 添加负样本
    print("\n3. 添加负样本...")
    negative_samples = create_negative_samples()
    for neg_sample in negative_samples:
        processed_input = filter_segments(remove_img_tags(preprocessing(neg_sample['input'])))
        sample = convert_to_qwen_format(processed_input, neg_sample['output'], system_prompt)
        training_data.append(sample)
    
    print(f"   ✓ 添加了 {len(negative_samples)} 条负样本")
    print(f"   ✓ 总样本数: {len(training_data)} 条")
    
    # 4. 数据统计
    print("\n4. 数据统计:")
    positive_count = len(df)
    negative_count = len(negative_samples)
    print(f"   - 正样本（有病灶）: {positive_count} 条 ({positive_count/len(training_data)*100:.1f}%)")
    print(f"   - 负样本（无病灶）: {negative_count} 条 ({negative_count/len(training_data)*100:.1f}%)")
    
    # 5. 保存为JSONL格式
    output_file = './train_data.jsonl'
    print(f"\n5. 保存训练数据到: {output_file}")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for sample in training_data:
            f.write(json.dumps(sample, ensure_ascii=False) + '\n')
    
    print(f"   ✓ 保存成功")
    
    # 6. 显示样本示例
    print("\n6. 样本示例:")
    print("-" * 60)
    print("\n【正样本示例】")
    print(json.dumps(training_data[0], ensure_ascii=False, indent=2))
    print("\n【负样本示例】")
    print(json.dumps(training_data[-1], ensure_ascii=False, indent=2))
    print("-" * 60)
    
    print("\n✓ 数据准备完成！")
    print(f"\n下一步: 使用 {output_file} 进行模型微调")


if __name__ == "__main__":
    main()