import os
from markitdown import MarkItDown

# --- 1. 定义你的文件路径 ---
# 替换成你想要转换的 Office 文件路径
input_file_path = r"D:\Desktop\科学分钱\荣誉激励\xx集团荣誉激励方案.docx"
# 或者 "C:\\Users\\YourName\\Documents\\slides.pptx"
# 或者 "C:\\Users\\YourName\\Data\\budget.xlsx"

# --- 2. 初始化 MarkItDown 转换器 ---
# 如果不涉及图片描述等AI增强功能，保持默认即可
md = MarkItDown()

try:
    print(f"开始转换文件：{input_file_path}...")

    # --- 3. 执行转换 ---
    conversion_result = md.convert(input_file_path)

    # 4. 生成输出文件名
    # 将原始文件的扩展名替换为 .md
    base_name, _ = os.path.splitext(input_file_path)
    output_file_path = base_name + ".md"

    # --- 5. 写入 Markdown 文件 ---
    with open(output_file_path, "w", encoding="utf-8") as f:
        f.write(conversion_result.text_content)

    print("🎉 转换成功！")
    print(f"Markdown 文件已保存到：{output_file_path}")

except Exception as e:
    print(f"❌ 转换失败，出现错误：{e}")