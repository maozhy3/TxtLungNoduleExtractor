#!/usr/bin/env python3
"""
命令行版本 - 医疗影像报告批量预测工具
"""
# 标准库
import os
import subprocess
import sys
from pathlib import Path

# 第三方库
import pandas as pd

# 本地模块
sys.path.insert(0, str(Path(__file__).parent))
from config_loader import load_config
from core import batch_predict

# 加载配置
config = load_config()


# 首次运行处理vc
bundle = Path(__file__).parent
flag = bundle / '_vcredist' / '.done'
vc    = bundle / '_vcredist' / 'vc_redist.x64.exe'
if vc.exists() and not flag.exists():
    try:
        subprocess.check_call([str(vc), '/quiet', '/norestart'])
        flag.parent.mkdir(parents=True, exist_ok=True)
        flag.touch()
    except Exception as e:
        print(f"警告：VC++ 运行库安装失败: {e}")


def main() -> None:
    """主函数"""
    try:
        df = pd.read_excel(config.EXCEL_PATH)
        print(f"✓ 成功读取输入文件: {config.EXCEL_PATH}")
        print(f"共 {len(df)} 条数据\n")

        for model_path in config.MODEL_PATHS:
            preds, total_time, model_name = batch_predict(df, model_path, config)
            col_name = f"pred_{model_name}"
            df[col_name] = preds

        df.to_excel(config.OUTPUT_PATH, index=False)
        print(f"\n✓ 结果已保存至：{config.OUTPUT_PATH}")
    except FileNotFoundError as e:
        print(f"❌ 文件未找到: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        input("\n按任意键结束...")


if __name__ == "__main__":
    main()