import os
import requests
import json
import sys
from dotenv import load_dotenv

load_dotenv() # 在所有代码之前，运行这个函数，它会自动加载.env文件

# --- 1. 配置程序所需的变量 ---

# 提示：为了安全，最好将API密钥存储在环境变量中.如果环境变量不存在，打印错误信息并退出。
API_KEY = os.getenv("ALIYUN_API_KEY") 
if not API_KEY: 
    print("错误：未找到ALIYUN_API_KEY环境变量！") 
    print("请在.env文件中设置您的API密钥") 
    exit(1) 

# 如果无法直接访问API，可以在这里设置代理服务器地址
PROXY_URL = None 
MODEL_NAME = "qwen-flash"
API_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions" 
HISTORY_FILE = "data/chat_log.json" # 历史记录文件路径
TEMPERARURE = 0.5

data_folder = os.path.dirname(HISTORY_FILE) # 如果 data 文件夹不存在，就自动创建它
if data_folder and not os.path.exists(data_folder):
    os.makedirs(data_folder)

# --- 2. 将AI调用逻辑封装成一个函数 ---
def get_ai_reply(history):
    """
    接收一个完整的对话历史列表，返回AI的回答。
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    data = {
        "model": MODEL_NAME,
        "messages": history,
        "temperature": TEMPERARURE,
    }

    proxies = {
    "http": PROXY_URL,
    "https": PROXY_URL,
    } if PROXY_URL else None

    try:
        response = requests.post(API_URL, headers=headers, json=data, proxies=proxies) 
        # 发送请求，获取响应
        response.raise_for_status()  # 如果请求失败(如4xx或5xx错误)，这里会抛出异常
        response_json = response.json() # 解析响应，获取AI的回答
        assistant_reply = response_json["choices"][0]["message"]["content"] 
        # 获取AI的回答
        return assistant_reply
    except requests.exceptions.RequestException as e:
        return  f"\n哎呀，网络错误！无法连接到服务器。错误详情：{e}"
    except Exception as e:
        # 打印更详细的错误信息，包括返回的内容，方便调试
        error_details = response.text if 'response' in locals() else "无响应内容"
        return f"发生未知错误：{e}\n服务器响应：{error_details}"



# --- 3. 主程序：实现永久记忆、循环对话和文件读取 ---
#首先尝试从文件加载历史记录
try:
    with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
        conversation_history = json.load(f)
    print("AI小助手：已成功加载过往记忆。")
except FileNotFoundError:
    # 如果文件不存在，说明是第一次运行，就创建一个空的列表
    conversation_history = []
    print("AI小助手：你好！一个新的旅程开始了。")

#第二步：检查是否需要“注入”新文件作为上下文
if len(sys.argv) > 1:
    try:
        file_path = sys.argv[1]
        with open(file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()

# 【核心】构建注入的提示，并将其追加到现有历史的末尾
        injection_prompt = f"""
好的，我现在为你提供一份新的文件内容。请你阅读并理解它，接下来可能会用到它。
---
文件路径: {os.path.basename(file_path)}
文件内容如下：
{file_content}
---
如果你已经阅读并理解了以上内容，请回复：“好的，新文件已阅读完毕，我们可以开始讨论了。”
"""
        
        conversation_history.append({"role": "user", "content": injection_prompt})
        print(f"AI小助手：正在注入新文件: {os.path.basename(file_path)} ...")

        # 【关键】注入后，立即让AI进行一次“确认性回复”，并将回复也存入历史
        ai_response = get_ai_reply(conversation_history)
        conversation_history.append({"role": "assistant", "content": ai_response})
        print(f"AI助手：{ai_response}")

    except FileNotFoundError:
        print(f"错误：找不到文件 {sys.argv[1]}。请检查路径是否正确。")
        exit()
    except Exception as e:
        print(f"处理文件时发生错误：{e}")
        exit()

print("="*30)

# 使用 while True 创建一个无限循环
while True:
    # 使用 input() 来获取你在终端输入的问题
    user_input = input("你：")

    # 设置退出条件
    if user_input.lower() in ["quit", "exit","bye","goodbye"]:
        try:
            with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(conversation_history, f, ensure_ascii=False, indent=2)
            print("AI小助手：记忆已保存，期待下次与你相见！")
        except Exception as e:
            print(f"AI小助手：哎呀，保存记忆时出错了：{e}")
        break

    # 将用户的输入存入“记忆”
    conversation_history.append({"role": "user", "content": user_input})

    # 2. 调用函数，把全部“记忆”都发给AI
    ai_response = get_ai_reply(conversation_history)

    # 3. 将AI的回答也存入“记忆”，形成完整的上下文
    # (我们加一个判断，确保不会把错误信息也记下来)
    if "请求失败" not in ai_response and "未知错误" not in ai_response:
        conversation_history.append({"role": "assistant", "content": ai_response})
    
    # 4. 打印AI的回答
    print(f"AI助手：{ai_response}") 
    print("-"*30) #打印分隔线

