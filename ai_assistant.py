"""
脚本名称: AI 助手 (ai_assistant.py)

功能描述:
    这是一个多功能的 AI 聊天机器人，支持命令行界面 (CLI) 和图形用户界面 (Web UI)。
    它通过阿里云的通义千问模型提供智能对话服务，并支持流式响应以实现实时交互。
    CLI 模式下具有对话历史持久化功能，Web UI 模式则提供更友好的可视化交互。
    此外，CLI 模式还支持将外部文件内容注入到对话上下文中，以便 AI 进行更深入的分析和讨论。

    注意：原有的批量处理文件夹功能已被移至 `note_process/batch_summarize.py` 脚本。

使用方法:
    1.  **CLI 模式 (默认短期记忆)**:
        在终端中运行: `python ai_assistant.py`
        -   直接输入问题与 AI 对话。
        -   输入 "quit", "exit", "bye", "goodbye" 之一即可退出。

    2.  **CLI 模式 (选择记忆策略 / 会话)**:
        -   长期记忆: `python ai_assistant.py --mode long`
        -   禁用记忆: `python ai_assistant.py --mode no`
        -   指定会话: `python ai_assistant.py --mode long --session 工作`
            (不同会话的历史会分别保存在独立文件中)

    3.  **CLI 模式 (带文件注入)**:
        在终端中运行: `python ai_assistant.py <文件路径> [其它参数]`
        -   例如: `python ai_assistant.py notes/summary.md --mode long`
        -   AI 会先阅读文件内容，再等待你的提问。

    4.  **Web UI 模式**:
        在终端中运行: `python ai_assistant.py --gui`
        -   启动基于 Gradio 的 Web 界面，可在浏览器中与 AI 交互。

配置:
    -   **API 密钥**: 必须在项目根目录的 `.env` 文件中设置 `ALIYUN_API_KEY` 环境变量。
        例如: `ALIYUN_API_KEY="your_api_key_here"`
    -   **代理**: 如果需要，可以在 `PROXY_URL` 变量中配置代理服务器地址。
    -   **历史记录**: 长期记忆模式会将历史保存在 `data/sessions/` 目录下（可通过 `MEMORY_ROOT` 调整）。

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
import sys
import gradio as gr
import argparse
from dotenv import load_dotenv
# 从 note_process 文件夹下的 ai_service.py 文件中导入 AIAssistantService 类
from ai_service import AIAssistantService
from memory_store import MemoryStore

load_dotenv() # 在所有代码之前，运行这个函数，它会自动加载.env文件

# --- 1. 配置程序所需的变量 ---

# 提示：为了安全，最好将API密钥存储在环境变量中.如果环境变量不存在，打印错误信息并退出。
API_KEY = os.getenv("ALIYUN_API_KEY") 
if not API_KEY: 
    print("错误：未找到ALIYUN_API_KEY环境变量！") 
    print("请在.env文件中设置您的API密钥") 
    exit(1) 

API_URL = os.getenv("ALIYUN_API_URL")
if not API_URL:
    print("错误：未找到ALIYUN_API_URL环境变量！")
    print("请在.env文件中设置您的API地址")
    exit(1)

MODEL_NAME = os.getenv("ALIYUN_MODEL_NAME")
if not MODEL_NAME:
    print("警告：未找到ALIYUN_MODEL_NAME环境变量！")
    print("请在.env文件中设置您的模型名称")
    exit(1)

MEMORY_ROOT = os.getenv("MEMORY_ROOT", "data/sessions")
DEFAULT_SESSION_ID = "default"
TEMPERATURE = float(os.getenv("TEMPERATURE",0.5))

memory_store = MemoryStore(root_dir=MEMORY_ROOT)

# --- 3. 核心功能封装 ---

# --- 4. 命令行界面 (CLI) 启动逻辑 ---
def start_cli():
    """启动命令行版本的 AI 助手。"""
    # --- 1. 使用 argparse 解析命令行参数 ---
    parser = argparse.ArgumentParser(
        description="一个支持多种记忆模式和文件注入的命令行 AI 助手。",
        # formatter_class 可以让帮助信息更好地显示默认值
        formatter_class=argparse.ArgumentDefaultsHelpFormatter 
    )
    # 将文件路径作为可选的位置参数，允许用户直接在脚本名后提供
    parser.add_argument(
        'file_path',
        nargs='?', # '?' 表示 0 或 1 个参数，使其成为可选的位置参数
        default=None,
        help="指定要加载到上下文中的文件路径。如果提供，AI会先阅读文件内容。"
    )
    # 将记忆模式改为可选参数，使用 -m 或 --mode
    parser.add_argument(
        '-m', '--mode',
        dest='memory_mode', # 解析后的参数名
        choices=['no', 'short', 'long'], # 允许的值
        default='short', # 默认值
        help="设置记忆模式: 'no' (无记忆), 'short' (短期会话记忆), 'long' (长期持久化记忆)。"
    )
    parser.add_argument(
        '--session',
        dest='session_id',
        default=DEFAULT_SESSION_ID,
        help="指定会话名称，用于区分不同主题的长期记忆。"
    )
    args = parser.parse_args() # 直接解析所有参数
    session_id = args.session_id.strip() or DEFAULT_SESSION_ID

    print("🚀 正在启动命令行 AI 助手...")
    print(f"🧠 记忆模式: {args.memory_mode}")
    print(f"🗂 会话名称: {session_id}")

    # --- 2. 初始化服务和会话状态 ---
    ai_service = AIAssistantService(
        api_key=API_KEY,
        model_name=MODEL_NAME,
        api_url=API_URL,
        temperature=TEMPERATURE,
    )

    # 根据记忆模式初始化对话历史
    if args.memory_mode == 'long':
        conversation_history = memory_store.load(session_id)
        if conversation_history:
            print(f"🗄 已加载会话 '{session_id}' 的历史消息，共 {len(conversation_history)} 条。")
        else:
            print(f"🗄 会话 '{session_id}' 暂无历史，将从头开始。")
    else:
        conversation_history = []
        print("AI小助手：你好！一个新的旅程开始了。")

    file_context = None
    # 检查 file_path 是否被提供，并进行相应的处理
    if args.file_path:
        # 如果 file_path 是一个目录，提示用户使用批量总结脚本
        if os.path.isdir(args.file_path):
            print("📁 检测到文件夹输入。")
            print("此功能已移至新脚本 `note_process/batch_summarize.py`。")
            print("请使用以下命令运行批量总结功能:")
            print(f"   python note_process/batch_summarize.py \"{args.file_path}\"")
            sys.exit(0)
        # 如果 file_path 是一个文件，加载其内容
        elif os.path.isfile(args.file_path):
            try:
                with open(args.file_path, 'r', encoding='utf-8') as f:
                    file_context = f.read()
                print(f"📎 已加载文件 '{os.path.basename(args.file_path)}'。现在您可以基于该文件提问了。")
            except FileNotFoundError:
                print(f"❌ 错误：找不到文件 {args.file_path}。请检查路径是否正确。")
                sys.exit(1) # 文件未找到，程序退出
            except Exception as e:
                print(f"❌ 处理文件时发生错误：{e}")
                sys.exit(1) # 其他文件处理错误，程序退出
        # 如果 file_path 既不是文件也不是目录，则报错
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
                memory_store.save(session_id, conversation_history)
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
        temperature=TEMPERATURE,
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
