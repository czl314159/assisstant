import pandas as pd  # 导入pandas库，并使用pd作为别名，这是一个广泛接受的惯例。
# pandas库是Python中用于数据分析的核心库，它提供了DataFrame这个强大的数据结构。
# 可处理多种格式的数据文件，包括Excel、CSV、SQL等。
import sys  # 导入sys模块，用于访问命令行参数。
import os  # 导入os模块，用于处理文件路径和文件系统操作。

def parse_arguments():
    """
    功能: 解析和验证命令行参数。
    - 检查用户是否提供了文件路径。
    - 解析可选的Sheet名或索引。
    - 验证文件路径是否存在且为文件。
    返回: 一个元组 (input_excel_path, sheet_to_read, sheet_display_name)。
    """
    # 检查命令行参数的数量。sys.argv[0] 是脚本本身的名称。
    # sys.argv[1] 是用户输入的第一个参数（文件路径）。
    # sys.argv[2] 是用户输入的第二个参数（可选的Sheet名或索引）。
    if len(sys.argv) < 2:
        # 如果用户没有提供文件路径，打印使用说明并退出程序。
        print("❌ 错误：请在命令行中提供要处理的Excel文件路径。")
        print("用法示例：")
        print("  python excel_process.py <你的Excel文件路径>")
        print("  python excel_process.py <你的Excel文件路径> <Sheet名称或索引>")
        sys.exit(1) # 使用非零状态码退出，表示程序异常终止。

    # 获取用户输入的Excel文件路径。
    input_excel_path = sys.argv[1]

    # 确定要读取的Sheet。
    # 默认读取第一个工作表（索引为0）。
    sheet_to_read = 0
    sheet_display_name = "第一个工作表 (索引 0)" # 用于打印输出的友好名称

    if len(sys.argv) > 2:
        # 如果用户提供了第三个参数，尝试将其作为Sheet名或索引。
        sheet_arg = sys.argv[2]
        try:
            # 尝试将参数转换为整数，如果成功，则认为是Sheet索引。
            sheet_to_read = int(sheet_arg)
            sheet_display_name = f"索引 {sheet_to_read}"
        except ValueError:
            # 如果转换失败，则认为是Sheet名称。
            sheet_to_read = sheet_arg
            sheet_display_name = f"名称 '{sheet_to_read}'"
        
        if len(sys.argv) > 3:
            print("⚠️ 警告：检测到多余的命令行参数，将只使用前两个参数（文件路径和可选的Sheet名/索引）。")

    # 验证文件路径是否存在。
    if not os.path.exists(input_excel_path):
        print(f"❌ 错误：文件不存在 -> '{input_excel_path}'")
        sys.exit(1)

    # 验证路径是否确实是一个文件，而不是一个目录。
    if not os.path.isfile(input_excel_path):
        print(f"❌ 错误：提供的路径不是一个文件，而是一个目录 -> '{input_excel_path}'")
        sys.exit(1)
        
    return input_excel_path, sheet_to_read, sheet_display_name

def read_excel_data(file_path, sheet_name, sheet_display_name):
    """
    功能: 从指定的Excel文件和工作表中读取数据。
    参数:
        - file_path: Excel文件路径。
        - sheet_name: 要读取的工作表名称或索引。
        - sheet_display_name: 用于打印信息的友好名称。
    返回: 一个pandas DataFrame对象。
    """
    # pd.read_excel() 是一个函数，用于读取Excel文件。
    # 这行代码的执行结果是创建一个DataFrame对象，你可以把它想象成内存中的一个Excel表格。
    try: 
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        print(f"✅ 成功读取文件：'{file_path}' 中的 {sheet_display_name} 工作表。")
        return df
    except ValueError as ve:
        # 捕获当指定的sheet_name不存在时可能抛出的ValueError。
        print(f"❌ 错误：在文件 '{file_path}' 中未找到指定的 {sheet_display_name} 工作表。")
        print(f"请检查Sheet名称或索引是否正确。详细错误：{ve}")
        sys.exit(1)
    except FileNotFoundError:
        # 尽管前面已经检查过文件是否存在，但为了健壮性，这里再次捕获。
        print(f"❌ 错误：无法找到文件 '{file_path}'。")
        sys.exit(1)
    except Exception as e:
        # 捕获其他可能的读取错误，例如文件损坏、格式不正确等。
        print(f"❌ 错误：读取Excel文件 '{file_path}' 时发生问题：{e}")
        sys.exit(1)

