import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import os
import re
import markdown
import json
from tkhtmlview import HTMLLabel

# 添加DPI感知支持，适应高分辨率屏幕和缩放倍率
try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)
except:
    pass  # 在非Windows系统上忽略

class QuestionExtractor:
    def __init__(self):
        print("[调试] 初始化QuestionExtractor")
        self.root = tk.Tk()
        print("[调试] 主窗口创建成功")
        self.root.title("题目提取工具 - 公式渲染测试版")
        self.root.geometry("1100x800")
        print("[调试] 窗口尺寸设置成功")
        
        # 计算适合的字体大小，考虑DPI缩放
        self.font_size = 12  # 增大基础字体大小
        self.font_config = {"font": ("SimHei", self.font_size)}
        print("[调试] 字体配置完成")
        
        self.file_path = None
        self.questions = []
        self.current_question_index = -1
        self.toolbar = None  # 添加toolbar属性初始化
        
        # 渲染模式：text或html
        self.render_mode = tk.StringVar(value="html")
        print("[调试] 渲染模式变量初始化成功")
        
        # 自动保存选项
        self.auto_save_var = tk.BooleanVar(value=False)
        print("[调试] 自动保存变量初始化成功")
        
        # 单选模式选项
        self.single_choice_var = tk.BooleanVar(value=True)
        print("[调试] 单选模式变量初始化成功")
        
        # 夜间模式选项
        self.dark_mode_var = tk.BooleanVar(value=False)
        print("[调试] 夜间模式变量初始化成功")
        
        # 颜色配置
        self.color_schemes = {
            'light': {
                'bg': 'white',
                'fg': 'black',
                'toolbar_bg': '#f0f0f0',
                'status_bar_bg': '#f0f0f0',
                'frame_bg': '#ffffff',
                'html_bg': 'white',
                'html_text': '#333333'
            },
            'dark': {
                'bg': '#1e1e1e',
                'fg': '#ffffff',
                'toolbar_bg': '#2d2d2d',
                'status_bar_bg': '#2d2d2d',
                'frame_bg': '#2d2d2d',
                'html_bg': '#2d2d2d',
                'html_text': '#e0e0e0'
            }
        }
        print("[调试] 颜色方案初始化成功")
        
        # 设置配置文件路径
        self.config_dir = os.path.join(os.path.expanduser("~"), ".question_extractor")
        self.config_file = os.path.join(self.config_dir, "config.json")
        print(f"[调试] 配置文件路径设置为: {self.config_file}")
        
        # 确保配置目录存在
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
            print(f"[调试] 创建配置目录: {self.config_dir}")
        
        self.setup_ui()
        print("[调试] UI设置完成")
        
        # 加载配置并尝试恢复上次进度
        self.restore_last_session()
        
        # 添加窗口关闭协议处理，确保退出时保存配置
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        print("[调试] 窗口关闭协议设置完成")
        
        # 绑定快捷键（移到这里确保UI完全初始化后立即绑定）
        # 绑定空格键事件到下一题功能
        self.root.bind('<space>', lambda event: self.next_question())
        print("[调试] 空格键快捷键绑定成功")
        
        # 修复数字键绑定，使用正确的事件绑定格式
        def on_key_press(event, key):
            print(f"[调试] 捕获到键按下事件: {key}")
            return self.select_option(key)
        
        # 绑定数字键1-4到选项选择功能
        for key in ['1', '2', '3', '4']:
            self.root.bind(key, lambda event, k=key: on_key_press(event, k))
        print("[调试] 数字键1-4快捷键绑定成功")
        
        # 设置焦点事件，确保窗口获得焦点时能接收键盘事件
        def on_focus_in(event):
            print("[调试] 窗口获得焦点")
            self.root.focus_set()
        
        self.root.bind('<FocusIn>', on_focus_in)
        # 初始设置焦点
        self.root.focus_set()
        print("[调试] 窗口焦点设置成功")
        print("[调试] 所有快捷键绑定完成")
    
    def setup_ui(self):
        print("[调试] 开始设置UI")
        # 顶部工具栏
        self.toolbar = tk.Frame(self.root, bg="#f0f0f0", padx=10, pady=5)
        self.toolbar.pack(fill=tk.X)
        print("[调试] 顶部工具栏创建成功")
        
        tk.Button(self.toolbar, text="选择文件", command=self.select_file, **self.font_config).pack(side=tk.LEFT, padx=5)
        tk.Button(self.toolbar, text="提取题目", command=self.extract_questions, **self.font_config).pack(side=tk.LEFT, padx=5)
        tk.Button(self.toolbar, text="自动修复选项格式", command=self.fix_all_question_formats, **self.font_config).pack(side=tk.LEFT, padx=5)
        tk.Button(self.toolbar, text="导出不带引用部分", command=self.export_without_quotes, **self.font_config).pack(side=tk.LEFT, padx=5)
        tk.Button(self.toolbar, text="导出带引用部分", command=self.export_with_quotes, **self.font_config).pack(side=tk.LEFT, padx=5)
        print("[调试] 工具栏按钮创建成功")
        
        # 文件信息标签
        self.file_label = tk.Label(self.toolbar, text="formula_test.md", fg="gray", **self.font_config)
        self.file_label.pack(side=tk.LEFT, padx=10)
        print("[调试] 文件信息标签创建成功")
        
        # 题目导航区域
        nav_frame = tk.Frame(self.root, pady=5)
        nav_frame.pack(fill=tk.X, padx=10)
        print("[调试] 题目导航区域创建成功")
        
        tk.Label(nav_frame, text="题目导航:", **self.font_config).pack(side=tk.LEFT)
        
        self.prev_button = tk.Button(nav_frame, text="上一题", command=self.prev_question, state=tk.DISABLED, **self.font_config)
        self.prev_button.pack(side=tk.LEFT, padx=5)
        
        self.next_button = tk.Button(nav_frame, text="下一题", command=self.next_question, state=tk.DISABLED, **self.font_config)
        self.next_button.pack(side=tk.LEFT, padx=5)
        
        self.question_info = tk.Label(nav_frame, text="共0题，当前第0题", **self.font_config)
        self.question_info.pack(side=tk.LEFT, padx=10)
        print("[调试] 导航按钮创建成功")
        
        # 添加进度条（拖动滑动框）
        self.progress_var = tk.DoubleVar()
        self.progress_bar = tk.Scale(nav_frame, from_=1, to=1, orient=tk.HORIZONTAL, length=200, 
                                    variable=self.progress_var, showvalue=False, state=tk.DISABLED,
                                    command=self.on_progress_change)
        self.progress_bar.pack(side=tk.LEFT, padx=10)
        print("[调试] 进度条（拖动滑动框）创建成功")
        
        # 添加题目跳转功能
        jump_frame = tk.Frame(nav_frame)
        jump_frame.pack(side=tk.LEFT, padx=10)
        
        tk.Label(jump_frame, text="跳转到:", **self.font_config).pack(side=tk.LEFT)
        self.jump_entry = tk.Entry(jump_frame, width=5, **self.font_config)
        self.jump_entry.pack(side=tk.LEFT, padx=5)
        self.jump_button = tk.Button(jump_frame, text="跳转", command=self.jump_to_question, **self.font_config)
        self.jump_button.pack(side=tk.LEFT)
        print("[调试] 题目跳转功能创建成功")
        
        # 设置选项框架
        settings_frame = tk.Frame(self.root, pady=5)
        settings_frame.pack(fill=tk.X, padx=10)
        
        # 渲染模式选择
        tk.Label(settings_frame, text="渲染模式:", **self.font_config).pack(side=tk.LEFT)
        tk.Radiobutton(settings_frame, text="原始文本", variable=self.render_mode, value="text", 
                      command=self.switch_render_mode, **self.font_config).pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(settings_frame, text="Markdown渲染", variable=self.render_mode, value="html", 
                      command=self.switch_render_mode, **self.font_config).pack(side=tk.LEFT, padx=5)
        
        # 自动保存选项
        tk.Checkbutton(settings_frame, text="自动保存选择", variable=self.auto_save_var, 
                      **self.font_config).pack(side=tk.LEFT, padx=20)
        print("[调试] 自动保存选项创建成功")
        
        # 单选模式选项
        tk.Checkbutton(settings_frame, text="单选模式", variable=self.single_choice_var, 
                      **self.font_config).pack(side=tk.LEFT, padx=10)
        print("[调试] 单选模式选项创建成功")
        print("[调试] 设置选项框架创建成功")
        
        # 内容显示区域
        content_frame = tk.Frame(self.root)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        print("[调试] 内容显示区域创建成功")
        
        # 不带引用部分
        no_quote_frame = tk.LabelFrame(content_frame, text="不带引用部分", **self.font_config)
        no_quote_frame.pack(fill=tk.BOTH, expand=True, side=tk.LEFT, padx=5)
        
        # 创建文本视图
        self.no_quote_text_frame = tk.Frame(no_quote_frame)
        self.no_quote_text = scrolledtext.ScrolledText(self.no_quote_text_frame, wrap=tk.WORD, **self.font_config)
        self.no_quote_text.pack(fill=tk.BOTH, expand=True)
        
        # 创建HTML视图
        self.no_quote_html_frame = tk.Frame(no_quote_frame)
        self.no_quote_html = HTMLLabel(self.no_quote_html_frame, background="white", html="<h3>请选择文件并提取题目</h3>")
        self.no_quote_html.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.no_quote_html.config(state=tk.NORMAL)  # 启用文本选择
        
        # 默认显示HTML视图
        self.no_quote_text_frame.pack_forget()
        self.no_quote_html_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        print("[调试] 不带引用部分视图创建成功")
        
        # 带引用部分
        quote_frame = tk.LabelFrame(content_frame, text="带引用部分", **self.font_config)
        quote_frame.pack(fill=tk.BOTH, expand=True, side=tk.LEFT, padx=5)
        
        # 创建文本视图
        self.quote_text_frame = tk.Frame(quote_frame)
        self.quote_text = scrolledtext.ScrolledText(self.quote_text_frame, wrap=tk.WORD, **self.font_config)
        self.quote_text.pack(fill=tk.BOTH, expand=True)
        
        # 创建HTML视图
        self.quote_html_frame = tk.Frame(quote_frame)
        self.quote_html = HTMLLabel(self.quote_html_frame, background="white", html="<h3>请选择文件并提取题目</h3>")
        self.quote_html.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.quote_html.config(state=tk.NORMAL)  # 启用文本选择
        
        # 默认显示HTML视图
        self.quote_text_frame.pack_forget()
        self.quote_html_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        print("[调试] 带引用部分视图创建成功")
        
        # 添加状态栏
        self.status_bar = tk.Label(self.root, text="就绪", bd=1, relief=tk.SUNKEN, anchor=tk.W, **self.font_config)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        print("[调试] 状态栏创建成功")
        
        # 绑定f键为当前题目修复快捷键
        self.root.bind('<KeyPress-f>', lambda event: self.fix_current_question_format())
        print("[调试] f键快捷键绑定为修复当前题目")
        
        # 绑定方向键左右控制上下一题
        self.root.bind('<Left>', lambda event: self.prev_question())
        self.root.bind('<Right>', lambda event: self.next_question())
        print("[调试] 方向键左右已绑定到题目导航功能")
        
        # 添加夜间模式切换按钮
        self.theme_toggle = tk.Checkbutton(self.toolbar, text="夜间模式", variable=self.dark_mode_var,
                                         command=self.toggle_dark_mode, **self.font_config)
        self.theme_toggle.pack(side=tk.RIGHT, padx=5)
        print("[调试] 夜间模式切换按钮添加成功")
    
    def select_file(self):
        filename = filedialog.askopenfilename(
            title="选择要处理的文件",
            filetypes=[("Markdown文件", "*.md"), ("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        if filename:
            self.file_path = filename
            self.file_label.config(text=os.path.basename(filename), fg="black")
            print(f"[调试] 已选择文件: {os.path.basename(filename)}")
            # 选择文件后自动提取题目
            print(f"[调试] 自动开始提取题目")
            self.extract_questions()
    
    def toggle_dark_mode(self):
        """切换夜间模式，完善所有UI元素的颜色设置"""
        print(f"[调试] 切换夜间模式: {'开启' if self.dark_mode_var.get() else '关闭'}")
        
        # 获取当前主题颜色配置
        theme = 'dark' if self.dark_mode_var.get() else 'light'
        colors = self.color_schemes[theme]
        
        # 更新主窗口颜色
        self.root.config(bg=colors['bg'])
        
        # 更新工具栏颜色和前景色
        self.toolbar.config(bg=colors['toolbar_bg'])
        # 更新工具栏上所有按钮和标签的颜色
        for widget in self.toolbar.winfo_children():
            if isinstance(widget, tk.Button):
                widget.config(bg=colors['toolbar_bg'], fg=colors['fg'])
            elif isinstance(widget, tk.Label):
                widget.config(bg=colors['toolbar_bg'], fg=colors['fg'])
            elif isinstance(widget, tk.Checkbutton):
                widget.config(bg=colors['toolbar_bg'], fg=colors['fg'])
        
        # 更新导航区域颜色
        nav_frame = self.prev_button.master  # 获取导航框架
        nav_frame.config(bg=colors['bg'])
        
        # 更新导航按钮颜色
        self.prev_button.config(bg=colors['frame_bg'], fg=colors['fg'])
        self.next_button.config(bg=colors['frame_bg'], fg=colors['fg'])
        self.question_info.config(bg=colors['bg'], fg=colors['fg'])
        
        # 更新进度条颜色
        self.progress_bar.config(bg=colors['bg'], troughcolor=colors['frame_bg'])
        
        # 更新跳转功能颜色
        jump_frame = self.jump_entry.master
        jump_frame.config(bg=colors['bg'])
        for widget in jump_frame.winfo_children():
            if isinstance(widget, tk.Button):
                widget.config(bg=colors['frame_bg'], fg=colors['fg'])
            elif isinstance(widget, tk.Label):
                widget.config(bg=colors['bg'], fg=colors['fg'])
        self.jump_entry.config(bg=colors['frame_bg'], fg=colors['fg'])
        
        # 更新设置框架颜色
        if hasattr(self, 'settings_frame'):
            self.settings_frame.config(bg=colors['bg'])
            for widget in self.settings_frame.winfo_children():
                if isinstance(widget, tk.Label) or isinstance(widget, tk.Checkbutton):
                    widget.config(bg=colors['bg'], fg=colors['fg'])
        
        # 更新内容区域颜色
        self.content_frame.config(bg=colors['bg'])
        
        # 更新标签框架颜色和文本颜色
        self.no_quote_frame.config(bg=colors['bg'], fg=colors['fg'])
        self.quote_frame.config(bg=colors['bg'], fg=colors['fg'])
        
        # 更新文本视图框架颜色
        self.no_quote_text_frame.config(bg=colors['bg'])
        self.quote_text_frame.config(bg=colors['bg'])
        
        # 更新文本框颜色（背景和前景）
        self.no_quote_text.config(bg=colors['frame_bg'], fg=colors['fg'])
        self.quote_text.config(bg=colors['frame_bg'], fg=colors['fg'])
        
        # 更新HTML视图框架颜色
        self.no_quote_html_frame.config(bg=colors['bg'])
        self.quote_html_frame.config(bg=colors['bg'])
        
        # 更新HTML视图颜色（背景和前景）
        self.no_quote_html.config(background=colors['html_bg'])
        self.quote_html.config(background=colors['html_bg'])
        
        # 更新状态栏颜色
        self.status_bar.config(bg=colors['status_bar_bg'], fg=colors['fg'])
        
        # 如果有当前题目，重新渲染HTML以应用新主题和颜色
        if self.questions and 0 <= self.current_question_index < len(self.questions):
            print("[调试] 重新渲染当前题目以应用新主题颜色")
            self.display_current_question()
        
        print("[调试] 主题切换完成，所有UI元素颜色已更新")
        
    def split_questions_by_separator(self, content):
        """按---分割题目"""
        # 使用正则表达式分割，保留分割符
        parts = re.split(r'(---\n)', content)
        questions = []
        current_question = ""
        
        for part in parts:
            if part.strip() == '---':
                if current_question.strip():
                    questions.append(current_question.strip())
                    current_question = ""
            else:
                current_question += part
        
        # 添加最后一题（如果有）
        if current_question.strip():
            questions.append(current_question.strip())
        
        return questions
    
    def extract_without_quotes(self, question_content):
        """提取不带引用的部分（不以>开头的行）"""
        lines = question_content.split('\n')
        non_quote_lines = [line for line in lines if not line.strip().startswith('>')]
        return '\n'.join(non_quote_lines).strip()
    
    def extract_with_quotes(self, question_content):
        """提取带引用的部分（以>开头的行）并去除>符号"""
        lines = question_content.split('\n')
        quote_lines = []
        for line in lines:
            if line.strip().startswith('>'):
                # 去除>符号和可能的空格
                content = line.strip()[1:].strip()
                quote_lines.append(content)
        return '\n'.join(quote_lines).strip()
    
    def fix_option_format(self, question_content):
        """自动修复选项格式，将一行多个选项转换为每行一个选项"""
        print(f"[调试] 开始修复选项格式，内容长度: {len(question_content)} 字符")
        
        # 匹配格式：- [ ] A.内容 B.内容 C.内容 D.内容 或类似变体
        # 引用块内和引用块外的格式都要处理
        option_patterns = [
            # 引用块外的格式
            (r'^\s*[-]\s*\[([ x])\]\s*([A-D])\.?\s*([^ABCD]*?)\s*([A-D])\.?\s*([^ABCD]*?)\s*([A-D])\.?\s*([^ABCD]*?)\s*([A-D])\.?\s*(.*?)$', 8),
            # 引用块内的格式
            (r'>\s*[-]\s*\[([ x])\]\s*([A-D])\.?\s*([^ABCD]*?)\s*([A-D])\.?\s*([^ABCD]*?)\s*([A-D])\.?\s*([^ABCD]*?)\s*([A-D])\.?\s*(.*?)$', 8)
        ]
        
        fixed_content = question_content
        modified = False
        
        for pattern, group_count in option_patterns:
            matches = re.findall(pattern, fixed_content, re.MULTILINE)
            
            for match in matches:
                print(f"[调试] 找到一行多选项格式: {match}")
                selected = match[0]  # [x] 或 []
                options = []
                
                # 提取所有选项 (字母+内容)
                for i in range(1, len(match), 2):
                    if i+1 <= len(match):
                        letter = match[i].strip()
                        content = match[i+1].strip()
                        if letter and content:
                            options.append((letter, content))
                
                if options:
                    # 构建修复后的选项行
                    prefix = '>' if pattern.startswith('>') else ''
                    fixed_lines = []
                    for letter, content in options:
                        fixed_lines.append(f"{prefix} - [{selected}] {letter}. {content}")
                    
                    # 替换原行
                    original_line = re.search(pattern, fixed_content, re.MULTILINE)
                    if original_line:
                        fixed_content = fixed_content.replace(original_line.group(0), '\n'.join(fixed_lines))
                        modified = True
                        print(f"[调试] 已修复选项格式，替换为多行格式")
        
        print(f"[调试] 选项格式修复完成，是否有修改: {modified}")
        return fixed_content, modified
    
    def analyze_option_type(self, question_content):
        """分析题目选项类型，区分判断题和普通选择题，并提供详细的非标准原因"""
        print(f"[调试] 开始分析选项类型，内容长度: {len(question_content)} 字符")
        
        # 同时提取引用块内和引用块外的复选框列表项格式
        # 引用块内的格式
        options_in_quote = re.findall(r'>\s*-\s*\[[ x]]\s*([A-D])\.?\s*(.*)$', question_content, re.MULTILINE)
        print(f"[调试] 找到 {len(options_in_quote)} 个引用块内的选项: {options_in_quote}")
        
        # 引用块外的格式
        options_out_quote = re.findall(r'^\s*-\s*\[[ x]]\s*([A-D])\.?\s*(.*)$', question_content, re.MULTILINE)
        print(f"[调试] 找到 {len(options_out_quote)} 个引用块外的选项: {options_out_quote}")
        
        # 合并两种格式的选项
        options = options_in_quote + options_out_quote
        
        # 去重（以防重复匹配）
        options = list(set(options))
        print(f"[调试] 合并并去重后的选项总数: {len(options)}, 选项: {options}")
        
        # 详细检查每个选项的格式
        for i, (letter, content) in enumerate(options, 1):
            is_valid_letter = letter in ['A', 'B', 'C', 'D']
            is_selected = '[x]' in question_content.split(f'- [{letter}')[0]
            print(f"[调试] 选项{i}: 字母='{letter}', 内容='{content}', 是否有效字母: {is_valid_letter}, 是否被选中: {is_selected}")
        
        # 检查是否为判断题（只有A 正确和B 错误两个选项）
        if len(options) == 2:
            print(f"[调试] 选项数量为2，检查是否为判断题")
            option0_correct = options[0][0] == 'A' and '正确' in options[0][1]
            option1_error = options[1][0] == 'B' and '错误' in options[1][1]
            print(f"[调试] 选项0是A且包含'正确': {option0_correct}")
            print(f"[调试] 选项1是B且包含'错误': {option1_error}")
            
            if option0_correct and option1_error:
                print(f"[调试] 符合判断题格式")
                return '判断题', None  # 没有错误原因
            else:
                print(f"[调试] 不符合判断题格式")
                return '非标准格式', f'选项数量为2，但不是标准判断题格式（应为A 正确，B 错误）'
        
        # 检查是否为普通选择题（有四个选项）
        elif len(options) == 4:
            print(f"[调试] 选项数量为4，检查是否为普通选择题")
            # 检查选项字母是否都在A-D范围内
            all_valid = all(option[0] in ['A', 'B', 'C', 'D'] for option in options)
            print(f"[调试] 所有选项字母是否在A-D范围内: {all_valid}")
            
            if all_valid:
                # 检查选项是否连续且唯一
                option_letters = [option[0] for option in options]
                print(f"[调试] 选项字母列表: {option_letters}")
                print(f"[调试] 排序后的选项字母: {sorted(option_letters)}")
                
                if sorted(option_letters) == ['A', 'B', 'C', 'D']:
                    print(f"[调试] 选项字母连续且唯一，符合普通选择题格式")
                    return '普通选择题', None  # 没有错误原因
                else:
                    print(f"[调试] 选项字母不连续或有重复")
                    return '非标准格式', f'选项字母不连续或有重复，当前选项字母: {option_letters}'
            else:
                invalid_letters = [option[0] for option in options if option[0] not in ['A', 'B', 'C', 'D']]
                print(f"[调试] 存在无效的选项字母: {invalid_letters}")
                return '非标准格式', f'存在无效的选项字母: {invalid_letters}'
        
        # 其他情况
        print(f"[调试] 选项数量{len(options)}不符合标准格式要求")
        return '非标准格式', f'选项数量为{len(options)}，不符合标准的判断题（2个选项）或选择题（4个选项）格式'
    
    def fix_current_question_format(self):
        """修复当前题目的选项格式（F键触发）"""
        if not self.questions:
            self.status_bar.config(text="没有加载的题目")
            print("[调试] 没有加载的题目")
            return
        
        print("[调试] 开始修复当前题目的选项格式")
        current_question = self.questions[self.current_question_index]
        
        # 修复原始内容
        original_content = current_question['original']
        fixed_original, modified = self.fix_option_format(original_content)
        
        if modified:
            # 更新题目内容
            self.questions[self.current_question_index]['original'] = fixed_original
            
            # 重新提取不带引用和带引用的部分
            self.questions[self.current_question_index]['without_quotes'] = self.extract_without_quotes(fixed_original)
            self.questions[self.current_question_index]['with_quotes'] = self.extract_with_quotes(fixed_original)
            
            # 重新分析选项类型
            option_type, error_reason = self.analyze_option_type(self.questions[self.current_question_index]['with_quotes'])
            self.questions[self.current_question_index]['option_type'] = option_type
            self.questions[self.current_question_index]['error_reason'] = error_reason
            
            # 更新显示
            self.display_current_question()
            
            # 更新状态栏
            self.status_bar.config(text=f"成功修复第{self.current_question_index + 1}题的选项格式")
            print(f"[调试] 第{self.current_question_index + 1}题选项格式已修复")
        else:
            self.status_bar.config(text=f"第{self.current_question_index + 1}题无需修复")
            print(f"[调试] 第{self.current_question_index + 1}题无需修复")
    
    def fix_all_question_formats(self):
        """修复所有题目的选项格式"""
        if not self.questions:
            self.status_bar.config(text="没有加载的题目")
            print("[调试] 没有加载的题目")
            return
        
        print("[调试] 开始修复所有题目的选项格式")
        fixed_count = 0
        
        for i, question in enumerate(self.questions):
            # 修复原始内容
            original_content = question['original']
            fixed_original, modified = self.fix_option_format(original_content)
            
            if modified:
                # 更新题目内容
                self.questions[i]['original'] = fixed_original
                
                # 重新提取不带引用和带引用的部分
                self.questions[i]['without_quotes'] = self.extract_without_quotes(fixed_original)
                self.questions[i]['with_quotes'] = self.extract_with_quotes(fixed_original)
                
                # 重新分析选项类型
                option_type, error_reason = self.analyze_option_type(self.questions[i]['with_quotes'])
                self.questions[i]['option_type'] = option_type
                self.questions[i]['error_reason'] = error_reason
                
                fixed_count += 1
                print(f"[调试] 第{i+1}题选项格式已修复")
        
        # 更新状态栏
        self.status_bar.config(text=f"成功修复 {fixed_count} 道题目的选项格式")
        print(f"[调试] 成功修复 {fixed_count} 道题目的选项格式")
        
        # 如果当前显示的题目被修复了，更新显示
        if self.questions and 0 <= self.current_question_index < len(self.questions):
            self.display_current_question()
    
    def extract_questions(self):
        if not self.file_path:
            messagebox.showerror("错误", "请先选择文件")
            return
        
        try:
            print(f"[调试] 开始处理文件: {self.file_path}")
            
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f"[调试] 文件读取完成，内容长度: {len(content)} 字符")
            
            # 分割题目
            raw_questions = self.split_questions_by_separator(content)
            print(f"[调试] 分割后得到 {len(raw_questions)} 个题目部分")
            
            # 处理每个题目，提取两部分内容
            self.questions = []
            non_standard_questions = []
            
            for i, q_content in enumerate(raw_questions, 1):
                print(f"[调试] 处理第 {i} 题")
                no_quotes = self.extract_without_quotes(q_content)
                with_quotes = self.extract_with_quotes(q_content)
                
                if no_quotes or with_quotes:  # 只添加有内容的题目
                    # 分析选项类型，传入带引用的内容
                    option_type, error_reason = self.analyze_option_type(with_quotes)
                    print(f"[调试] 第 {i} 题选项类型: {option_type}")
                    print(f"[调试] 第 {i} 题带引用部分内容: {with_quotes}")
                    
                    # 记录非标准格式题目及其错误原因
                    if option_type == '非标准格式':
                        non_standard_questions.append((i, error_reason))
                    
                    self.questions.append({
                        'index': i,
                        'original': q_content,
                        'without_quotes': no_quotes,
                        'with_quotes': with_quotes,
                        'option_type': option_type,
                        'error_reason': error_reason,
                        'selected_options': []  # 存储用户选择的选项
                    })
                    print(f"[调试] 第 {i} 题提取成功")
                else:
                    print(f"[调试] 第 {i} 题内容为空，跳过")
            
            # 记录非标准格式题目的信息（不再显示弹窗）
            if non_standard_questions:
                print(f"[调试] 发现 {len(non_standard_questions)} 道题目的选项格式非标准")
                for q_index, reason in non_standard_questions:
                    print(f"[调试] 第 {q_index} 题: {reason}")
            
            if not self.questions:
                # 在状态栏显示提示信息，而不是弹窗
                self.status_bar.config(text="未找到有效的题目")
                print("[调试] 状态栏更新: 未找到有效的题目")
                return
            
            # 显示第一题
            self.current_question_index = 0
            self.display_current_question()
            
            # 更新导航按钮状态
            self.update_navigation_buttons()
            
            # 在状态栏显示加载题目数量，而不是弹窗
            self.status_bar.config(text=f"成功提取 {len(self.questions)} 道题目")
            print(f"[调试] 状态栏更新: 成功提取 {len(self.questions)} 道题目")
            
        except Exception as e:
            print(f"[错误] 提取题目时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("错误", f"提取题目时出错: {str(e)}")
    
    
    def display_current_question(self):
        """显示当前题目内容"""
        if 0 <= self.current_question_index < len(self.questions):
            question = self.questions[self.current_question_index]
            
            # 更新题目信息，包含选项类型
            option_type_info = f" - {question['option_type']}"
            if question['option_type'] == '非标准格式' and question['error_reason']:
                option_type_info += f" ({question['error_reason'][:50]}..." if len(question['error_reason']) > 50 else f" ({question['error_reason']})"
            
            self.question_info.config(text=f"共{len(self.questions)}题，当前第{question['index']}题{option_type_info}")
            
            # 根据当前渲染模式显示内容
            if self.render_mode.get() == "text":
                print("[渲染] 文本模式显示")
                # 显示原始文本
                self.no_quote_text.delete(1.0, tk.END)
                self.no_quote_text.insert(1.0, question['without_quotes'])
                
                self.quote_text.delete(1.0, tk.END)
                self.quote_text.insert(1.0, question['with_quotes'])
            else:
                print("[渲染] HTML渲染模式显示")
                # 显示渲染后的HTML
                try:
                    print("[渲染] 开始生成无引用部分HTML")
                    no_quote_html = self.markdown_to_html(question['without_quotes'])
                    self.no_quote_html.set_html(no_quote_html)
                    
                    print("[渲染] 开始生成带引用部分HTML")
                    quote_html = self.markdown_to_html(question['with_quotes'])
                    self.quote_html.set_html(quote_html)
                    
                    print("[渲染] HTML渲染完成")
                except Exception as e:
                    print(f"[渲染错误] HTML渲染失败: {str(e)}")
                    import traceback
                    traceback.print_exc()
    
    def markdown_to_html(self, markdown_text):
        print("[渲染] 开始Markdown转HTML转换")
        
        if not markdown_text or not markdown_text.strip():
            return ""
        
        try:
            # 为文件保存生成完整的HTML文档
            theme = 'dark' if self.dark_mode_var.get() else 'light'
            colors = self.color_schemes[theme]
            
            # 使用markdown库处理
            md_html_content = markdown.markdown(markdown_text, 
                                        extensions=['extra'],
                                        output_format='html5')
            
            # 处理复选框和公式
            md_html_content = re.sub(r'<li>- \[([ x])\]', 
                                r'<li><input type="checkbox" disabled style="margin-right:8px;" \1>', 
                                md_html_content)
            md_html_content = re.sub(r'(?<!\$)\$([^$]+?)\$(?!\$)', 
                                r'<span class="math inline">\\(\1\\)</span>', 
                                md_html_content)
            md_html_content = re.sub(r'\$\$([\s\S]*?)\$\$', 
                                r'<div class="math display">\\[\1\\]</div>', 
                                md_html_content)
            
            # 生成完整HTML
            final_html = f'''
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                        font-size: 16px;
                        line-height: 1.6;
                        padding: 20px;
                        margin: 0;
                        background-color: {colors['html_bg']};
                        color: {colors['html_text']};
                    }}
                    .math.inline {{
                        font-size: 1.1em;
                        padding: 0.1em 0.2em;
                        margin: 0 0.1em;
                    }}
                    .math.display {{
                        margin: 1.5em 0;
                        padding: 0.8em;
                        overflow-x: auto;
                        text-align: center;
                        background-color: {colors.get('formula_bg', 'rgba(0,0,0,0.05)')};
                    }}
                </style>
                <script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>
                <script>
                    MathJax = {{
                        tex: {{
                            inlineMath: [['\\\\(', '\\\\)']],
                            displayMath: [['\\\\[', '\\\\]']],
                            processEscapes: true
                        }},
                        svg: {{
                            fontCache: 'global'
                        }},
                        chtml: {{
                            scale: 1.1,
                            minScale: 0.8,
                            maxScale: 1.5
                        }}
                    }};
                </script>
            </head>
            <body>
                {md_html_content}
            </body>
            </html>
            '''
            
            # 保存渲染结果到文件
            try:
                output_dir = "render_output"
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)
                
                import time
                timestamp = int(time.time())
                filename = os.path.join(output_dir, f"rendered_{timestamp}.html")
                
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(final_html)
                
                print(f"[渲染] HTML生成完成，渲染结果已保存到: {filename}")
            except Exception as e:
                print(f"[渲染错误] 保存渲染结果失败: {str(e)}")
            
            # 为HTMLLabel组件返回优化的HTML片段
            # 添加标题加粗支持，保留公式的原始表示
            
            # 处理基本的Markdown元素
            simple_html = markdown_text
            
            # 处理复选框
            def replace_checkbox(match):
                if match.group(1) == 'x':
                    return '<span style="margin-right:5px;">✓</span>'
                else:
                    return '<span style="margin-right:5px;">□</span>'
            
            simple_html = re.sub(r'- \[([ x])\]', replace_checkbox, simple_html)
            
            # 处理二级标题，添加加粗效果 - 简化正则表达式
            simple_html = re.sub(r'##\s+(.*?)\n', r'<strong>\1</strong><br>', simple_html)
            
            # 针对HTMLLabel组件的公式处理策略
            # 1. 对于行内公式，使用更好的样式并添加数学标记
            simple_html = re.sub(r'\$([^$]+?)\$', 
                               r'<span style="font-family: monospace; background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px; color: #0066cc; font-style: italic;">\( \1 \)</span>', 
                               simple_html)
            
            # 2. 对于块级公式，使用更明显的区块样式并居中显示
            simple_html = re.sub(r'\$\$([\s\S]*?)\$\$', 
                               r'<div style="font-family: monospace; margin: 10px 0; padding: 8px; background-color: #f5f5f5; border-left: 3px solid #0066cc; text-align: center; color: #0066cc; font-style: italic;">\[ \1 \]</div>', 
                               simple_html)
            
            # 转换换行符为<br>
            simple_html = simple_html.replace('\n', '<br>')
            
            # 定义返回给HTMLLabel的HTML片段
            for_htmllabel = f"<div>{simple_html}</div>"
            
            # 为保存到文件生成的完整HTML文档 - 保持原来的复杂处理
            # 这里使用原始的markdown处理方式
            md_html_content = markdown.markdown(markdown_text, 
                                        extensions=['extra'],
                                        output_format='html5')
            
            # 处理复选框
            md_html_content = re.sub(r'<li>- \[([ x])\]', 
                                r'<li><input type="checkbox" disabled style="margin-right:8px;" \1>', 
                                md_html_content)
            
            # 公式处理
            md_html_content = re.sub(r'(?<!\$)\$([^$]+?)\$(?!\$)', 
                                r'<span class="math inline">\\(\1\\)</span>', 
                                md_html_content)
            md_html_content = re.sub(r'\$\$([\s\S]*?)\$\$', 
                                r'<div class="math display">\\[\1\\]</div>', 
                                md_html_content)
            
            final_html = f'''
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                        font-size: 16px;
                        line-height: 1.6;
                        padding: 20px;
                        margin: 0;
                        background-color: {colors['html_bg']};
                        color: {colors['html_text']};
                    }}
                    .math.inline {{
                        font-size: 1.1em;
                        padding: 0.1em 0.2em;
                        margin: 0 0.1em;
                    }}
                    .math.display {{
                        margin: 1.5em 0;
                        padding: 0.8em;
                        overflow-x: auto;
                        text-align: center;
                        background-color: {colors.get('formula_bg', 'rgba(0,0,0,0.05)')};
                    }}
                </style>
                <script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>
                <script>
                    MathJax = {{
                        tex: {{
                            inlineMath: [['\\\\(', '\\\\)']],
                            displayMath: [['\\\\[', '\\\\]']],
                            processEscapes: true
                        }},
                        svg: {{
                            fontCache: 'global'
                        }},
                        chtml: {{
                            scale: 1.1,
                            minScale: 0.8,
                            maxScale: 1.5
                        }}
                    }};
                </script>
            </head>
            <body>
                {md_html_content}
            </body>
            </html>
            '''
            
            print("[渲染] HTML生成完成")
            
            # 保存渲染结果到文件，便于查看
            try:
                # 创建渲染输出目录
                output_dir = "render_output"
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)
                
                # 生成唯一的文件名，基于当前时间戳
                import time
                timestamp = int(time.time())
                filename = os.path.join(output_dir, f"rendered_{timestamp}.html")
                
                # 保存HTML到文件
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(final_html)
                
                print(f"[渲染] 渲染结果已保存到: {filename}")
            except Exception as e:
                print(f"[渲染错误] 保存渲染结果失败: {str(e)}")
            
            # 返回适合HTMLLabel的HTML片段
            print("[渲染] HTML生成完成，返回适合HTMLLabel的HTML片段")
            return for_htmllabel
            
        except Exception as e:
            print(f"[渲染错误] {str(e)}")
            import traceback
            traceback.print_exc()
            return f"<html><body><p>{html.escape(markdown_text)}</p></body></html>"

    def update_navigation_buttons(self):
        # 更新导航按钮状态
        self.prev_button.config(state=tk.NORMAL if self.current_question_index > 0 else tk.DISABLED)
        self.next_button.config(state=tk.NORMAL if self.current_question_index < len(self.questions) - 1 else tk.DISABLED)
        
        # 更新进度条状态和值
        if self.questions:
            self.progress_bar.config(state=tk.NORMAL, to=len(self.questions))
            self.progress_var.set(self.current_question_index + 1)  # 设置当前值，从1开始
        else:
            self.progress_bar.config(state=tk.DISABLED, to=1)
            self.progress_var.set(0)
        print(f"[调试] 进度条更新: 当前第{self.current_question_index + 1}题，共{len(self.questions)}题")
    
    def jump_to_question(self):
        """跳转到指定序号的题目"""
        try:
            jump_num = int(self.jump_entry.get())
            if 1 <= jump_num <= len(self.questions):
                # 转换为索引（索引从0开始）
                self.current_question_index = jump_num - 1
                self.display_current_question()
                self.update_navigation_buttons()
                print(f"[调试] 跳转到题目 #{jump_num}")
            else:
                messagebox.showerror("错误", f"请输入1-{len(self.questions)}之间的数字")
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字")
    
    def prev_question(self):
        if self.current_question_index > 0:
            self.current_question_index -= 1
            self.display_current_question()
            self.update_navigation_buttons()
    
    def get_current_question_option_count(self):
        """获取当前题目的选项数量"""
        if 0 <= self.current_question_index < len(self.questions):
            question = self.questions[self.current_question_index]
            option_type = question['option_type']
            
            if option_type == '判断题':
                print("[调试] 当前是判断题，有2个选项")
                return 2
            elif option_type == '普通选择题':
                print("[调试] 当前是普通选择题，有4个选项")
                return 4
            else:
                print(f"[调试] 当前是非标准格式题目，类型: {option_type}")
                return 0
        return 0
    
    def on_progress_change(self, value):
        """处理进度条值改变事件，实现拖动滑动框切换题目"""
        try:
            # 获取拖动后的值并转换为整数
            new_index = int(float(value)) - 1  # 转换为0-based索引
            # 确保索引有效且与当前题目不同
            if 0 <= new_index < len(self.questions) and new_index != self.current_question_index:
                print(f"[调试] 拖动滑动框切换题目: {self.current_question_index + 1} -> {new_index + 1}")
                self.current_question_index = new_index
                self.display_current_question()
                self.update_navigation_buttons()
        except ValueError:
            print("[调试] 输入不是有效的数字")
    
    def next_question(self):
        if self.current_question_index < len(self.questions) - 1:
            self.current_question_index += 1
            self.display_current_question()
            self.update_navigation_buttons()
    
    def export_without_quotes(self):
        if not self.questions:
            messagebox.showerror("错误", "请先提取题目")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".md",
            filetypes=[("Markdown文件", "*.md"), ("文本文件", "*.txt")]
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    for question in self.questions:
                        f.write(question['without_quotes'])
                        f.write('\n\n---\n\n')
                messagebox.showinfo("成功", "不带引用部分已导出")
            except Exception as e:
                messagebox.showerror("错误", f"导出失败: {str(e)}")
    
    def export_with_quotes(self):
        """导出带引用部分的题目"""
        if not self.questions:
            messagebox.showerror("错误", "请先提取题目")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".md",
            filetypes=[("Markdown文件", "*.md"), ("文本文件", "*.txt")]
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    for question in self.questions:
                        f.write(question['with_quotes'])
                        f.write('\n\n---\n\n')
                messagebox.showinfo("成功", "带引用部分已导出")
            except Exception as e:
                messagebox.showerror("错误", f"导出失败: {str(e)}")
    
    def switch_render_mode(self):
        """切换渲染模式（文本/HTML）"""
        print(f"[渲染] 切换渲染模式，新模式: {self.render_mode.get()}")
        mode = self.render_mode.get()
        
        if mode == "text":
            # 切换到文本视图
            self.no_quote_html_frame.pack_forget()
            self.no_quote_text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            self.quote_html_frame.pack_forget()
            self.quote_text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            print("[渲染] 已切换到文本视图")
        else:
            # 切换到HTML视图
            self.no_quote_text_frame.pack_forget()
            self.no_quote_html_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            self.quote_text_frame.pack_forget()
            self.quote_html_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            print("[渲染] 已切换到HTML视图")
        
        # 重新显示当前题目以适应新模式
        if self.questions:
            print("[渲染] 重新显示当前题目以适应新模式")
            self.display_current_question()
    
    def update_question_content_with_selected(self, question_content, selected_option):
        """更新题目内容中的选项选中状态"""
        # 检查并更新引用块内和块外的选项
        content_with_quotes = question_content
        
        # 处理两种格式的选项
        patterns = [
            # 引用块内的选项格式
            fr'>\s*-\s*\[([ x])\]\s*{selected_option}\.?\s*',
            # 引用块外的选项格式
            fr'^\s*-\s*\[([ x])\]\s*{selected_option}\.?\s*'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, content_with_quotes, re.MULTILINE)
            for match in matches:
                current_status = match.group(1)
                new_status = 'x' if current_status == ' ' else ' '
                old_str = match.group(0)
                new_str = old_str.replace(f'[{current_status}]', f'[{new_status}]')
                content_with_quotes = content_with_quotes.replace(old_str, new_str)
                print(f"[调试] 更新选项{selected_option}状态从[{current_status}]到[{new_status}]")
                return content_with_quotes  # 找到并更新后立即返回
        
        return content_with_quotes
    
    def auto_save(self):
        """自动保存当前所有题目的选择状态"""
        if self.auto_save_var.get() and self.file_path:
            try:
                # 创建保存路径（在原文件名后添加_autosave）
                file_dir, file_name = os.path.split(self.file_path)
                file_base, file_ext = os.path.splitext(file_name)
                save_path = os.path.join(file_dir, f"{file_base}_autosave{file_ext}")
                
                # 保存所有题目的带引用部分
                with open(save_path, 'w', encoding='utf-8') as f:
                    for question in self.questions:
                        f.write(question['with_quotes'])
                        f.write('\n\n---\n\n')
                
                print(f"[调试] 自动保存成功，文件保存至: {save_path}")
                return True
            except Exception as e:
                print(f"[调试] 自动保存失败: {str(e)}")
                return False
        return False
    
    def save_config(self):
        """保存当前配置到配置文件"""
        try:
            # 创建配置数据
            config_data = {
                "last_file_path": self.file_path,
                "current_question_index": self.current_question_index,
                "auto_save": self.auto_save_var.get(),
                "single_choice": self.single_choice_var.get(),
                "render_mode": self.render_mode.get()
            }
            
            # 保存配置到文件
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            
            print(f"[调试] 配置保存成功: {self.config_file}")
            return True
        except Exception as e:
            print(f"[调试] 配置保存失败: {str(e)}")
            return False
            
    def on_closing(self):
        """处理窗口关闭事件"""
        print("[调试] 窗口关闭事件触发，准备保存配置")
        
        # 保存当前配置
        self.save_config()
        
        # 执行正常关闭
        print("[调试] 配置保存完成，准备关闭程序")
        self.root.destroy()
    def load_config(self):
        """从配置文件加载配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # 恢复配置
                if "last_file_path" in config_data:
                    self.file_path = config_data["last_file_path"]
                    print(f"[调试] 加载上次文件路径: {self.file_path}")
                
                if "auto_save" in config_data:
                    self.auto_save_var.set(config_data["auto_save"])
                    print(f"[调试] 加载自动保存设置: {config_data['auto_save']}")
                
                if "single_choice" in config_data:
                    self.single_choice_var.set(config_data["single_choice"])
                    print(f"[调试] 加载单选模式设置: {config_data['single_choice']}")
                
                if "render_mode" in config_data:
                    self.render_mode.set(config_data["render_mode"])
                    print(f"[调试] 加载渲染模式设置: {config_data['render_mode']}")
                
                print(f"[调试] 配置加载成功: {self.config_file}")
                return config_data
            else:
                print(f"[调试] 配置文件不存在: {self.config_file}")
                return None
        except Exception as e:
            print(f"[调试] 配置加载失败: {str(e)}")
            return None
    
    def restore_last_session(self):
        """恢复上次的工作会话"""
        print("[调试] 尝试恢复上次会话")
        config_data = self.load_config()
        
        if config_data and self.file_path and os.path.exists(self.file_path):
            try:
                print(f"[调试] 发现上次打开的文件: {self.file_path}，尝试自动打开")
                
                # 更新文件标签显示
                self.file_label.config(text=os.path.basename(self.file_path), fg="black")
                
                # 自动提取题目
                self.extract_questions()
                
                # 如果保存了上次的题目索引，尝试恢复到该位置
                if "current_question_index" in config_data and config_data["current_question_index"] >= 0:
                    saved_index = config_data["current_question_index"]
                    # 确保索引有效
                    if 0 <= saved_index < len(self.questions):
                        self.current_question_index = saved_index
                        self.display_current_question()
                        print(f"[调试] 已恢复到第{saved_index + 1}题")
                
                print("[调试] 会话恢复成功")
            except Exception as e:
                print(f"[调试] 会话恢复失败: {str(e)}")
        else:
            print("[调试] 没有找到可恢复的会话或上次文件不存在")
    
    def remove_answer_and_analysis(self, content):
        """移除答案和解析部分"""
        # 匹配常见的答案和解析格式
        # 匹配 '答案：' 或 '参考答案：' 开头的行，及其之后直到下一个部分的内容
        patterns = [
            # 移除'答案：' 或 '参考答案：' 及其后面的内容（包括多个空行）
            r'(答案|参考答案)[:：].*?(?=\n\n|$)',
            # 移除'> 解析：' 或 '解析：' 及其后面的内容（包括多个空行）
            r'[>]?\s*(解析)[:：].*?(?=\n\n|$)',
            # 移除'>'引用块中的答案部分
            r'>\s*[A-D]\).*?(?=\n\n|$)',
            # 移除'> 答案：' 或 '> 参考答案：' 及其后面的内容
            r'>\s*(答案|参考答案)[:：].*?(?=\n\n|$)',
            # 特别处理AI答案为"的"的文本
            r'>\s*AI答案为(\s*"的"\s*)\.?.*?(?=\n\n|$)',
            r'>\s*AI答案为的.*?(?=\n\n|$)'
        ]
        
        result = content
        for pattern in patterns:
            # 使用DOTALL标志，让.匹配换行符
            result = re.sub(pattern, '', result, flags=re.DOTALL)
        
        return result
    
    def select_option(self, key):
        """根据按键选择对应选项"""
        option_map = {'1': 'A', '2': 'B', '3': 'C', '4': 'D'}
        option_count = self.get_current_question_option_count()
        
        print(f"[调试] 进入select_option方法，按键: {key}")
        
        if 0 <= self.current_question_index < len(self.questions) and option_count > 0:
            # 检查按键是否有效
            if key in option_map and int(key) <= option_count:
                selected_option = option_map[key]
                print(f"[调试] 按键{key}选择了选项{selected_option}")
                
                # 获取当前题目
                question = self.questions[self.current_question_index]
                
                # 确保selected_options列表存在且类型正确
                if not hasattr(question, 'selected_options') or not isinstance(question['selected_options'], list):
                    question['selected_options'] = []
                    print(f"[调试] 创建缺失的selected_options列表")
                
                # 打印更新前的状态
                print(f"[调试] 更新前选中选项: {question['selected_options']}")
                
                # 检查是否是单选模式
                is_single_choice = self.single_choice_var.get()
                print(f"[调试] 当前是否为单选模式: {is_single_choice}")
                
                # 先检查选项是否已经在选中列表中
                is_already_selected = selected_option in question['selected_options']
                print(f"[调试] 选项{selected_option}是否已选中: {is_already_selected}")
                
                # 标记是否需要清除答案和解析（仅当用户实际修改了选项状态时）
                need_clear_analysis = False
                
                # 处理单选模式的逻辑
                if is_single_choice:
                    # 单选模式下的特殊处理
                    if not is_already_selected:
                        print(f"[调试] 单选模式: 切换到选项{selected_option}")
                        need_clear_analysis = True  # 用户切换了选项，需要清除答案和解析
                        
                        # 先取消所有其他选项
                        for option in list(question['selected_options']):
                            # 更新题目内容中的其他选项为未选中状态
                            question['with_quotes'] = self.update_question_content_with_selected(question['with_quotes'], option)
                            question['without_quotes'] = self.update_question_content_with_selected(question['without_quotes'], option)
                            print(f"[调试] 单选模式下取消选中选项{option}")
                        
                        # 清空选中选项列表
                        question['selected_options'] = []
                        
                        # 更新题目内容中的当前选项为选中状态
                        question['with_quotes'] = self.update_question_content_with_selected(question['with_quotes'], selected_option)
                        question['without_quotes'] = self.update_question_content_with_selected(question['without_quotes'], selected_option)
                        
                        # 将当前选项添加到选中列表
                        question['selected_options'].append(selected_option)
                        print(f"[调试] 单选模式: 选中选项{selected_option}")
                    else:
                        print(f"[调试] 单选模式: 选项{selected_option}已选中，不执行任何操作")
                        # 单选模式下不允许取消已选中的选项
                        # 直接返回，不进行任何修改
                        pass
                else:
                    # 多选模式的逻辑
                    # 更新题目内容中的当前选项选中状态
                    question['with_quotes'] = self.update_question_content_with_selected(question['with_quotes'], selected_option)
                    question['without_quotes'] = self.update_question_content_with_selected(question['without_quotes'], selected_option)
                    
                    # 更新选中选项列表（切换选中状态）
                    if is_already_selected:
                        question['selected_options'].remove(selected_option)
                        print(f"[调试] 多选模式: 取消选中选项{selected_option}")
                        need_clear_analysis = True  # 用户修改了选项状态，需要清除答案和解析
                    else:
                        question['selected_options'].append(selected_option)
                        print(f"[调试] 多选模式: 选中选项{selected_option}")
                        need_clear_analysis = True  # 用户修改了选项状态，需要清除答案和解析
                
                # 如果用户修改了选项状态，清除答案和解析部分
                if need_clear_analysis:
                    print(f"[调试] 清除第{question['index']}题的答案和解析部分")
                    # 移除答案和解析部分
                    question['with_quotes'] = self.remove_answer_and_analysis(question['with_quotes'])
                    question['without_quotes'] = self.remove_answer_and_analysis(question['without_quotes'])
                
                # 打印更新后的状态
                print(f"[调试] 更新后选中选项: {question['selected_options']}")
                
                # 重新显示当前题目以更新UI
                print("[调试] 调用display_current_question更新UI")
                self.display_current_question()
                
                # 强制更新UI
                self.root.update_idletasks()
                print("[调试] 强制更新UI完成")
                
                # 检查是否需要自动保存
                self.auto_save()
                
                return selected_option
            else:
                print(f"[调试] 无效的按键{key}，当前题目只有{option_count}个选项")
        else:
            print("[调试] 当前题目不支持键盘选择选项")
        return None
    
    def run(self):
        print("[调试] 启动主循环")
        # 自动加载公式测试文件
        test_file = "test.md"  # 使用我们创建的测试文件
        print(f"[调试] 自动加载公式测试文件: {test_file}")
        if os.path.exists(test_file):
            self.file_path = test_file
            # 读取文件内容并提取题目
            with open(test_file, "r", encoding="utf-8") as f:
                content = f.read()
            self.questions = self.split_questions_by_separator(content)
            self.extract_questions()
            # 显示第一题
            if self.questions:
                self.current_question_index = 0
                self.display_current_question()
                self.update_navigation_buttons()
        
        # 确保窗口获得焦点
        self.root.focus_set()
        print("[调试] 确认窗口焦点设置")
        
        self.root.mainloop()
        print("[调试] 主循环结束")

# 创建并运行应用
if __name__ == "__main__":
    app = QuestionExtractor()
    app.run()