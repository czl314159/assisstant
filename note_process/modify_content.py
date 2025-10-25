import re
import os
import sys # 导入 sys 模块以处理命令行参数

def format_paragraph(file_path):
    """
    读取文件内容，移除段落内部的单个换行符，保留段落间的空行。

    Args:
        file_path (str): 需要处理的文本文件的路径。

    Returns:
        str: 经过格式化处理后的文本内容。
        如果文件不存在或读取失败，则返回None。
    """
    # 检查文件是否存在
    if not os.path.exists(file_path):
        print(f"错误：文件 '{file_path}' 不存在。")
        return None

    try:
        # 读取整个文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 1. 使用正则表达式替换掉段落内部的换行符
        #    - `(?<!\n)\n(?!\n)` 这个是核心的正则表达式
        #    - `(?<!\n)`: 这是一个“负向先行断言”，意思是前面的字符不能是换行符 `\n`。
        #    - `\n`: 匹配一个换行符。
        #    - `(?!\n)`: 这是一个“负向先行断言”，意思是后面的字符不能是换行符 `\n`。
        #    - 综合起来，这个表达式只匹配那些“孤立”的换行符，也就是段落内部的硬换行。
        #    - 我们将匹配到的换行符替换为空字符串 `''`，即直接删除。
        formatted_content = re.sub(r'(?<!\n)\n(?!\n)', '', content)

        # 2. （可选）将多个连续的空行合并为一个，使格式更整洁
        #    - `\n{2,}` 匹配两个或更多连续的换行符
        #    - `\n\n` 替换为两个换行符，确保段落间只有一个空行
        formatted_content = re.sub(r'\n{2,}', '\n\n', formatted_content)

        return formatted_content

    except Exception as e:
        print(f"处理文件时发生错误: {e}")
        return None

# --- 主程序开始 ---
if __name__ == "__main__":
    # 1. 检查命令行参数是否正确
    # sys.argv 是一个列表，第一个元素是脚本名，第二个元素是用户输入的第一个参数
    if len(sys.argv) != 2:
        print("用法: python note_process.py <文件路径>")
        print("示例: python note_process.py \"d:\\我的文档\\笔记.md\"")
        sys.exit(1) # 参数不正确，退出程序

    # 2. 从命令行获取文件路径
    target_file_path = sys.argv[1]

    # 调用函数处理文件
    new_content = format_paragraph(target_file_path)

    # 如果处理成功，打印结果或写入新文件
    if new_content:
        # 构建新文件名，例如 "原文件名_formatted.md"
        directory, filename = os.path.split(target_file_path)
        name, ext = os.path.splitext(filename)
        new_file_path = os.path.join(directory, f"{name}_formatted{ext}")

        try:
            # 将处理后的内容写入新文件
            with open(new_file_path, 'w', encoding='utf-8') as f: f.write(new_content)
            print(f"处理完成！结果已保存到新文件: {new_file_path}")
        except Exception as e:
            print(f"写入新文件时发生错误: {e}")