def process_duplicate_rows(df):
    """
    功能: 实现核心业务逻辑——根据"新增记录"列的值复制行。
    参数:
        - df: 原始的DataFrame。
    返回: 一个处理过（复制了行）的新DataFrame。
    """
    # 创建一个空的Python列表，命名为processed_rows。
    # 我们将用这个列表来收集所有的行，包括原始行和需要复制的新行。
    processed_rows = []

    # df.iterrows() 是一个非常有用的方法，它会逐行遍历DataFrame (df)。
    # 在每一次循环中，它会返回两个值：
    # - index: 当前行的行标签（或行号），默认从0开始。
    # - row: 一个包含当前行所有数据的Series对象。你可以通过列名从row中获取单元格的值。
    for index, row in df.iterrows():
        # 无论如何，我们都希望保留原始的每一行数据，所以先把当前行(row)添加到我们的结果列表(processed_rows)中。
        processed_rows.append(row)
        
        # --- 核心逻辑：根据"新增记录"列的值来复制行 ---
        # row.get('新增记录', 0) 从当前行(row)中获取'新增记录'这一列的值。
        # 使用 .get() 方法的好处是，如果'新增记录'这一列不存在，或者该单元格为空，它会返回一个默认值0，而不是报错。
        add_num = row.get('新增记录', 0)

        # pd.notnull(add_num) 用来检查我们获取到的值是否是有效值（不是空值NaN）。
        if pd.notnull(add_num):
            try:
                # 尝试将获取到的值转换为整数。如果这一格里是文本（比如"abc"），转换会失败，并触发except。
                add_num = int(add_num)
                # 只有当需要新增的记录数大于0时，才执行复制操作。
                if add_num > 0:
                    # 使用 for 循环来精确地复制指定的次数。
                    # 比如，如果 add_num 是 2，这个循环就会执行 2 次。
                    for _ in range(add_num):
                        # 在循环中，把当前行(row)再次添加到结果列表中。
                        processed_rows.append(row)
            except (ValueError, TypeError):
                # 如果int()转换失败（例如，值是文本或无法转换的格式），程序会跳转到这里。
                # pass 语句表示什么也不做，直接忽略这个错误，继续处理下一行。
                pass
    
    # 当所有行都处理完毕后，processed_rows列表里就包含了所有原始行和被复制的新行。
    # pd.DataFrame(processed_rows) 会使用这个列表来创建一个全新的DataFrame。
    # .reset_index(drop=True) 会为新的DataFrame生成一个干净的、从0开始的连续索引，并丢弃旧的索引。
    result_df = pd.DataFrame(processed_rows).reset_index(drop=True)
    return result_df

def save_dataframe_to_excel(df, original_input_path):
    """
    功能: 将最终的DataFrame保存到新的Excel文件中。
    - 根据原始输入路径自动生成输出文件名。
    参数:
        - df: 要保存的DataFrame。
        - original_input_path: 原始输入文件的路径，用于生成输出文件名。
    """
    # 获取输入文件的目录。
    input_dir = os.path.dirname(original_input_path)
    # 获取输入文件的基本名称（不包含目录）。
    input_filename = os.path.basename(original_input_path)
    # 分离文件名和扩展名。
    name, ext = os.path.splitext(input_filename)
    # 构造新的输出文件名，例如 '原始文件名_processed.xlsx'。
    output_filename = f"{name}_processed{ext}"
    # 组合目录和新的文件名，形成完整的输出文件路径。
    output_excel_path = os.path.join(input_dir, output_filename)

    # 将最终处理好的DataFrame (df) 保存到一个新的Excel文件中。
    # index=False 参数告诉pandas在保存时，不要把DataFrame的行索引（0, 1, 2...）也写到Excel文件里，这通常是我们想要的结果。
    df.to_excel(output_excel_path, index=False)

    print(f"🎉 处理完成！结果已保存到：'{output_excel_path}'")

def main():
    """
    主函数，程序的总入口和调度中心。
    """
    # 1. 解析命令行参数
    input_path, sheet, sheet_name_for_print = parse_arguments()
    
    # 2. 读取Excel数据
    original_df = read_excel_data(input_path, sheet, sheet_name_for_print)
    
    # 3. 执行核心处理逻辑
    processed_df = process_duplicate_rows(original_df)
    
    # 4. 保存处理结果
    save_dataframe_to_excel(processed_df, input_path)

if __name__ == "__main__":
    main()