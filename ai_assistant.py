"""
脚本名称: AI 助手 (ai_assistant.py)

功能描述:
    这是一个多功能的 AI 聊天机器人，支持命令行界面 (CLI) 和图形用户界面 (Web UI)。
    它通过阿里云的通义千问模型提供智能对话服务，并支持流式响应以实现实时交互。
    CLI 模式下具有对话历史持久化功能，Web UI 模式则提供更友好的可视化交互。
    此外，CLI 模式还支持将外部文件内容注入到对话上下文中，以便 AI 进行更深入的分析和讨论。

使用方法:
    1.  **CLI 模式 (默认)**:
        在终端中运行: `python ai_assistant.py`
        -   输入问题与 AI 对话。
        -   输入 "quit", "exit", "bye", "goodbye" 之一可保存对话历史并退出。

    2.  **CLI 模式 (带文件注入)**:
        在终端中运行: `python ai_assistant.py <文件路径>`
        -   例如: `python ai_assistant.py d:/Documents/Assistant/my_document.txt`
        -   AI 会先阅读文件内容，然后等待你的提问。

    3.  **Web UI 模式**:
        在终端中运行: `python ai_assistant.py --gui`
        -   这会启动一个基于 Gradio 的 Web 界面，你可以在浏览器中与 AI 交互。

配置:
    -   **API 密钥**: 必须在项目根目录的 `.env` 文件中设置 `ALIYUN_API_KEY` 环境变量。
        例如: `ALIYUN_API_KEY="your_api_key_here"`
    -   **代理**: 如果需要，可以在 `PROXY_URL` 变量中配置代理服务器地址。
    -   **历史记录**: CLI 模式下的对话历史保存在 `data/chat_log.json` 文件中。

依赖:
    -   `requests`
    -   `gradio`
    -   `python-dotenv`
    -   `json`
    -   `os`
    -   `sys`

注意事项:
    -   Web UI 模式下的对话历史不会被持久化保存。
    -   确保已安装所有依赖库 (`pip install -r requirements.txt`)。
"""
import os
import requests
import json
import sys
import gradio as gr
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

# --- 2. AI 服务类 ---
class AIAssistantService:
    """
    封装与 AI 模型交互的所有逻辑，包括 API 请求、流式响应处理和错误管理。
    """
    # --- 2.1. 初始化服务 ---
    def __init__(self, api_key, model_name, api_url, temperature, proxy_url=None):
        """
        初始化 AI 服务实例。

        :param api_key: 用于 API 认证的密钥。
        :param model_name: 要使用的 AI 模型名称。
        :param api_url: API 的终端节点 URL。
        :param temperature: 控制生成文本的随机性。
        :param proxy_url: (可选) 用于网络请求的代理服务器地址。
        """
        self.api_key = api_key
        self.model_name = model_name
        self.api_url = api_url
        self.temperature = temperature
        self.proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

    # --- 2.2. 获取流式回复 ---
    def stream_chat_completion(self, history):
        """
        接收一个完整的对话历史列表，以生成器的方式流式返回 AI 的回答。

        :param history: 一个包含对话消息的列表。
        :return: 一个生成器，逐块(chunk)产生 AI 的回复内容。
        """
        data = {
            "model": self.model_name,
            "messages": history,
            "temperature": self.temperature,
            "stream": True,
        }

        try:
            response = requests.post(self.api_url, headers=self.headers, json=data, proxies=self.proxies, stream=True)
            response.raise_for_status()

            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith("data:"):
                        json_str = decoded_line[len("data: "):]
                        if json_str.strip() == "[DONE]":
                            break
                        response_json = json.loads(json_str)
                        content = response_json["choices"][0]["delta"].get("content", "")
                        yield content
        except requests.exceptions.RequestException as e:
            yield f"\n哎呀，网络错误！无法连接到服务器。错误详情：{e}"
        except Exception as e:
            error_details = response.text if 'response' in locals() else "无响应内容"
            yield f"发生未知错误：{e}\n服务器响应：{error_details}"

