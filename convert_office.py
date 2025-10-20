import os
import sys
from markitdown import MarkItDown # 导入 MarkItDown 库

# --- 1. 从命令行参数获取文件路径 ---
if len(sys.argv) < 2:
    print("❌ 错误：请提供要转换的文件路径作为参数。")
    print("用法: python convert_office.py <文件路径>")
    sys.exit(1)

input_file_path = sys.argv[1]

# 检查文件是否存在
if not os.path.exists(input_file_path):
    print(f"❌ 错误：文件不存在 -> {input_file_path}")
    sys.exit(1)

# 初始化 MarkItDown 转换器 ---
md = MarkItDown() # 创建 MarkItDown 实例

try:
    print(f"开始转换文件：{input_file_path}...")

    # --- 3. 执行转换 ---
    conversion_result = md.convert(input_file_path)

    # 4. 生成输出文件名
    # 将原始文件的扩展名替换为 .md
    # 将路径分为纯路径和扩展名并存入元组，然后赋值给两个变量，其中-表示占位符，以为着我们不关心扩展名部分
    base_name, _ = os.path.splitext(input_file_path) 
    output_file_path = base_name + ".md" # 生成新的路径名

    # --- 5. 写入 Markdown 文件 ---
    # 请以 'utf-8' 编码，用写入模式（'w'） 打开路径为 output_file_path 的文件
    # 并将其命名为 f。请在接下来的代码块中让我使用 f 来操作它，
    # 并且无论发生什么，操作一结束就自动帮我把文件关好。
    with open(output_file_path, "w", encoding="utf-8") as f:
        f.write(conversion_result.text_content)

    print("🎉 转换成功！")
    print(f"Markdown 文件已保存到：{output_file_path}")

except Exception as e:
    # 使用 f-string 格式化错误信息，更清晰
    print(f"❌ 转换失败，出现错误： {e}")