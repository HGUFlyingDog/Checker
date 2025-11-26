import re
import os
import sys
import argparse
from typing import List
from pathlib import Path

def split_markdown_by_questions(input_file: str, output_prefix: str = "questions", questions_per_file: int = 100):
    """
    按题目块分割Markdown文件
    
    Args:
        input_file: 输入的Markdown文件路径
        output_prefix: 输出文件前缀
        questions_per_file: 每个文件包含的题目块数量
    """
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 分割内容为块
    blocks = content.split('\n---\n')
    
    # 过滤出有效的题目块（包含 "> ## " 的块）
    valid_blocks = []
    for block in blocks:
        # 检查块中是否包含引用格式的二级标题
        if re.search(r'^> ## ', block, re.MULTILINE):
            valid_blocks.append(block)
    
    print(f"总共找到 {len(valid_blocks)} 个有效的题目块")
    
    # 创建输出目录
    output_dir = os.path.dirname(input_file) if os.path.dirname(input_file) else "."
    
    # 按指定数量分割并保存文件
    for i in range(0, len(valid_blocks), questions_per_file):
        chunk = valid_blocks[i:i + questions_per_file]
        file_number = (i // questions_per_file + 1) * questions_per_file
        output_filename = f"{output_prefix}_{file_number}.md"
        output_path = os.path.join(output_dir, output_filename)
        
        # 用 "---" 连接块
        chunk_content = "\n---\n".join(block.strip() for block in chunk)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(chunk_content)
        
        print(f"已保存 {output_path}，包含 {len(chunk)} 个题目块")


def split_markdown_by_questions_v2(input_file: str, output_prefix: str = "questions", questions_per_file: int = 100):
    """
    按题目块分割Markdown文件（针对当前项目格式的版本）
    
    Args:
        input_file: 输入的Markdown文件路径
        output_prefix: 输出文件前缀
        questions_per_file: 每个文件包含的题目块数量
    """
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 使用更准确的正则表达式匹配题目块
    # 每个题目块包含一个以 "> ##" 开头的标题，以及后续的内容直到下一个 "---" 或文件结束
    pattern = r'(> ##.*?)(?=\n---\n> ##|\Z)'
    blocks = re.findall(pattern, content, re.DOTALL)
    
    # 如果没有找到匹配的块，尝试另一种模式
    if len(blocks) <= 1:
        # 尝试匹配以 "> ##" 开始的块，直到下一个 "> ##" 或文件结束
        pattern2 = r'(> ##.*?)(?=\n> ##|\Z)'
        blocks = re.findall(pattern2, content, re.DOTALL)
    
    print(f"总共找到 {len(blocks)} 个题目块")
    
    # 创建输出目录
    output_dir = os.path.dirname(input_file) if os.path.dirname(input_file) else "."
    
    # 按指定数量分割并保存文件
    for i in range(0, len(blocks), questions_per_file):
        chunk = blocks[i:i + questions_per_file]
        file_number = (i // questions_per_file + 1) * questions_per_file
        output_filename = f"{output_prefix}_{file_number}.md"
        output_path = os.path.join(output_dir, output_filename)
        
        # 用 "---" 连接块
        chunk_content = "\n---\n".join(block.strip() for block in chunk)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(chunk_content)
        
        print(f"已保存 {output_path}，包含 {len(chunk)} 个题目块")


def merge_markdown_files(input_dir: str, output_file: str, file_pattern: str = r"questions_\d+\.md"):
    """
    合并分割的Markdown文件
    
    Args:
        input_dir: 包含分割文件的目录
        output_file: 合并后的输出文件路径
        file_pattern: 文件名匹配模式
    """
    # 获取所有匹配的文件
    files = [f for f in os.listdir(input_dir) if re.match(file_pattern, f)]
    
    # 按数字排序文件
    files.sort(key=lambda x: int(re.findall(r'\d+', x)[0]) if re.findall(r'\d+', x) else 0)
    
    merged_content = []
    file_count = 0
    
    for file in files:
        file_path = os.path.join(input_dir, file)
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if content:  # 只有当文件不为空时才添加
                merged_content.append(content)
                file_count += 1
    
    # 用 "---" 连接所有内容
    final_content = "\n---\n".join(merged_content)
    
    # 写入合并后的文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(final_content)
    
    print(f"已合并 {file_count} 个文件到 {output_file}")


def get_all_question_blocks(input_file: str) -> List[str]:
    """
    提取所有题目块用于分析
    
    Args:
        input_file: 输入的Markdown文件路径
        
    Returns:
        所有题目块的列表
    """
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 使用正则表达式匹配题目块
    pattern = r'(> ##.*?)(?=\n---\n> ##|\Z)'
    blocks = re.findall(pattern, content, re.DOTALL)
    
    # 如果没有找到匹配的块，尝试另一种模式
    if len(blocks) <= 1:
        pattern2 = r'(> ##.*?)(?=\n> ##|\Z)'
        blocks = re.findall(pattern2, content, re.DOTALL)
    
    return blocks


def count_total_questions(input_file: str) -> int:
    """
    统计文件中题目块的总数
    
    Args:
        input_file: 输入的Markdown文件路径
        
    Returns:
        题目块的数量
    """
    blocks = get_all_question_blocks(input_file)
    return len(blocks)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Markdown题目块分割与合并工具")
    parser.add_argument(
        "action", 
        choices=["split", "merge"], 
        help="选择操作类型: split(分割) 或 merge(合并)"
    )
    parser.add_argument(
        "--input", 
        "-i", 
        default="extracted_questions_processed.md",
        help="输入文件路径 (分割时使用)"
    )
    parser.add_argument(
        "--output-prefix", 
        "-p", 
        default="questions",
        help="输出文件前缀 (分割时使用)"
    )
    parser.add_argument(
        "--questions-per-file", 
        "-q", 
        type=int, 
        default=100,
        help="每个文件包含的题目数量 (分割时使用)"
    )
    parser.add_argument(
        "--input-dir", 
        "-d", 
        default=".",
        help="输入目录路径 (合并时使用)"
    )
    parser.add_argument(
        "--output-file", 
        "-o", 
        default="merged_questions.md",
        help="合并后的输出文件路径 (合并时使用)"
    )
    parser.add_argument(
        "--file-pattern", 
        "-f", 
        default=r"questions_\d+\.md",
        help="文件名匹配模式 (合并时使用)"
    )
    
    args = parser.parse_args()
    
    if args.action == "split":
        # 检查输入文件是否存在
        if not os.path.exists(args.input):
            print(f"错误: 文件 {args.input} 不存在")
            return
        
        # 分割文件
        split_markdown_by_questions_v2(
            args.input, 
            args.output_prefix, 
            args.questions_per_file
        )
        
    elif args.action == "merge":
        # 合并文件
        merge_markdown_files(
            args.input_dir, 
            args.output_file, 
            args.file_pattern
        )


if __name__ == "__main__":
    main()