# --- 3. 命令行界面 (CLI) 启动逻辑 ---
def start_cli():
    """启动命令行版本的 AI 助手。"""
    print("🚀 正在启动命令行 AI 助手...")

    # --- 新增：初始化 AI 服务 ---
    ai_service = AIAssistantService(
        api_key=API_KEY,
        model_name=MODEL_NAME,
        api_url=API_URL,
        temperature=TEMPERARURE,
        proxy_url=PROXY_URL
    )

    # 尝试从文件加载历史记录
    try:
        # 使用 with open() 语句确保文件在操作后能被正确关闭
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            conversation_history = json.load(f)
        print("AI小助手：已成功加载过往记忆。")
    except FileNotFoundError:
        # 如果文件不存在，说明是第一次运行，就创建一个空的列表
        conversation_history = []
        print("AI小助手：你好！一个新的旅程开始了。")

    # 检查命令行参数，sys.argv 是一个包含命令行参数的列表
    # sys.argv[0] 是脚本名，sys.argv[1] 是第一个参数，以此类推
    # 我们检查列表长度是否大于1，来判断用户是否提供了额外的参数（比如文件名）
    if len(sys.argv) > 1:
        try:
            file_path = sys.argv[1]
            # 同样使用 with open() 安全地读取文件内容
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

            # 注入后，立即让AI进行一次“确认性回复”，并将回复也存入历史
            print(f"AI助手：", end="")
            ai_response_content = ""
            # --- 修改：调用 AI 服务实例的方法 ---
            for chunk in ai_service.stream_chat_completion(conversation_history):
                ai_response_content += chunk
                print(chunk, end="", flush=True)
            print() # 换行

            # 将AI的确认回复也添加到历史记录中，以便后续对话能理解这个上下文
            conversation_history.append({"role": "assistant", "content": ai_response_content})

        except FileNotFoundError:
            print(f"错误：找不到文件 {sys.argv[1]}。请检查路径是否正确。")
            exit()
        except Exception as e:
            print(f"处理文件时发生错误：{e}")
            exit()

    print("="*30)

    # 使用 while True 创建一个无限循环，持续接收用户输入
    while True:
        # 使用 input() 来获取你在终端输入的问题
        user_input = input("你：")

        # 设置退出条件：当用户输入特定词汇时，保存历史并退出循环
        # .lower() 将输入转为小写，使得判断不区分大小写
        if user_input.lower() in ["quit", "exit","bye","goodbye","q","e"]:
            try:
                with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
                    # json.dump 用于将Python对象序列化为JSON格式并写入文件
                    # ensure_ascii=False 确保中文字符能被正确写入，而不是被转义
                    # indent=2 使JSON文件格式化，带2个空格的缩进，更易读
                    json.dump(conversation_history, f, ensure_ascii=False, indent=2)
                print("AI小助手：记忆已保存，期待下次与你相见！")
            except Exception as e:
                print(f"AI小助手：哎呀，保存记忆时出错了：{e}")
            break

        # 将用户的输入存入“记忆”
        conversation_history.append({"role": "user", "content": user_input})

        # 调用生成器函数，并迭代打印结果
        print(f"AI助手：", end="")
        full_response = ""
        has_error = False
        # --- 修改：调用 AI 服务实例的方法 ---
        for chunk in ai_service.stream_chat_completion(conversation_history):
            # 检查返回的片段中是否包含错误信息
            if "网络错误" in chunk or "未知错误" in chunk:
                has_error = True
            full_response += chunk
            # flush=True 强制刷新输出缓冲区，确保内容能被立即显示
            print(chunk, end="", flush=True)
        print() # 结束时换行

        # 将AI的回答也存入“记忆”，形成完整的上下文
        # (确保不会把错误信息也记下来)
        if not has_error:
            conversation_history.append({"role": "assistant", "content": full_response})
        
        print("-"*30) #打印分隔线

# --- 4. 图形用户界面 (GUI) 启动逻辑 ---
def start_gui():
    """启动 Gradio 图形用户界面。"""
    print("🚀 正在启动 Gradio 图形界面...")

    # --- 新增：初始化 AI 服务 ---
    ai_service = AIAssistantService(
        api_key=API_KEY,
        model_name=MODEL_NAME,
        api_url=API_URL,
        temperature=TEMPERARURE,
        proxy_url=PROXY_URL
    )

    # --- 为 Gradio UI 编写的接口函数 ---
    def chat_response(user_input, chatbot_history, conversation_state):
        """处理用户输入，并流式返回AI响应"""
        # 将用户输入添加到对话历史状态
        conversation_state.append({"role": "user", "content": user_input})
        # 更新Chatbot UI以立即显示用户输入
        chatbot_history.append([user_input, ""])
        # yield 关键字使这个函数成为一个生成器，可以逐步返回UI更新
        yield chatbot_history, conversation_state

        # 流式获取AI回复
        full_response = ""
        has_error = False
        # --- 修改：调用 AI 服务实例的方法 ---
        for chunk in ai_service.stream_chat_completion(conversation_state):
            if "网络错误" in chunk or "未知错误" in chunk:
                has_error = True
            full_response += chunk
            chatbot_history[-1][1] = full_response # 更新聊天机器人界面中最后一条消息的AI回复部分
            yield chatbot_history, conversation_state

        # 如果没有错误，将完整的AI回复添加到对话历史状态
        # 注意：Gradio版本中，历史记录是临时的，只在当前会话中有效，关闭即丢失
        if not has_error:
            conversation_state.append({"role": "assistant", "content": full_response})

    # --- 构建 Gradio 界面 ---
    with gr.Blocks(title="AI 助手") as app:
        # gr.State 用于在后端存储会话期间的完整对话历史（包含system role等）
        # 它在前端是不可见的
        conversation_state = gr.State(value=[])

        gr.Markdown("# 🤖 AI 助手")
        gr.Markdown("一个由阿里通义千问驱动的智能助手。")

        # 主要聊天界面
        chatbot = gr.Chatbot(label="通义千问", height=500)
        
        with gr.Row():
            txt_input = gr.Textbox(show_label=False, lines=3, placeholder="询问任何问题", scale=8)
            btn_submit = gr.Button("发送", variant="primary", scale=1)

        # --- 绑定事件 ---
        # 将提交动作（按回车或点击按钮）绑定到 chat_response 函数
        txt_input.submit(chat_response, [txt_input, chatbot, conversation_state], [chatbot, conversation_state]).then(lambda: "", [], [txt_input])
        btn_submit.click(chat_response, [txt_input, chatbot, conversation_state], [chatbot, conversation_state]).then(lambda: "", [], [txt_input])

    # 启动Gradio应用
    app.launch()

# --- 5. 主程序执行入口 ---
# 下面的代码只有在直接运行 `python ai_assistant.py` 时才会执行
if __name__ == "__main__":
    # 检查命令行参数，如果第二个参数是 '--gui'，则启动GUI模式
    if len(sys.argv) > 1 and sys.argv[1] == '--gui':
        start_gui()
    else:
        # 否则，启动默认的命令行模式
        # 注意：在CLI模式下，除了 '--gui' 之外的其他参数会被当作文件路径处理
        start_cli()
