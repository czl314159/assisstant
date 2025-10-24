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
import re # 导入 re 模块用于正则表达式操作
import argparse
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

# 定义总结提炼的标记，与 html_to_md.py 中的 SUMMARY_TEMPLATE 保持一致
SUMMARY_HEADING_MARKER = "# 总结提炼\n\n" # 标题标记，后面跟两个换行符
SUMMARY_SEPARATOR_MARKER = "\n---" # 分隔符标记，前面跟一个换行符
# 编译正则表达式，用于查找 SUMMARY_HEADING_MARKER 作为插入点。re.DOTALL 允许 '.' 匹配换行符。
SUMMARY_PATTERN = re.compile(rf"({re.escape(SUMMARY_HEADING_MARKER)})", re.DOTALL)
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

# --- 3. 核心功能封装 ---

def load_history(file_path):
    """
    从指定路径加载对话历史。
    :param file_path: 历史记录文件的路径。
    :return: 一个包含对话历史的列表。如果文件不存在，则返回空列表。
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            history = json.load(f)
        print("AI小助手：已成功加载过往记忆。")
        return history
    except FileNotFoundError:
        print("AI小助手：你好！一个新的旅程开始了。")
        return []

def save_history(history, file_path):
    """
    将对话历史保存到指定路径。
    :param history: 要保存的对话历史列表。
    :param file_path: 历史记录文件的路径。
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        print("AI小助手：记忆已保存，期待下次与你相见！")
    except Exception as e:
        print(f"AI小助手：哎呀，保存记忆时出错了：{e}")

# --- 批处理文件夹总结功能 ---
def process_folder_for_summaries(folder_path, ai_service, prompt_template):
    """
    遍历指定文件夹下的所有Markdown/文本文件，查找总结提炼区域，
    如果该区域为空，则调用AI进行总结并写入文件。
    如果该区域已有内容，则将新总结写入一个新文件。
    :param folder_path: 要处理的文件夹路径。
    :param ai_service: AI 服务实例。
    :param prompt_template: 用于生成AI请求的提示词模板。
    """
    print(f"📁 检测到文件夹输入：'{folder_path}'。将进入批处理模式，自动总结文件。")
    processed_count = 0 # 统计成功处理（原地更新）的文件数量
    skipped_count = 0
    error_count = 0

    if "{content}" not in prompt_template:
        print("⚠️ 警告：提供的提示词模板中未找到 '{content}' 占位符。AI可能无法获取文件内容。")

    for root, _, files in os.walk(folder_path):
        for file_name in files:
            # 只处理 Markdown 和文本文件
            if not file_name.lower().endswith(('.md')):
                continue

            file_path = os.path.join(root, file_name)
            print(f"\n--- 正在处理文件: {file_name} ---")

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 使用正则表达式查找总结提炼区域
                match = SUMMARY_PATTERN.search(content)

                if not match: # 如果连标题标记都找不到，就跳过
                    print(f"   ⏭️ 跳过 '{file_name}'：未找到总结提炼的标题标记 ('{SUMMARY_HEADING_MARKER.strip()}')。")
                    skipped_count += 1
                    continue

                # 准备发送给 AI 的提示词
                summary_prompt = prompt_template.format(content=content) # 将文件内容填充到提示词模板中
                # 为 AI 调用创建一个临时的对话历史，因为总结不需要之前的上下文
                temp_history = [{"role": "user", "content": summary_prompt}]
                
                print("   🤖 正在请求 AI 生成内容...")
                ai_summary = ""
                for chunk in ai_service.stream_chat_completion(temp_history):
                    ai_summary += chunk
                    # 可以在这里打印 chunk 以提供实时反馈，但批处理模式下通常不需要
                    # print(chunk, end="", flush=True)

                if not ai_summary.strip():
                    print(f"   ⏭️ AI 未返回有效内容，跳过 '{file_name}'。请检查提示词或文件内容。")
                    skipped_count += 1
                    continue

                # 简化逻辑：直接在 SUMMARY_HEADING_MARKER 之后插入 AI 总结
                # r"\1" 是正则表达式匹配到的 SUMMARY_HEADING_MARKER 本身
                # ai_summary.strip() 是 AI 生成的总结内容
                # "\n\n" 是为了在插入的总结和原有内容之间保持两行空行，以符合Markdown格式和可读性
                new_content = SUMMARY_PATTERN.sub(r"\1" + ai_summary.strip() + "\n\n", content, 1)

                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"   ✅ 成功插入内容并更新文件: '{file_name}'")
                processed_count += 1
                    
            except Exception as e:
                print(f"   ❌ 处理文件 '{file_name}' 时发生错误: {e}")
                error_count += 1
                continue
    
    print("\n--- 批处理完成 ---")
    total_files = processed_count + skipped_count + error_count
    print(f"总计扫描文件: {total_files}")
    print(f"成功插入内容并更新: {processed_count}")
    print(f"跳过 (无标记区域): {skipped_count}")
    print(f"处理失败: {error_count}")
    print("------------------")
    
