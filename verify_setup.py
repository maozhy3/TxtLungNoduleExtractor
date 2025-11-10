#!/usr/bin/env python3
"""
验证项目设置脚本
检查所有依赖、配置和文件是否正确
"""
import sys
from pathlib import Path


def check_files():
    """检查必要文件是否存在"""
    print("检查文件...")
    required_files = [
        "main.py",
        "gui.py",
        "core.py",
        "config.py",
        "config_loader.py",
        "download_model.py",
        "requirements.txt",
        "requirements-dev.txt",
        "pyproject.toml",
        "pytest.ini",
        "README.md",
        "DEVELOPMENT.md",
        "CHANGELOG.md",
    ]
    
    missing = []
    for file in required_files:
        if not Path(file).exists():
            missing.append(file)
            print(f"  ❌ 缺失: {file}")
        else:
            print(f"  ✓ {file}")
    
    if missing:
        print(f"\n❌ 缺少 {len(missing)} 个文件")
        return False
    else:
        print("\n✓ 所有必要文件都存在")
        return True


def check_imports():
    """检查核心模块是否可以导入"""
    print("\n检查模块导入...")
    modules = [
        ("config", "config.py"),
        ("config_loader", "config_loader.py"),
        ("core", "core.py"),
    ]
    
    failed = []
    for module_name, file_name in modules:
        try:
            __import__(module_name)
            print(f"  ✓ {module_name}")
        except Exception as e:
            print(f"  ❌ {module_name}: {e}")
            failed.append(module_name)
    
    if failed:
        print(f"\n❌ {len(failed)} 个模块导入失败")
        return False
    else:
        print("\n✓ 所有模块导入成功")
        return True


def check_dependencies():
    """检查依赖是否安装"""
    print("\n检查依赖...")
    dependencies = [
        "pandas",
        "openpyxl",
        "tqdm",
    ]
    
    missing = []
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"  ✓ {dep}")
        except ImportError:
            print(f"  ❌ {dep} (未安装)")
            missing.append(dep)
    
    # llama-cpp-python 特殊处理
    try:
        import llama_cpp
        print(f"  ✓ llama-cpp-python")
    except ImportError:
        print(f"  ❌ llama-cpp-python (未安装)")
        missing.append("llama-cpp-python")
    
    if missing:
        print(f"\n⚠ 缺少 {len(missing)} 个依赖")
        print("运行以下命令安装：")
        print("  pip install -r requirements.txt")
        return False
    else:
        print("\n✓ 所有核心依赖已安装")
        return True


def check_dev_dependencies():
    """检查开发依赖是否安装"""
    print("\n检查开发依赖（可选）...")
    dev_deps = [
        "pytest",
        "black",
        "ruff",
    ]
    
    missing = []
    for dep in dev_deps:
        try:
            __import__(dep)
            print(f"  ✓ {dep}")
        except ImportError:
            print(f"  ⚠ {dep} (未安装)")
            missing.append(dep)
    
    if missing:
        print(f"\n⚠ 缺少 {len(missing)} 个开发依赖（不影响正常使用）")
        print("如需开发，运行以下命令安装：")
        print("  pip install -r requirements-dev.txt")
        return False
    else:
        print("\n✓ 所有开发依赖已安装")
        return True


def check_config():
    """检查配置是否正确"""
    print("\n检查配置...")
    try:
        from config_loader import load_config
        config = load_config()
        
        # 检查必要的配置项
        required_attrs = [
            "EXCEL_PATH",
            "OUTPUT_PATH",
            "MODEL_PATHS",
            "LLAMA_N_CTX",
            "LLAMA_N_THREADS",
            "LLAMA_N_GPU_LAYERS",
            "PROCESS_POOL_MAX_WORKERS",
            "CHECKPOINT_SAVE_INTERVAL",
            "PROMPT_TEMPLATE",
        ]
        
        missing = []
        for attr in required_attrs:
            if not hasattr(config, attr):
                missing.append(attr)
                print(f"  ❌ 缺少配置项: {attr}")
            else:
                print(f"  ✓ {attr}")
        
        if missing:
            print(f"\n❌ 缺少 {len(missing)} 个配置项")
            return False
        else:
            print("\n✓ 配置完整")
            return True
    except Exception as e:
        print(f"\n❌ 配置加载失败: {e}")
        return False


def check_tests():
    """检查测试文件是否存在"""
    print("\n检查测试文件...")
    test_files = [
        "tests/__init__.py",
        "tests/test_preprocessing.py",
        "tests/test_extraction.py",
        "tests/test_checkpoint.py",
        "tests/test_config_loader.py",
    ]
    
    missing = []
    for file in test_files:
        if not Path(file).exists():
            missing.append(file)
            print(f"  ❌ 缺失: {file}")
        else:
            print(f"  ✓ {file}")
    
    if missing:
        print(f"\n❌ 缺少 {len(missing)} 个测试文件")
        return False
    else:
        print("\n✓ 所有测试文件都存在")
        return True


def main():
    """主函数"""
    print("=" * 60)
    print("项目设置验证")
    print("=" * 60)
    print()
    
    results = []
    
    # 运行所有检查
    results.append(("文件检查", check_files()))
    results.append(("模块导入", check_imports()))
    results.append(("核心依赖", check_dependencies()))
    results.append(("开发依赖", check_dev_dependencies()))
    results.append(("配置检查", check_config()))
    results.append(("测试文件", check_tests()))
    
    # 总结
    print("\n" + "=" * 60)
    print("验证总结")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓" if result else "❌"
        print(f"{status} {name}")
    
    print()
    print(f"通过: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 所有检查通过！项目设置正确。")
        print("\n下一步:")
        print("  1. 下载模型文件: python download_model.py")
        print("  2. 运行测试: pytest tests/ -v")
        print("  3. 启动程序: python gui.py 或 python main.py")
        return 0
    else:
        print("\n⚠ 部分检查未通过，请根据上述提示修复。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
