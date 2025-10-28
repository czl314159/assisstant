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
    -   Web UI 模式默认启用长期记忆，可通过界面切换不同会话。
    -   确保已安装所有依赖库 (`pip install -r requirements.txt`)。
"""
import os
import sys
import gradio as gr
import argparse
from dotenv import load_dotenv
# 项目自带的服务对象，负责与后端大模型交互
from ai_service import AIAssistantService
# 统一的会话记忆存储实现
from memory_store import MemoryStore

# 读取 .env 文件到环境变量中，让下面的 os.getenv 可以获取到配置
load_dotenv()

# --- 1. 配置程序所需的变量 ---

# 以下配置用于驱动模型调用，全部依赖环境变量。
# 这样做的好处是不需要把敏感信息写死在代码里。
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

# 实例化记忆存储，CLI 与 GUI 共用，保证会话切换行为一致
memory_store = MemoryStore(root_dir=MEMORY_ROOT)

def history_to_chatbot_pairs(history):
    """
    将完整的消息历史转换为 Chatbot 组件需要的 [user, assistant] 列表。

    history 参数使用的是 OpenAI 兼容格式：
    [
        {"role": "user", "content": "..."},
        {"role": "assistant", "content": "..."},
        ...
    ]
    而 Gradio Chatbot 组件需要 [[用户内容, 助手内容], ...] 的二维数组。
    """
    pairs = []
    for message in history:
        role = message.get("role")
        content = message.get("content", "")
        if role == "user":
            # 新开一轮对话，把用户输入放在左侧
            pairs.append([content, ""])
        elif role == "assistant":
            if pairs:
                # 将助手回复填充到上一条用户消息的右侧
                pairs[-1][1] = content
            else:
                # 某些极端情况下历史可能以 assistant 开头，这里兜底
                pairs.append(["", content])
        # 其他角色（如 system）在当前界面中忽略
    return pairs


def format_session_status(session_id, history):
    """
    生成当前会话的状态文本，用于 GUI 顶部提示。
    """
    total_messages = len(history)
    turns = sum(1 for msg in history if msg.get("role") == "assistant")
    return f"当前会话：{session_id} ｜ 轮次：{turns} ｜ 消息数：{total_messages}"


# --- 2. 命令行界面 (CLI) 启动逻辑 ---
def start_cli():
    """启动命令行版本的 AI 助手。"""
    # --- 1. 使用 argparse 解析命令行参数 ---
    # 初学者提示：argparse 会自动解析命令行输入、生成帮助文档，非常适合写 CLI 工具
    parser = argparse.ArgumentParser(
        description="一个支持多种记忆模式和文件注入的命令行 AI 助手。",
        # formatter_class 可以让帮助信息更好地显示默认值
        formatter_class=argparse.ArgumentDefaultsHelpFormatter 
    )
    # 将文件路径作为可选的位置参数，这样用户可以直接把文档拖入终端后回车
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
    # parse_args() 会根据上面的定义解析命令行参数
    args = parser.parse_args()
    # normalize_session_id 会移除不合法字符，确保文件名安全
    session_id = memory_store.normalize_session_id(args.session_id)

    print("🚀 正在启动命令行 AI 助手...")
    print(f"🧠 记忆模式: {args.memory_mode}")
    print(f"🗂 会话名称: {session_id}")

    # --- 2. 初始化服务和会话状态 ---
    # 这里只创建一次服务实例，避免每轮对话重复建立网络连接
    ai_service = AIAssistantService(
        api_key=API_KEY,
        model_name=MODEL_NAME,
        api_url=API_URL,
        temperature=TEMPERATURE,
    )

    # 根据记忆模式初始化对话历史
    # 长期记忆 => 从磁盘读取历史；短期/无记忆 => 直接从空上下文开始
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
    # 主循环：不断读取终端输入，直到用户手动退出
    while True:
        # 使用 input() 来获取你在终端输入的问题
        user_input = input("你：")

        # 设置退出条件：当用户输入特定关键词时，保存历史并退出循环
        # lower() 将输入转为小写，从而支持 Quit、QUIT 等不同写法
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
            # 这样模型会先阅读文件内容，再回答最新的问题
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

        # 无论何种模式，都将用户输入存入完整的历史记录，保持上下文同步
        conversation_history.append({"role": "user", "content": final_input})

        # --- 3. 根据记忆模式决定发送给 AI 的内容 ---
        if args.memory_mode == 'no':
            # 无记忆模式：只发送包含当前这一次输入的新列表
            history_to_send = [conversation_history[-1]]
        else: # 'short' 和 'long' 模式都使用短期记忆
            # 短期/长期记忆模式：发送包含所有历史记录的完整列表
            # 注意：对于 long 模式，这里与 conversation_history 是同一个列表
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
            if args.memory_mode == 'long':
                memory_store.save(session_id, conversation_history)
        
        print("\n" + "-"*30) #打印分隔线，并在前面加一个换行以改善间距

# --- 3. 图形用户界面 (GUI) 启动逻辑 ---
def start_gui():
    """启动 Gradio 图形用户界面。"""
    print("🚀 正在启动 Gradio 图形界面...")

    # --- 初始化 AI 服务 ---
    ai_service = AIAssistantService(
        api_key=API_KEY,
        model_name=MODEL_NAME,
        api_url=API_URL,
        temperature=TEMPERATURE,
    )

    # --- 准备默认会话 ---
    initial_session = memory_store.normalize_session_id(DEFAULT_SESSION_ID)
    initial_history = memory_store.load(initial_session)
    initial_pairs = history_to_chatbot_pairs(initial_history)
    initial_status = format_session_status(initial_session, initial_history)
    print(f"🗄 GUI 会话 '{initial_session}' 已加载 {len(initial_history)} 条消息。")

    # --- 为 Gradio UI 编写的接口函数 ---
    def chat_response(user_input, chatbot_history, conversation_state, session_id):
        """处理用户输入，并流式返回AI响应。"""
        session_id = memory_store.normalize_session_id(session_id)
        # 将用户输入追加到历史列表，保存为 {"role": "user", "content": "..."} 的格式
        conversation_state.append({"role": "user", "content": user_input})
        # 同步更新界面组件，让用户输入立即出现在聊天窗口里
        chatbot_history.append([user_input, ""])
        yield (
            chatbot_history,
            conversation_state,
            gr.update(value=format_session_status(session_id, conversation_state)),
        )

        # 流式获取AI回复：模型输出被拆成多次回调，能够模拟实时打印的效果
        full_response = ""
        has_error = False
        for chunk in ai_service.stream_chat_completion(conversation_state):
            if "网络错误" in chunk or "未知错误" in chunk:
                has_error = True
            full_response += chunk
            # 更新当前轮的“助手回答”部分，让用户看到实时生成的内容
            chatbot_history[-1][1] = full_response
            yield (
                chatbot_history,
                conversation_state,
                gr.update(value=format_session_status(session_id, conversation_state)),
            )

        if not has_error:
            # 将助手回复追加到历史中，并立即写入磁盘文件
            conversation_state.append({"role": "assistant", "content": full_response})
            memory_store.save(session_id, conversation_state)

        yield (
            chatbot_history,
            conversation_state,
            gr.update(value=format_session_status(session_id, conversation_state)),
        )

    def switch_session(requested_session, conversation_history, current_session_id):
        """
        切换到新的会话：保存当前历史后，加载目标会话并刷新界面。
        """
        current_session_id = memory_store.normalize_session_id(current_session_id)
        if conversation_history:
            # 离开旧会话前先保存，避免未提交的对话被覆盖
            memory_store.save(current_session_id, conversation_history)

        # 加载目标会话，如果还不存在则会返回空历史
        new_session = memory_store.normalize_session_id(requested_session)
        new_history = memory_store.load(new_session)
        print(f"🗄 已切换到会话 '{new_session}'，共 {len(new_history)} 条消息。")

        chatbot_pairs = history_to_chatbot_pairs(new_history)
        status_text = format_session_status(new_session, new_history)

        return (
            gr.update(value=new_session),
            gr.update(value=chatbot_pairs),
            new_history,
            new_session,
            gr.update(value=status_text),
        )

    # --- 构建 Gradio 界面 ---
    with gr.Blocks(title="AI 助手") as app:
        # gr.State 在服务器端保存状态，相当于“隐藏变量”，不会直接展示给用户
        conversation_state = gr.State(value=list(initial_history))
        session_state = gr.State(value=initial_session)

        gr.Markdown("# 🤖 AI 助手")
        gr.Markdown("一个由阿里通义千问驱动的智能助手。")

        with gr.Row():
            session_input = gr.Textbox(
                label="会话名称",
                value=initial_session,
                placeholder="例如：工作",
                scale=5,
            )
            load_button = gr.Button("切换会话", variant="secondary", scale=1)

        # 会话状态展示当前会话名、轮次，帮助用户确认上下文
        session_status = gr.Markdown(initial_status)

        # Chatbot 组件用来渲染聊天气泡，初始值为历史记录
        chatbot = gr.Chatbot(label="通义千问", height=500, value=initial_pairs)

        with gr.Row():
            txt_input = gr.Textbox(show_label=False, lines=3, placeholder="询问任何问题", scale=8)
            btn_submit = gr.Button("发送", variant="primary", scale=1)

        # --- 绑定事件 ---
        # 点击“切换会话”时先保存当前历史，再载入目标会话
        load_button.click(
            switch_session,
            inputs=[session_input, conversation_state, session_state],
            outputs=[session_input, chatbot, conversation_state, session_state, session_status],
        )

        submit_inputs = [txt_input, chatbot, conversation_state, session_state]
        submit_outputs = [chatbot, conversation_state, session_status]
        # 文本框回车、按钮点击共用同一套逻辑
        txt_input.submit(chat_response, submit_inputs, submit_outputs).then(lambda: "", [], [txt_input])
        btn_submit.click(chat_response, submit_inputs, submit_outputs).then(lambda: "", [], [txt_input])

    # 启动Gradio应用，启动后会在浏览器中打开一个新页面
    app.launch()

# --- 4. 主程序执行入口 ---
# 下面的代码只有在直接运行 `python ai_assistant.py` 时才会执行
if __name__ == "__main__":
    # 优先检查是否要启动 GUI 模式
    if '--gui' in sys.argv:
        start_gui()
    else:
        # 否则，启动默认的命令行模式
        # start_cli 函数内部会使用 argparse 处理所有相关的命令行参数
        start_cli()
