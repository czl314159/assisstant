"""
脚本名称: Office 和 PDF 到 Markdown 转换器 (office_to_md.py)

功能描述:
    此脚本是一个实用工具，用于将 Microsoft Office 文档（.docx, .pptx, .xlsx）
    以及 PDF 文件转换为 Markdown 格式。它支持处理单个文件或指定文件夹中的所有支持文件。

使用方法:
    在终端中运行，并提供要转换的文件或文件夹的路径作为参数：

    1.  **转换单个文件**:
        `python office_to_md.py /path/to/your/document.docx`
        `python office_to_md.py /path/to/your/presentation.pptx`
        `python office_to_md.py /path/to/your/spreadsheet.xlsx`
        `python office_to_md.py /path/to/your/report.pdf`

    2.  **转换文件夹中的所有支持文件**:
        `python office_to_md.py /path/to/your/documents_folder`

依赖:
    -   `markitdown`
"""
import os # 导入 os 模块以处理文件路径和检查文件是否存在，os 的作用是提供与操作系统进行交互的功能
import sys # 导入 sys 模块以处理命令行参数，sys的作用是提供对解释器使用或维护的一些变量和函数的访问
from markitdown import MarkItDown # 导入 MarkItDown 库，而不是导入整个 markitdown 模块

# --- 1. 将转换逻辑封装成一个函数 ---
def convert_file(file_path):
    """
    转换单个 Office 文件为 Markdown。
    :param file_path: 要转换的单个文件的完整路径。
    """
    # 定义支持的文件扩展名，只处理这些类型的文件
    supported_extensions = ('.docx', '.pptx', '.xlsx', '.pdf')
    if not file_path.lower().endswith(supported_extensions):
        # 如果文件类型不支持，就静默跳过，不打印信息，以免处理文件夹时输出过多无关内容
        return
        
    try:
        # 打印当前正在转换的文件名，os.path.basename可以从完整路径中提取出文件名
        print(f"⏳ 正在转换: {os.path.basename(file_path)}...")
        
        # 初始化 MarkItDown 转换器 并执行转换
        md = MarkItDown() # 创建 MarkItDown 实例
        conversion_result = md.convert(file_path) # 调用convert方法
        
        # 生成输出文件名
        base_name, _ = os.path.splitext(file_path) 
        output_file_path = base_name + ".md" # 生成新的路径名
        
        # 写入 Markdown 文件
        with open(output_file_path, "w", encoding="utf-8") as f:
            f.write(conversion_result.text_content)
        
        print(f"✅ 转换成功 -> {os.path.basename(output_file_path)}")
        
    except Exception as e:
        # 使用 f-string 格式化错误信息，更清晰
        print(f"❌ 转换失败: {os.path.basename(file_path)}，错误： {e}")

# --- 主程序入口 ---
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ 错误：请提供要转换的文件或文件夹路径作为参数。")
        print("用法: python convert_office.py <文件或文件夹路径>")
        sys.exit(1)
    
    input_path = sys.argv[1]
    
    # 检查路径是否存在
    if not os.path.exists(input_path):
        print(f"❌ 错误：路径不存在 -> {input_path}")
        sys.exit(1)
    
    # 判断输入是文件还是文件夹
    if os.path.isdir(input_path):
        print(f"📁 开始处理文件夹: {input_path}")
        # os.walk 会遍历文件夹下的所有子文件夹和文件
        for root, dirs, files in os.walk(input_path):
            for file in files:
                full_path = os.path.join(root, file)
                convert_file(full_path)
        print("\n🎉 所有文件处理完毕！")
    elif os.path.isfile(input_path):
        # 如果是单个文件，直接调用转换函数
        convert_file(input_path)
    else:
        print(f"❌ 错误：输入路径既不是文件也不是文件夹 -> {input_path}")