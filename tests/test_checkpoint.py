"""
检查点功能测试
"""
import pytest
from pathlib import Path
from core import CheckpointManager


class TestCheckpointManager:
    """测试 CheckpointManager 类"""
    
    @pytest.fixture
    def temp_checkpoint_dir(self, tmp_path):
        """创建临时检查点目录"""
        return tmp_path / "test_checkpoints"
    
    @pytest.fixture
    def manager(self, temp_checkpoint_dir):
        """创建检查点管理器实例"""
        return CheckpointManager(checkpoint_dir=temp_checkpoint_dir, save_interval=5)
    
    def test_init(self, manager, temp_checkpoint_dir):
        """测试初始化"""
        assert manager.checkpoint_dir == temp_checkpoint_dir
        assert manager.save_interval == 5
        assert temp_checkpoint_dir.exists()
    
    def test_get_checkpoint_path(self, manager):
        """测试获取检查点路径"""
        model_name = "test_model"
        path = manager.get_checkpoint_path(model_name)
        assert path.name == f"{model_name}_checkpoint.pkl"
        assert path.parent == manager.checkpoint_dir
    
    def test_save_and_load_checkpoint(self, manager):
        """测试保存和加载检查点"""
        model_name = "test_model"
        predictions = [1, 2, 3, None, 5]
        processed_indices = {0, 1, 2, 4}
        total_time = 10.5
        
        # 保存检查点
        manager.save_checkpoint(model_name, predictions, processed_indices, total_time)
        
        # 加载检查点
        checkpoint = manager.load_checkpoint(model_name)
        
        assert checkpoint is not None
        assert checkpoint['predictions'] == predictions
        assert checkpoint['processed_indices'] == processed_indices
        assert checkpoint['total_time'] == total_time
        assert 'timestamp' in checkpoint
    
    def test_load_nonexistent_checkpoint(self, manager):
        """测试加载不存在的检查点"""
        checkpoint = manager.load_checkpoint("nonexistent_model")
        assert checkpoint is None
    
    def test_clear_checkpoint(self, manager):
        """测试清除检查点"""
        model_name = "test_model"
        predictions = [1, 2, 3]
        processed_indices = {0, 1, 2}
        total_time = 5.0
        
        # 保存检查点
        manager.save_checkpoint(model_name, predictions, processed_indices, total_time)
        checkpoint_path = manager.get_checkpoint_path(model_name)
        assert checkpoint_path.exists()
        
        # 清除检查点
        manager.clear_checkpoint(model_name)
        assert not checkpoint_path.exists()
    
    def test_clear_nonexistent_checkpoint(self, manager):
        """测试清除不存在的检查点（不应报错）"""
        manager.clear_checkpoint("nonexistent_model")
        # 不应抛出异常
    
    def test_overwrite_checkpoint(self, manager):
        """测试覆盖已存在的检查点"""
        model_name = "test_model"
        
        # 第一次保存
        manager.save_checkpoint(model_name, [1, 2], {0, 1}, 5.0)
        
        # 第二次保存（覆盖）
        manager.save_checkpoint(model_name, [1, 2, 3], {0, 1, 2}, 10.0)
        
        # 加载并验证
        checkpoint = manager.load_checkpoint(model_name)
        assert len(checkpoint['predictions']) == 3
        assert len(checkpoint['processed_indices']) == 3
        assert checkpoint['total_time'] == 10.0


class TestCheckpointIntegration:
    """测试检查点集成场景"""
    
    @pytest.fixture
    def manager(self, tmp_path):
        """创建检查点管理器"""
        return CheckpointManager(checkpoint_dir=tmp_path / "checkpoints", save_interval=2)
    
    def test_resume_from_checkpoint(self, manager):
        """测试从检查点恢复"""
        model_name = "test_model"
        total_items = 10
        
        # 模拟处理一半后中断
        predictions = [i if i < 5 else None for i in range(total_items)]
        processed_indices = set(range(5))
        total_time = 5.0
        
        manager.save_checkpoint(model_name, predictions, processed_indices, total_time)
        
        # 模拟恢复
        checkpoint = manager.load_checkpoint(model_name)
        assert checkpoint is not None
        
        # 继续处理剩余部分
        remaining = total_items - len(checkpoint['processed_indices'])
        assert remaining == 5
        
        # 验证已处理的索引
        for idx in range(5):
            assert idx in checkpoint['processed_indices']
        for idx in range(5, 10):
            assert idx not in checkpoint['processed_indices']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
