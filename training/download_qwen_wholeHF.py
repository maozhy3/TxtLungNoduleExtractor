#!/usr/bin/env python3
"""
从国内镜像下载 Qwen2.5-3B-Instruct 模型
支持多个国内镜像源，自动重试和断点续传
"""

import os
import sys
from pathlib import Path

def download_with_huggingface_hub():
    """使用 huggingface_hub 库从镜像下载"""
    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        print("正在安装 huggingface_hub...")
        os.system(f"{sys.executable} -m pip install huggingface_hub --break-system-packages")
        from huggingface_hub import snapshot_download
    
    model_name = "Qwen/Qwen2.5-3B-Instruct"
    
    # 国内镜像源列表
    mirrors = [
        "https://hf-mirror.com",  # HF-Mirror (推荐)
        "https://mirror.sjtu.edu.cn/huggingface",  # 上海交大镜像
    ]
    
    # 设置下载目录
    download_dir = "./models/Qwen2.5-3B-Instruct"
    
    print(f"开始下载模型: {model_name}")
    print(f"保存路径: {os.path.abspath(download_dir)}")
    print("=" * 60)
    
    for mirror in mirrors:
        try:
            print(f"\n尝试使用镜像: {mirror}")
            
            # 设置环境变量
            os.environ['HF_ENDPOINT'] = mirror
            
            # 下载模型
            local_dir = snapshot_download(
                repo_id=model_name,
                local_dir=download_dir,
                resume_download=True,  # 支持断点续传
                max_workers=4,  # 并行下载
            )
            
            print(f"\n✓ 下载完成！")
            print(f"模型保存在: {local_dir}")
            return True
            
        except Exception as e:
            print(f"✗ 使用 {mirror} 下载失败: {str(e)}")
            continue
    
    print("\n所有镜像源都失败了，请检查网络连接或稍后重试。")
    return False


def download_with_modelscope():
    """使用 modelscope 库下载（备选方案）"""
    try:
        from modelscope import snapshot_download
    except ImportError:
        print("正在安装 modelscope...")
        os.system(f"{sys.executable} -m pip install modelscope --break-system-packages")
        from modelscope import snapshot_download
    
    model_name = "Qwen/Qwen2.5-3B-Instruct"
    download_dir = "./models/Qwen2.5-3B-Instruct"
    
    print(f"\n使用 ModelScope 下载模型: {model_name}")
    print(f"保存路径: {os.path.abspath(download_dir)}")
    print("=" * 60)
    
    try:
        local_dir = snapshot_download(
            model_id=model_name,
            cache_dir=download_dir,
        )
        
        print(f"\n✓ 下载完成！")
        print(f"模型保存在: {local_dir}")
        return True
        
    except Exception as e:
        print(f"✗ ModelScope 下载失败: {str(e)}")
        return False


def main():
    print("=" * 60)
    print("Qwen2.5-3B-Instruct 模型下载工具")
    print("=" * 60)
    
    # 首选：使用 HuggingFace Hub + 国内镜像
    print("\n方案1: 使用 HuggingFace Hub + 国内镜像")
    if download_with_huggingface_hub():
        return
    
    # 备选：使用 ModelScope
    print("\n方案2: 使用 ModelScope 镜像")
    if download_with_modelscope():
        return
    
    print("\n下载失败，请检查网络连接或手动下载。")
    print("\n手动下载方法：")
    print("1. 访问 https://hf-mirror.com/Qwen/Qwen2.5-3B-Instruct")
    print("2. 或访问 https://modelscope.cn/models/Qwen/Qwen2.5-3B-Instruct")


if __name__ == "__main__":
    main()