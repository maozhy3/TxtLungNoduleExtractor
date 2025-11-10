"""
核心业务逻辑模块
包含文本预处理、数值提取、模型预测等功能
"""
# 标准库
import pickle
import re
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Optional, Set, Tuple

# 第三方库
import pandas as pd
from llama_cpp import Llama
from tqdm import tqdm


# ==================== 文本预处理 ====================

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
        if len(match.group(0)) <= 20:
            return ""
        return match.group(0)

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


# ==================== 数值提取 ====================

# 预编译正则：把"数字+可选空白+单位"整体抓出来
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
    elif 3 <= max_val < 7 and has_cm and not has_mm:  
        max_val *= 10

    return int(max_val) if max_val.is_integer() else max_val


# ==================== 模型预测 ====================

def predict_single(llm: Llama, input_text: str, prompt_template: str) -> Tuple[Optional[float], float]:
    """
    对单个输入进行预测
    
    Args:
        llm: 已加载的模型实例
        input_text: 原始输入文本
        prompt_template: prompt模板
    
    Returns:
        (预测结果, 推理耗时)
    """
    # 预处理
    processed_input = input_text
    processed_input = preprocessing(processed_input)
    processed_input = remove_img_tags(processed_input)
    processed_input = filter_segments(processed_input)
    
    # 构建prompt
    prompt = prompt_template.format(processed_input=processed_input)
    
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


# ==================== 多进程支持 ====================

def _worker_init(model_path: str, n_ctx: int, n_threads: int, n_gpu_layers: int) -> None:
    """进程初始化：每个进程加载一次模型"""
    global _worker_llm, _worker_prompt_template
    _worker_llm = Llama(
        model_path=model_path,
        n_ctx=n_ctx,
        n_threads=n_threads,
        n_gpu_layers=n_gpu_layers,
        verbose=False,
    )


def _worker_predict(args: Tuple[int, str, str]) -> Tuple[int, Optional[float], float]:
    """工作进程：使用已加载的模型进行预测"""
    idx, input_text, prompt_template = args
    pred_value, infer_time = predict_single(_worker_llm, input_text, prompt_template)
    return idx, pred_value, infer_time


# ==================== 检查点管理 ====================

class CheckpointManager:
    """管理预测进度的检查点"""
    
    def __init__(self, checkpoint_dir: Path = None, save_interval: int = 10):
        """
        Args:
            checkpoint_dir: 检查点保存目录
            save_interval: 每处理多少条数据保存一次检查点
        """
        self.checkpoint_dir = checkpoint_dir or Path("checkpoints")
        self.checkpoint_dir.mkdir(exist_ok=True)
        self.save_interval = save_interval
    
    def get_checkpoint_path(self, model_name: str) -> Path:
        """获取指定模型的检查点文件路径"""
        return self.checkpoint_dir / f"{model_name}_checkpoint.pkl"
    
    def save_checkpoint(
        self, 
        model_name: str, 
        predictions: list, 
        processed_indices: Set[int], 
        total_time: float
    ) -> None:
        """保存检查点"""
        checkpoint_path = self.get_checkpoint_path(model_name)
        checkpoint_data = {
            'predictions': predictions,
            'processed_indices': processed_indices,
            'total_time': total_time,
            'timestamp': time.time()
        }
        
        try:
            with open(checkpoint_path, 'wb') as f:
                pickle.dump(checkpoint_data, f)
        except Exception as e:
            print(f"⚠ 保存检查点失败: {e}")
    
    def load_checkpoint(self, model_name: str) -> Optional[dict[str, Any]]:
        """加载检查点"""
        checkpoint_path = self.get_checkpoint_path(model_name)
        
        if not checkpoint_path.exists():
            return None
        
        try:
            with open(checkpoint_path, 'rb') as f:
                checkpoint_data = pickle.load(f)
            return checkpoint_data
        except Exception as e:
            print(f"⚠ 加载检查点失败: {e}")
            return None
    
    def clear_checkpoint(self, model_name: str) -> None:
        """清除检查点文件"""
        checkpoint_path = self.get_checkpoint_path(model_name)
        if checkpoint_path.exists():
            try:
                checkpoint_path.unlink()
            except Exception as e:
                print(f"⚠ 删除检查点失败: {e}")


# ==================== 批量预测 ====================

