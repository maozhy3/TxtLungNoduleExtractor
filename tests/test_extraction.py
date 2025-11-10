"""
数值提取功能测试
"""
import pytest
from core import extract_max_value


class TestExtractMaxValue:
    """测试 extract_max_value 函数"""
    
    def test_extract_mm_value(self):
        """测试提取mm单位的数值"""
        text = "8mm"
        result = extract_max_value(text, text)
        assert result == 8
    
    def test_extract_cm_value(self):
        """测试提取cm单位的数值（应转换为mm）"""
        text = "1.2cm"
        result = extract_max_value(text, text)
        assert result == 12
    
    def test_extract_multiple_values(self):
        """测试提取多个数值（返回最大值）"""
        text = "8mm×10mm"
        result = extract_max_value(text, text)
        assert result == 10
    
    def test_extract_decimal_value(self):
        """测试提取小数"""
        text = "8.5mm"
        result = extract_max_value(text, text)
        assert result == 8.5
    
    def test_extract_cm_decimal(self):
        """测试提取cm小数"""
        text = "1.5cm"
        result = extract_max_value(text, text)
        assert result == 15
    
    def test_no_unit(self):
        """测试无单位的数字"""
        text = "8"
        result = extract_max_value(text, text)
        assert result == 8
    
    def test_small_value_with_cm(self):
        """测试小数值但原文有cm（应乘10）"""
        text = "2"
        raw_text = "结节大小约2cm"
        result = extract_max_value(text, raw_text)
        assert result == 20
    
    def test_ambiguous_value_with_cm(self):
        """测试模糊数值（3-7之间）有cm无mm"""
        text = "5"
        raw_text = "结节大小约5cm"
        result = extract_max_value(text, raw_text)
        assert result == 50
    
    def test_ambiguous_value_with_both_units(self):
        """测试模糊数值但同时有cm和mm"""
        text = "5"
        raw_text = "结节大小约5cm或50mm"
        result = extract_max_value(text, raw_text)
        # 有mm时不应该乘10
        assert result == 5
    
    def test_no_numbers(self):
        """测试无数字"""
        text = "未见异常"
        result = extract_max_value(text, text)
        assert result is None
    
    def test_complex_text(self):
        """测试复杂文本"""
        text = "8mm×10mm×12mm"
        result = extract_max_value(text, text)
        assert result == 12
    
    def test_mixed_units(self):
        """测试混合单位"""
        text = "1.2cm×8mm"
        result = extract_max_value(text, text)
        assert result == 12  # 1.2cm = 12mm
    
    def test_chinese_units(self):
        """测试中文单位"""
        text = "8毫米"
        raw_text = "结节大小约8毫米"
        result = extract_max_value(text, raw_text)
        assert result == 8
    
    def test_chinese_cm(self):
        """测试中文厘米"""
        text = "1.2"
        raw_text = "结节大小约1.2厘米"
        result = extract_max_value(text, raw_text)
        assert result == 12


class TestEdgeCases:
    """测试边界情况"""
    
    def test_empty_string(self):
        """测试空字符串"""
        result = extract_max_value("", "")
        assert result is None
    
    def test_zero_value(self):
        """测试零值"""
        result = extract_max_value("0mm", "0mm")
        assert result == 0
    
    def test_very_large_value(self):
        """测试很大的数值"""
        result = extract_max_value("100mm", "100mm")
        assert result == 100
    
    def test_very_small_decimal(self):
        """测试很小的小数"""
        result = extract_max_value("0.5mm", "0.5mm")
        assert result == 0.5
    
    def test_whitespace_handling(self):
        """测试空格处理"""
        result = extract_max_value("8 mm", "8 mm")
        assert result == 8
    
    def test_multiple_spaces(self):
        """测试多个空格"""
        result = extract_max_value("8   mm", "8   mm")
        assert result == 8


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
