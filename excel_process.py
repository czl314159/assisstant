import pandas as pd # 导入pandas库以处理Excel数据
# pandas的作用是提供高效的数据结构和数据分析工具,可处理多种格式的数据文件，包括Excel、CSV、SQL等  

# 读取Excel文件，生成DataFrame对象
df = pd.read_excel('工作簿1.xlsx', sheet_name='Sheet1')

# 创建一个新容器存放所有记录
processed_rows = [] #空列表

# 遍历每一行数据
for index, row in df.iterrows(): #iterrows() 方法用于逐行遍历 DataFrame 对象，返回每行的索引和数据
    # 始终保留原有记录
    processed_rows.append(row)
    
    # 检查"新增记录"字段是否为有效正整数
    add_num = row.get('新增记录', 0)
    if pd.notnull(add_num):
        try:
            add_num = int(add_num)
            if add_num > 0:
                # 复制指定的次数
                for _ in range(add_num):
                    processed_rows.append(row)
        except:
            pass  # 非数字值或转换失败则忽略

# 构建新的DataFrame
result_df = pd.DataFrame(processed_rows).reset_index(drop=True)

# 另存为新文件
result_df.to_excel('处理后的工作簿.xlsx', index=False)