# --- 4. 命令行界面 (CLI) 启动逻辑 ---
def start_cli():
    """启动命令行版本的 AI 助手。"""
    # --- 1. 使用 argparse 解析命令行参数 ---
    parser = argparse.ArgumentParser(
        description="一个支持多种记忆模式和文件注入的命令行 AI 助手。",
        # formatter_class 可以让帮助信息更好地显示默认值
        formatter_class=argparse.ArgumentDefaultsHelpFormatter 
    )
    parser.add_argument(
        'memory_mode',
        nargs='?', # '?' 表示 0 或 1 个参数，使其成为可选的位置参数
        choices=['no', 'short', 'long'],
        default='short',
        help="设置记忆模式: 'no' (无记忆), 'short' (短期会话记忆), 'long' (长期持久化记忆)。"
    )
    parser.add_argument(
        '-f', '--file',
        dest='file_path', # 解析后的参数名
        default=None,
        help="指定要加载到上下文中的文件路径。"
    )
    # 创建一个互斥组，确保 --prompt 和 --prompt-file 不会同时使用
    prompt_group = parser.add_mutually_exclusive_group()
    prompt_group.add_argument(
        '--prompt',
        dest='prompt_string',
        help="直接在命令行中提供提示词模板。请使用 '{content}' 作为文件内容的占位符。"
    )
    prompt_group.add_argument(
        '--prompt-file',
        dest='prompt_file_path',
        help="从指定文件中加载提示词模板。文件中应包含 '{content}' 占位符。"
    )
    # 从 sys.argv 中过滤掉脚本名和 '--gui' 标志，只解析与CLI相关的参数
    cli_args = [arg for arg in sys.argv[1:] if arg != '--gui']
    args = parser.parse_args(cli_args)

    print("🚀 正在启动命令行 AI 助手...")
    print(f"🧠 记忆模式: {args.memory_mode}")

    # --- 2. 初始化服务和会话状态 ---
    ai_service = AIAssistantService(
        api_key=API_KEY,
        model_name=MODEL_NAME,
        api_url=API_URL,
        temperature=TEMPERARURE,
        proxy_url=PROXY_URL
    )

    # 根据记忆模式初始化对话历史
    if args.memory_mode == 'long':
        conversation_history = load_history(HISTORY_FILE)
    else:
        conversation_history = []
        print("AI小助手：你好！一个新的旅程开始了。")

    file_context = None
    if args.file_path:
        if os.path.isdir(args.file_path):
            # --- 批处理模式的提示词处理 ---
            prompt_template = ""
            if args.prompt_string:
                prompt_template = args.prompt_string
            elif args.prompt_file_path:
                try:
                    with open(args.prompt_file_path, 'r', encoding='utf-8') as f:
                        prompt_template = f.read()
                except Exception as e:
                    print(f"❌ 读取提示词文件 '{args.prompt_file_path}' 时出错: {e}")
                    sys.exit(1)
            else:
                # 如果用户未提供提示词，则进入交互式输入
                print("\n批处理模式需要一个提示词模板。")
                print("模板中必须包含 '{content}' 占位符，它将被替换为每个文件的实际内容。")
                default_prompt = "请你仔细阅读以下文本，并提炼出主要内容和关键信息，生成一份简洁的总结。请直接输出总结内容，不要包含任何额外的前缀或后缀。\n\n文本内容:\n```\n{content}\n```"
                print(f"\n示例 (默认模板):\n---\n{default_prompt}\n---")
                
                user_prompt = input("\n请输入你的提示词模板 (直接按 Enter 使用默认模板): \n")
                if user_prompt.strip():
                    prompt_template = user_prompt
                else:
                    prompt_template = default_prompt
            
            process_folder_for_summaries(args.file_path, ai_service, prompt_template)
            sys.exit(0) # 批处理完成后退出程序
        elif os.path.isfile(args.file_path):
            # 如果是文件，加载文件内容作为对话上下文
            try:
                with open(args.file_path, 'r', encoding='utf-8') as f:
                    file_context = f.read()
                print(f"📎 已加载文件 '{os.path.basename(args.file_path)}'。现在您可以基于该文件提问了。")
            except FileNotFoundError:
                print(f"❌ 错误：找不到文件 {args.file_path}。请检查路径是否正确。")
                sys.exit(1)
            except Exception as e:
                print(f"❌ 处理文件时发生错误：{e}")
                sys.exit(1)
        else:
            print(f"❌ 错误：'{args.file_path}' 既不是文件也不是文件夹。请提供有效路径。")
            sys.exit(1)

    # 使用 while True 创建一个无限循环，持续接收用户输入
    while True:
        # 使用 input() 来获取你在终端输入的问题
        user_input = input("你：")

        # 设置退出条件：当用户输入特定词汇时，保存历史并退出循环
        # .lower() 将输入转为小写，使得判断不区分大小写
        if user_input.lower() in ["quit", "exit","bye","goodbye","q","e"]:
            # 仅在长期记忆模式下保存历史
            if args.memory_mode == 'long':
                save_history(conversation_history, HISTORY_FILE)
            print("AI小助手：期待下次与你相见！")
            break

        # --- 核心修改：动态构建用户输入 ---
        # 如果存在文件上下文，则将其与用户当前问题组合
        if file_context:
            # 构建一个包含文件上下文和用户问题的复合提示
            final_input = f"""请基于以下文档内容来回答我的问题。
---
文档内容:
{file_context}
---
我的问题是：{user_input}
"""
        else:
            # 如果没有文件上下文，则直接使用用户输入
            final_input = user_input

        # 无论何种模式，都将用户的输入存入完整的历史记录，以备将来保存
        conversation_history.append({"role": "user", "content": final_input})

        # --- 3. 根据记忆模式决定发送给 AI 的内容 ---
        if args.memory_mode == 'no':
            # 无记忆模式：只发送包含当前这一次输入的新列表
            history_to_send = [conversation_history[-1]]
        else: # 'short' 和 'long' 模式都使用短期记忆
            # 短期/长期记忆模式：发送包含所有历史记录的完整列表
            history_to_send = conversation_history

        # 调用生成器函数，并迭代打印结果
        print(f"AI助手：", end="")
        full_response = ""
        has_error = False
        # 调用 AI 服务实例的方法
        for chunk in ai_service.stream_chat_completion(history_to_send):
            # 检查返回的片段中是否包含错误信息
            if "网络错误" in chunk or "未知错误" in chunk:
                has_error = True
            full_response += chunk
            # flush=True 强制刷新输出缓冲区，确保内容能被立即显示
            print(chunk, end="", flush=True)
        print() # 结束时换行

        # 无论何种模式，都将AI的回答也存入完整的历史记录
        # (确保不会把错误信息也记下来), 以备将来保存
        if not has_error:
            conversation_history.append({"role": "assistant", "content": full_response})
        
        print("\n" + "-"*30) #打印分隔线，并在前面加一个换行以改善间距

# --- 5. 图形用户界面 (GUI) 启动逻辑 ---
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
        # 调用 AI 服务实例的方法
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

# --- 6. 主程序执行入口 ---
# 下面的代码只有在直接运行 `python ai_assistant.py` 时才会执行
if __name__ == "__main__":
    # 优先检查是否要启动 GUI 模式
    if '--gui' in sys.argv:
        start_gui()
    else:
        # 否则，启动默认的命令行模式
        # start_cli 函数内部会使用 argparse 处理所有相关的命令行参数
        start_cli()