def batch_predict(df: pd.DataFrame, model_path: str, config: Any) -> Tuple[list, float, str]:
    """
    批量预测（支持断点续传）
    
    Args:
        df: 包含测试数据的DataFrame
        model_path: 模型文件路径
        config: 配置模块
    
    Returns:
        (预测结果列表, 总耗时, 模型名称)
    """
    model_name = Path(model_path).stem
    
    print(f"\n{'=' * 80}")
    print(f"模型: {model_name}")
    print(f"{'=' * 80}")
    
    # 初始化检查点管理器
    save_interval = getattr(config, 'CHECKPOINT_SAVE_INTERVAL', 10)
    checkpoint_manager = CheckpointManager(save_interval=save_interval)
    
    # 尝试加载检查点
    checkpoint = checkpoint_manager.load_checkpoint(model_name)
    if checkpoint:
        predictions = checkpoint['predictions']
        processed_indices = checkpoint['processed_indices']
        total_time = checkpoint['total_time']
        remaining = len(df) - len(processed_indices)
        print(f"✓ 检测到检查点，已完成 {len(processed_indices)}/{len(df)} 条，继续处理剩余 {remaining} 条")
    else:
        predictions = [None] * len(df)
        processed_indices = set()
        total_time = 0
        print(f"开始新的预测任务（共 {len(df)} 条）")
    
    max_workers = getattr(config, 'PROCESS_POOL_MAX_WORKERS', 1)
    
    if max_workers <= 1:
        # 单进程模式
        print("正在加载模型...")
        try:
            llm = Llama(
                model_path=model_path,
                n_ctx=config.LLAMA_N_CTX,
                n_threads=config.LLAMA_N_THREADS,
                n_gpu_layers=config.LLAMA_N_GPU_LAYERS,
                verbose=config.LLAMA_VERBOSE,
            )
            print("✓ 模型加载成功")
        except Exception as e:
            print(f"❌ 模型加载失败: {e}")
            return None, 0.0, model_name
        
        print(f"正在进行批量预测...")
        print("-" * 80)
        
        processed_count = 0
        try:
            for idx, row in tqdm(df.iterrows(), total=len(df), desc="预测进度", initial=len(processed_indices)):
                # 跳过已处理的数据
                if idx in processed_indices:
                    continue
                
                input_text = str(row['yxbx'])
                pred_value, infer_time = predict_single(llm, input_text, config.PROMPT_TEMPLATE)
                predictions[idx] = pred_value
                total_time += infer_time
                processed_indices.add(idx)
                processed_count += 1
                
                # 周期性保存检查点
                if processed_count % save_interval == 0:
                    checkpoint_manager.save_checkpoint(
                        model_name, predictions, processed_indices, total_time
                    )
        except KeyboardInterrupt:
            print("\n⚠ 检测到中断信号，正在保存检查点...")
            checkpoint_manager.save_checkpoint(
                model_name, predictions, processed_indices, total_time
            )
            print("✓ 检查点已保存，可以稍后继续运行")
            raise
        except Exception as e:
            print(f"\n❌ 预测过程出错: {e}")
            print("正在保存检查点...")
            checkpoint_manager.save_checkpoint(
                model_name, predictions, processed_indices, total_time
            )
            print("✓ 检查点已保存")
            raise
    else:
        # 多进程模式
        print(f"正在启动 {max_workers} 个进程并加载模型...")
        print("-" * 80)
        
        # 只处理未完成的任务
        tasks = [(idx, str(row['yxbx']), config.PROMPT_TEMPLATE) 
                 for idx, row in df.iterrows() if idx not in processed_indices]
        
        if not tasks:
            print("✓ 所有数据已处理完成")
        else:
            processed_count = 0
            try:
                with ProcessPoolExecutor(
                    max_workers=max_workers,
                    initializer=_worker_init,
                    initargs=(model_path, config.LLAMA_N_CTX, config.LLAMA_N_THREADS, config.LLAMA_N_GPU_LAYERS)
                ) as executor:
                    futures = {executor.submit(_worker_predict, task): task for task in tasks}
                    
                    for future in tqdm(as_completed(futures), total=len(tasks), desc="预测进度", initial=len(processed_indices)):
                        idx, pred_value, infer_time = future.result()
                        predictions[idx] = pred_value
                        total_time += infer_time
                        processed_indices.add(idx)
                        processed_count += 1
                        
                        # 周期性保存检查点
                        if processed_count % save_interval == 0:
                            checkpoint_manager.save_checkpoint(
                                model_name, predictions, processed_indices, total_time
                            )
            except KeyboardInterrupt:
                print("\n⚠ 检测到中断信号，正在保存检查点...")
                checkpoint_manager.save_checkpoint(
                    model_name, predictions, processed_indices, total_time
                )
                print("✓ 检查点已保存，可以稍后继续运行")
                raise
            except Exception as e:
                print(f"\n❌ 预测过程出错: {e}")
                print("正在保存检查点...")
                checkpoint_manager.save_checkpoint(
                    model_name, predictions, processed_indices, total_time
                )
                print("✓ 检查点已保存")
                raise

    # 最终保存检查点
    checkpoint_manager.save_checkpoint(
        model_name, predictions, processed_indices, total_time
    )
    
    avg_time = total_time / len(df) if len(df) > 0 else 0
    print("-" * 80)
    print(f"✓ 预测完成！总耗时: {total_time:.2f}s，平均耗时: {avg_time:.3f}s")
    
    # 完成后清除检查点
    checkpoint_manager.clear_checkpoint(model_name)
        
    return predictions, total_time, model_name
