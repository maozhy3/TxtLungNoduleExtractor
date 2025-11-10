"""
文本预处理功能测试
"""
import pytest
from core import filter_segments, remove_img_tags, preprocessing


class TestFilterSegments:
    """测试 filter_segments 函数"""
    
    def test_basic_filtering(self):
        """测试基本的片段过滤"""
        text = "右肺上叶见结节影，大小约8mm。左肺下叶未见异常。"
        result = filter_segments(text)
        assert "8mm" in result
        assert "右肺上叶" in result
    
    def test_no_lung_keywords(self):
        """测试不包含肺部关键词的文本"""
        text = "心脏正常。肝脏正常。"
        result = filter_segments(text)
        assert result == ""
    
    def test_no_numbers(self):
        """测试不包含数字的文本"""
        text = "右肺上叶见结节影。"
        result = filter_segments(text)
        assert result == ""
    
    def test_multiple_segments(self):
        """测试多个片段"""
        text = "右肺上叶见结节影，大小约8mm；左肺下叶见磨玻璃影，直径12mm。心脏正常。"
        result = filter_segments(text)
        assert "8mm" in result
        assert "12mm" in result
        assert "心脏正常" not in result
    
    def test_empty_input(self):
        """测试空输入"""
        result = filter_segments("")
        assert result == ""


class TestRemoveImgTags:
    """测试 remove_img_tags 函数"""
    
    def test_remove_short_img_tag(self):
        """测试删除短的图像标签"""
        text = "右肺上叶见结节影(img1)，大小约8mm"
        result = remove_img_tags(text)
        assert "img1" not in result
        assert "右肺上叶" in result
        assert "8mm" in result
    
    def test_keep_long_content(self):
        """测试保留长内容（即使包含img）"""
        text = "右肺上叶见结节影(这是一段很长的描述包含img但是超过20个字符所以应该保留)，大小约8mm"
        result = remove_img_tags(text)
        assert "img" in result  # 长内容应该保留
    
    def test_case_insensitive(self):
        """测试大小写不敏感"""
        text = "右肺上叶见结节影(IMG1)，大小约8mm"
        result = remove_img_tags(text)
        assert "IMG1" not in result
    
    def test_chinese_brackets(self):
        """测试中文括号"""
        text = "右肺上叶见结节影（img1），大小约8mm"
        result = remove_img_tags(text)
        assert "img1" not in result
    
    def test_lm_and_im(self):
        """测试lm和im标签"""
        text = "右肺上叶见结节影(lm1)，左肺下叶(im2)，大小约8mm"
        result = remove_img_tags(text)
        assert "lm1" not in result
        assert "im2" not in result
    
    def test_empty_input(self):
        """测试空输入"""
        result = remove_img_tags("")
        assert result == ""


class TestPreprocessing:
    """测试 preprocessing 函数"""
    
    def test_normalize_multiplication_signs(self):
        """测试标准化乘号"""
        text = "结节大小8x10mm"
        result = preprocessing(text)
        assert "×" in result
        assert "x" not in result.lower() or "8×10mm" in result
    
    def test_convert_dimension_format(self):
        """测试转换尺寸格式"""
        text = "结节大小8×10mm"
        result = preprocessing(text)
        assert "8mm×10mm" in result or "8mm" in result
    
    def test_remove_spaces(self):
        """测试删除空格"""
        text = "结节 大小 8 mm"
        result = preprocessing(text)
        assert " " not in result or result.count(" ") < text.count(" ")
    
    def test_remove_newlines(self):
        """测试删除换行符"""
        text = "结节大小\n8mm"
        result = preprocessing(text)
        assert "\n" not in result
    
    def test_remove_brn(self):
        """测试删除(brn)标记"""
        text = "结节大小8mm(brn)"
        result = preprocessing(text)
        assert "brn" not in result
    
    def test_complex_input(self):
        """测试复杂输入"""
        text = "右肺上叶见结节影 8 X 10 mm，左肺下叶 12 * 15 cm\n(brn)"
        result = preprocessing(text)
        assert "×" in result
        assert "brn" not in result
        assert "\n" not in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
