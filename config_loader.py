"""
配置加载模块
支持默认配置和外部配置覆盖
"""
import os
import sys
import importlib.util
from pathlib import Path
from typing import Any


def get_base_path() -> Path:
    """
    获取基础路径，兼容开发环境和打包后的环境
    
    Returns:
        Path: 基础路径
    """
    if getattr(sys, 'frozen', False):
        # 打包后的环境
        return Path(sys.executable).parent
    else:
        # 开发环境
        return Path(__file__).parent


def load_config() -> Any:
    """
    加载配置，支持外部配置覆盖
    
    优先级：
    1. 外部配置文件（exe同级目录的config.py）
    2. 默认配置文件（内置的config.py）
    
    Returns:
        配置模块对象
    """
    # 导入默认配置
    import config as default_config
    
    # 尝试加载外部配置
    base_path = get_base_path()
    external_config_path = base_path / 'config.py'
    
    # 如果外部配置存在且不是默认配置本身
    if external_config_path.exists() and external_config_path != Path(default_config.__file__):
        try:
            spec = importlib.util.spec_from_file_location(
                "external_config", 
                external_config_path
            )
            external_config = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(external_config)
            
            # 用外部配置覆盖默认配置
            for key in dir(external_config):
                if not key.startswith('_'):
                    setattr(default_config, key, getattr(external_config, key))
            
            print(f"✓ 已加载外部配置: {external_config_path}")
        except Exception as e:
            print(f"⚠ 加载外部配置失败: {e}")
            print("使用默认配置")
    
    return default_config


def get_config_value(config: Any, key: str, default: Any = None) -> Any:
    """
    安全地获取配置值
    
    Args:
        config: 配置模块
        key: 配置键名
        default: 默认值
    
    Returns:
        配置值或默认值
    """
    return getattr(config, key, default)
