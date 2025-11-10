#!/usr/bin/env python3
"""
GUI界面 - 医疗影像报告批量预测工具
"""
import sys
import os
import importlib.util
from pathlib import Path
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import pandas as pd
from io import StringIO

# 设置路径
sys.path.insert(0, str(Path(__file__).parent))

# 导入核心业务逻辑
from core import batch_predict
import config

# 尝试加载外层配置
outer = os.path.join(os.path.dirname(sys.executable), 'config.py')
if os.path.exists(outer):
    spec = importlib.util.spec_from_file_location("external_config", outer)
    cfg = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cfg)
    for key in dir(cfg):
        if not key.startswith('_'):
            setattr(config, key, getattr(cfg, key))


class RedirectText:
    """重定向print输出到GUI文本框，智能处理tqdm进度条"""
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.current_line = ""
        self.is_progress_line = False
        
    def write(self, string):
        import re
        
        # 清理ANSI转义序列
        clean_string = self._clean_ansi(string)
        
        # 处理回车符（tqdm使用\r来更新同一行）
        if '\r' in clean_string:
            # 分割字符串
            parts = clean_string.split('\r')
            
            for i, part in enumerate(parts):
                if i == 0 and self.is_progress_line:
                    # 删除上一个进度行
                    try:
                        self.text_widget.delete("end-2c linestart", "end-1c")
                    except:
                        pass
                
                if part.strip():
                    # 检测是否是进度条行（包含百分比或it/s）
                    if '%' in part or 'it/s' in part or '/s' in part:
                        self.text_widget.insert(tk.END, part.strip() + '\n')
                        self.is_progress_line = True
                    else:
                        self.text_widget.insert(tk.END, part)
                        self.is_progress_line = False
        else:
            # 普通输出
            self.text_widget.insert(tk.END, clean_string)
            if '\n' in clean_string:
                self.is_progress_line = False
            
        self.text_widget.see(tk.END)
        self.text_widget.update_idletasks()
        
    def _clean_ansi(self, text):
        """清理ANSI转义序列和其他控制字符"""
        import re
        # 移除ANSI颜色代码和控制序列
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        text = ansi_escape.sub('', text)
        # 移除其他控制字符（保留\n, \r, \t）
        text = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', text)
        return text
        
    def flush(self):
        pass


class MedicalPredictorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("医疗影像报告批量预测工具")
        self.root.geometry("950x750")
        
        # 变量
        self.excel_path = tk.StringVar(value=str(config.EXCEL_PATH))
        self.output_path = tk.StringVar(value=str(config.OUTPUT_PATH))
        self.model_paths = config.MODEL_PATHS.copy()
        self.is_running = False
        
        # 配置参数变量
        self.n_threads = tk.IntVar(value=config.LLAMA_N_THREADS)
        self.n_gpu_layers = tk.IntVar(value=config.LLAMA_N_GPU_LAYERS)
        self.max_workers = tk.IntVar(value=config.PROCESS_POOL_MAX_WORKERS)
        self.checkpoint_interval = tk.IntVar(value=config.CHECKPOINT_SAVE_INTERVAL)
        
        self.create_widgets()
        
    def create_widgets(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # 标题
        title_label = ttk.Label(main_frame, text="医疗影像报告批量预测工具", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # 输入文件选择
        row = 1
        ttk.Label(main_frame, text="输入文件:").grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.excel_path, width=50).grid(
            row=row, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(main_frame, text="浏览...", command=self.browse_input).grid(
            row=row, column=2, padx=5)
        
        # 输出文件选择
        row += 1
        ttk.Label(main_frame, text="输出文件:").grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.output_path, width=50).grid(
            row=row, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(main_frame, text="浏览...", command=self.browse_output).grid(
            row=row, column=2, padx=5)
        
        # 模型列表
        row += 1
        ttk.Label(main_frame, text="模型列表:").grid(row=row, column=0, sticky=tk.W, pady=5)
        
        # 模型列表框架
        model_frame = ttk.Frame(main_frame)
        model_frame.grid(row=row, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        model_frame.columnconfigure(0, weight=1)
        
        # 模型列表显示
        self.model_listbox = tk.Listbox(model_frame, height=4)
        self.model_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        scrollbar = ttk.Scrollbar(model_frame, orient=tk.VERTICAL, 
                                 command=self.model_listbox.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.model_listbox.config(yscrollcommand=scrollbar.set)
        
        # 模型按钮
        model_btn_frame = ttk.Frame(model_frame)
        model_btn_frame.grid(row=1, column=0, columnspan=2, pady=5)
        ttk.Button(model_btn_frame, text="添加模型", 
                  command=self.add_model).pack(side=tk.LEFT, padx=2)
        ttk.Button(model_btn_frame, text="删除选中", 
                  command=self.remove_model).pack(side=tk.LEFT, padx=2)
        
        self.update_model_list()
        
        # 分隔线
        row += 1
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).grid(
            row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=15)
        
        # 配置参数区域
        row += 1
        config_label = ttk.Label(main_frame, text="运行参数配置:", 
                                font=("Arial", 10, "bold"))
        config_label.grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=(5, 10))
        
        # 配置参数框架
        row += 1
        config_frame = ttk.LabelFrame(main_frame, text="性能参数", padding="10")
        config_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        config_frame.columnconfigure(1, weight=1)
        config_frame.columnconfigure(3, weight=1)
        
        # 第一行：线程数和GPU层数
        ttk.Label(config_frame, text="CPU线程数:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        ttk.Spinbox(config_frame, from_=1, to=32, textvariable=self.n_threads, 
                   width=10).grid(row=0, column=1, sticky=tk.W, padx=5)
        
        ttk.Label(config_frame, text="GPU层数:").grid(row=0, column=2, sticky=tk.W, padx=(20, 5))
        ttk.Spinbox(config_frame, from_=0, to=100, textvariable=self.n_gpu_layers, 
                   width=10).grid(row=0, column=3, sticky=tk.W, padx=5)
        
        ttk.Label(config_frame, text="(0=纯CPU)").grid(row=0, column=4, sticky=tk.W, padx=5)
        
        # 第二行：进程数和检查点间隔
        ttk.Label(config_frame, text="并行进程数:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5), pady=(10, 0))
        ttk.Spinbox(config_frame, from_=1, to=16, textvariable=self.max_workers, 
                   width=10).grid(row=1, column=1, sticky=tk.W, padx=5, pady=(10, 0))
        
        ttk.Label(config_frame, text="检查点间隔:").grid(row=1, column=2, sticky=tk.W, padx=(20, 5), pady=(10, 0))
        ttk.Spinbox(config_frame, from_=1, to=10000, textvariable=self.checkpoint_interval, 
                   width=10).grid(row=1, column=3, sticky=tk.W, padx=5, pady=(10, 0))
        
        ttk.Label(config_frame, text="(条/次)").grid(row=1, column=4, sticky=tk.W, padx=5, pady=(10, 0))
        
        # 说明文字
        row += 1
        help_text = "提示：进程数×线程数 ≈ CPU核心数；多进程会增加内存占用"
        ttk.Label(main_frame, text=help_text, foreground="gray", 
                 font=("Arial", 8)).grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=(0, 10))
        
        # 分隔线
        row += 1
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).grid(
            row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        # 控制按钮
        row += 1
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=row, column=0, columnspan=3, pady=10)
        
        self.start_btn = ttk.Button(btn_frame, text="开始预测", 
                                    command=self.start_prediction, width=15)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(btn_frame, text="停止", 
                                   command=self.stop_prediction, 
                                   state=tk.DISABLED, width=15)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        # 日志输出
        row += 1
        ttk.Label(main_frame, text="运行日志:").grid(
            row=row, column=0, sticky=tk.W, pady=(10, 5))
        
        row += 1
        self.log_text = scrolledtext.ScrolledText(main_frame, height=15, 
                                                  wrap=tk.WORD, state=tk.NORMAL)
        self.log_text.grid(row=row, column=0, columnspan=3, 
                          sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        main_frame.rowconfigure(row, weight=1)
        
        # 状态栏
        row += 1
        self.status_label = ttk.Label(main_frame, text="就绪", 
                                     relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.grid(row=row, column=0, columnspan=3, 
                              sticky=(tk.W, tk.E), pady=(10, 0))
        
    def update_model_list(self):
        """更新模型列表显示"""
        self.model_listbox.delete(0, tk.END)
        for model_path in self.model_paths:
            model_name = Path(model_path).name
            self.model_listbox.insert(tk.END, model_name)
    
    def browse_input(self):
        """浏览输入文件"""
        filename = filedialog.askopenfilename(
            title="选择输入Excel文件",
            filetypes=[("Excel文件", "*.xlsx *.xls"), ("所有文件", "*.*")]
        )
        if filename:
            self.excel_path.set(filename)
    
    def browse_output(self):
        """浏览输出文件"""
        filename = filedialog.asksaveasfilename(
            title="选择输出Excel文件",
            defaultextension=".xlsx",
            filetypes=[("Excel文件", "*.xlsx"), ("所有文件", "*.*")]
        )
        if filename:
            self.output_path.set(filename)
    
    def add_model(self):
        """添加模型"""
        filename = filedialog.askopenfilename(
            title="选择模型文件",
            filetypes=[("GGUF模型", "*.gguf"), ("所有文件", "*.*")]
        )
        if filename:
            self.model_paths.append(filename)
            self.update_model_list()
    
    def remove_model(self):
        """删除选中的模型"""
        selection = self.model_listbox.curselection()
        if selection:
            idx = selection[0]
            del self.model_paths[idx]
            self.update_model_list()
    
    def start_prediction(self):
        """开始预测"""
        # 验证输入
        if not Path(self.excel_path.get()).exists():
            messagebox.showerror("错误", "输入文件不存在！")
            return
        
        if not self.model_paths:
            messagebox.showerror("错误", "请至少添加一个模型！")
            return
        
        # 更新配置参数
        config.LLAMA_N_THREADS = self.n_threads.get()
        config.LLAMA_N_GPU_LAYERS = self.n_gpu_layers.get()
        config.PROCESS_POOL_MAX_WORKERS = self.max_workers.get()
        config.CHECKPOINT_SAVE_INTERVAL = self.checkpoint_interval.get()
        
        # 更新UI状态
        self.is_running = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_label.config(text="正在运行...")
        self.log_text.delete(1.0, tk.END)
        
        # 重定向输出
        sys.stdout = RedirectText(self.log_text)
        sys.stderr = RedirectText(self.log_text)
        
        # 在新线程中运行预测
        thread = threading.Thread(target=self.run_prediction, daemon=True)
        thread.start()
    
    def run_prediction(self):
        """运行预测任务"""
        try:
            # 读取数据
            df = pd.read_excel(self.excel_path.get())
            print(f"成功读取输入文件: {self.excel_path.get()}")
            print(f"共 {len(df)} 条数据\n")
            
            # 对每个模型进行预测
            for model_path in self.model_paths:
                if not self.is_running:
                    print("\n预测已停止")
                    break
                
                preds, total_time, model_name = batch_predict(df, model_path, config)
                col_name = f"pred_{model_name}"
                df[col_name] = preds
            
            # 保存结果
            if self.is_running:
                df.to_excel(self.output_path.get(), index=False)
                print(f"\n✓ 结果已保存至：{self.output_path.get()}")
                self.root.after(0, lambda: messagebox.showinfo(
                    "完成", f"预测完成！\n结果已保存至：{self.output_path.get()}"))
            
        except Exception as e:
            print(f"\n❌ 错误: {e}")
            import traceback
            traceback.print_exc()
            self.root.after(0, lambda: messagebox.showerror("错误", str(e)))
        
        finally:
            # 恢复UI状态
            self.root.after(0, self.reset_ui)
    
    def stop_prediction(self):
        """停止预测"""
        self.is_running = False
        self.status_label.config(text="正在停止...")
        print("\n⚠ 用户请求停止...")
    
    def reset_ui(self):
        """重置UI状态"""
        self.is_running = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_label.config(text="就绪")
        
        # 恢复标准输出
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__


def main():
    root = tk.Tk()
    app = MedicalPredictorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
