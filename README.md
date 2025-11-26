# Markdown 题目处理工具

## 项目概述

本项目是一个用于处理Markdown格式题目文件的工具集，主要提供题目提取、分割和合并功能，帮助用户更有效地管理大量题目内容。

## 功能介绍

- **题目分割**：将包含大量题目的单个Markdown文件分割成多个较小的文件，方便管理和处理
- **文件合并**：将之前分割的多个Markdown题目文件重新合并成一个完整的文件
- **题目提取**：支持从原始文档中提取结构化的题目内容（通过question_extractor.py实现）

## 安装说明

### 环境要求
- Python 3.6+
- 无额外依赖（使用Python标准库）

### 安装步骤

1. 克隆或下载本项目到本地
2. 确保已安装Python 3.6或更高版本
3. 无需安装额外依赖，项目仅使用Python标准库

## 使用方法

### markdown_splitter.py

该工具用于分割和合并Markdown格式的题目文件。

#### 基本格式
```bash
python markdown_splitter.py [action] [options]
```

#### 操作类型
- `split`: 分割文件
- `merge`: 合并文件

#### 分割操作选项
```bash
# 使用默认参数分割文件
python markdown_splitter.py split

# 指定输入文件、输出前缀和每文件题目数量
python markdown_splitter.py split --input your_input_file.md --output-prefix questions --questions-per-file 50
```

参数说明：
- `--input`, `-i`: 输入的Markdown文件路径（默认：`extracted_questions_processed.md`）
- `--output-prefix`, `-p`: 输出文件前缀（默认：`questions`）
- `--questions-per-file`, `-q`: 每个文件包含的题目数量（默认：100）

#### 合并操作选项
```bash
# 使用默认参数合并文件
python markdown_splitter.py merge

# 指定输入目录、输出文件和文件名模式
python markdown_splitter.py merge --input-dir ./split_files --output-file merged_questions.md --file-pattern "questions_\d+\.md"
```

参数说明：
- `--input-dir`, `-d`: 包含分割文件的目录路径（默认：`.`）
- `--output-file`, `-o`: 合并后的输出文件路径（默认：`merged_questions.md`）
- `--file-pattern`, `-f`: 文件名匹配模式（默认：`questions_\d+\.md`）

### question_extractor.py

#### 功能介绍
`question_extractor.py`是一个基于tkinter的图形界面应用程序，专门用于从Markdown文件中提取、分析和处理题目内容。它提供了直观的用户界面，支持题目浏览、格式分析和选项修复等功能。

#### 主要特性
- **题目提取与解析**：自动从Markdown文件中提取题目内容，通过`---`分隔符识别不同题目
- **双栏显示**：将题目内容分为带引用和不带引用两部分，便于比较和编辑
- **题目类型分析**：自动识别题目类型（判断题、选择题或非标准格式），并提供错误原因说明
- **选项格式修复**：支持修复选项格式问题，将一行多个选项转换为每行一个选项的标准格式
- **多视图模式**：提供文本视图和HTML渲染视图两种显示模式
- **数学公式支持**：集成MathJax支持，可渲染题目中的数学公式
- **题目导航**：支持前后浏览题目、跳转到指定序号题目
- **夜间模式**：提供深色/浅色主题切换，保护眼睛
- **自动保存**：自动将渲染结果保存为HTML文件，便于后续查看

#### 使用方法
1. 运行程序：
```bash
python question_extractor.py
```

2. 基本操作：
   - 点击文件选择按钮选择包含题目的Markdown文件
   - 程序会自动提取并显示题目内容
   - 使用导航按钮浏览不同题目
   - 输入题目序号并点击跳转按钮可直接跳转到特定题目
   - 使用格式修复功能可修复选项格式问题

3. 高级功能：
   - 切换视图模式（文本/HTML渲染）查看不同格式的题目
   - 切换深色/浅色模式以适应不同环境
   - 渲染后的HTML文件会自动保存在`render_output`目录中

## 项目结构

```
Checker/
├── .gitignore           # Git忽略文件
├── markdown_splitter.py # Markdown分割与合并工具
├── question_extractor.py # 题目提取工具
├── requirements.txt     # 项目依赖列表
└── README.md            # 项目说明文档
```

## 注意事项

1. **文件格式要求**：工具专门处理以 `> ##` 格式开头的题目块，请确保输入文件符合此格式
2. **路径问题**：运行脚本时请确保在正确的项目目录下执行
3. **输出目录**：默认情况下，分割文件会保存在与输入文件相同的目录中
4. **性能考虑**：对于特别大的文件，可能需要调整每文件包含的题目数量以获得最佳性能
5. **文件命名**：分割后的文件会以 `output_prefix_数字.md` 格式命名
6. **合并顺序**：合并时会按照文件名中的数字顺序进行排序

## 许可证

本项目采用MIT许可证。
