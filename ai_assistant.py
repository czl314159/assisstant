import os
import requests
import json
from dotenv import load_dotenv

# 在所有代码之前，运行这个函数，它会自动加载.env文件
load_dotenv()

# --- 1. 配置你的秘密钥匙和代理 ---
# 提示：为了安全，最好将API密钥存储在环境变量中。
API_KEY = os.getenv("ALIYUN_API_KEY")
# 如果你无法直接访问API，可以在这里设置你的代理服务器地址
# 如果你可以直接访问，请将下面这行保留为None
PROXY_URL = None 

# --- 2. 设定我们要联系的“魔法塔”地址 ---
# 阿里云 DeepSeek-V3.1 模型的API地址
API_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"

# --- 3. 将AI调用逻辑封装成一个函数 ---
# 这样做的好处是代码更清晰，可以重复使用
def get_ai_response(prompt):
    """调用阿里云 DeepSeek-V3.1 模型，获取AI回复"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    data = {
        "model": "deepseek-v3.1",
        "input": {
            "messages": [
                {
                    "role": "user",
                    "content": prompt # 这里使用函数传入的问题
                }
            ]
        }
    }

    proxies = {
    "http": PROXY_URL,
    "https": PROXY_URL,
    } if PROXY_URL else None

    try:
        response = requests.post(API_URL, headers=headers, json=data, proxies=proxies)
        # 检查回信的状态
        response.raise_for_status()  # 如果请求失败(如4xx或5xx错误)，这里会抛出异常
        response_json = response.json()
        assistant_reply = response_json()
        # 解析阿里云DeepSeek返回的格式
        assistant_reply = response_json["output"]["text"]
        return assistant_reply
    except requests.exceptions.RequestException as e:
        return  f"\n哎呀，网络错误！无法连接到服务器。错误详情：{e}"
    except Exception as e:
        # 打印更详细的错误信息，包括返回的内容，方便调试
        error_details = response.text if 'response' in locals() else "无响应内容"
        return f"发生未知错误：{e}\n服务器响应：{error_details}"

# --- 4. 主程序循环 ---
print("AI小助手已启动！输入 'quit' 或 'exit' 来结束对话。")
print("="*30)

# 使用 while True 创建一个无限循环
while True:
    # 使用 input() 来获取你在终端输入的问题
    user_input = input("你：")

    # 设置退出条件
    if user_input.lower() in ["quit", "exit","bye","goodbye"]:
        print("AI小助手：再见啦！")
        break # 跳出循环

    # 调用函数，获取AI的回答
    ai_response = get_ai_response(user_input)
    
    # 打印AI的回答
    print(f"AI助手：{ai_response}")
    print("-"*30)

