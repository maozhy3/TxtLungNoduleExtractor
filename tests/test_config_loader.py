"""
配置加载模块测试
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestGetBasePath:
    """测试 get_base_path 函数"""
    
    def test_development_environment(self):
        """测试开发环境"""
        from config_loader import get_base_path
        
        # 在开发环境中，应该返回当前文件的父目录
        base_path = get_base_path()
        assert isinstance(base_path, Path)
        assert base_path.exists()
    
    @patch('sys.frozen', True, create=True)
    @patch('sys.executable', '/path/to/app.exe')
    def test_frozen_environment(self):
        """测试打包环境"""
        from config_loader import get_base_path
        
        base_path = get_base_path()
        assert base_path == Path('/path/to')


class TestLoadConfig:
    """测试 load_config 函数"""
    
    def test_load_default_config(self):
        """测试加载默认配置"""
        from config_loader import load_config
        
        config = load_config()
        
        # 验证配置对象存在
        assert config is not None
        
        # 验证基本配置项存在
        assert hasattr(config, 'EXCEL_PATH')
        assert hasattr(config, 'OUTPUT_PATH')
        assert hasattr(config, 'MODEL_PATHS')
        assert hasattr(config, 'LLAMA_N_CTX')
        assert hasattr(config, 'LLAMA_N_THREADS')
    
    def test_config_values_types(self):
        """测试配置值的类型"""
        from config_loader import load_config
        
        config = load_config()
        
        # 验证配置值类型
        assert isinstance(config.LLAMA_N_CTX, int)
        assert isinstance(config.LLAMA_N_THREADS, int)
        assert isinstance(config.LLAMA_N_GPU_LAYERS, int)
        assert isinstance(config.MODEL_PATHS, list)


class TestGetConfigValue:
    """测试 get_config_value 函数"""
    
    def test_get_existing_value(self):
        """测试获取存在的配置值"""
        from config_loader import get_config_value, load_config
        
        config = load_config()
        value = get_config_value(config, 'LLAMA_N_CTX')
        
        assert value is not None
        assert isinstance(value, int)
    
    def test_get_nonexistent_value_with_default(self):
        """测试获取不存在的配置值（使用默认值）"""
        from config_loader import get_config_value, load_config
        
        config = load_config()
        default_value = 9999
        value = get_config_value(config, 'NONEXISTENT_KEY', default_value)
        
        assert value == default_value
    
    def test_get_nonexistent_value_without_default(self):
        """测试获取不存在的配置值（无默认值）"""
        from config_loader import get_config_value, load_config
        
        config = load_config()
        value = get_config_value(config, 'NONEXISTENT_KEY')
        
        assert value is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
