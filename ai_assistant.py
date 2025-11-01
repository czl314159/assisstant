"""
脚本名称: AI 助手 (ai_assistant.py)

功能描述:
    这是AI助手的交互层(门面)。
    它负责启动和管理命令行界面 (CLI) 和图形用户界面 (Web UI)，
    并将所有核心的AI逻辑处理委托给 `orchestrator.py`。

使用方法:
    与之前完全相同。
    - CLI: `python ai_assistant.py`
    - GUI: `python ai_assistant.py --gui`
"""
import os
import sys
import gradio as gr
import argparse
from dotenv import load_dotenv

# 核心变化：导入新的调度器
from orchestrator import Orchestrator

# --- 辅助函数 (UI相关，保留在此) ---
def history_to_chatbot_pairs(history):
    """
    将完整的消息历史转换为 Chatbot 组件需要的 [user, assistant] 列表。
    """
    pairs = []
    for message in history:
        role = message.get("role")
        content = message.get("content", "")
        if role == "user":
            pairs.append([content, ""])
        elif role == "assistant":
            if pairs:
                pairs[-1][1] = content
            else:
                pairs.append(["", content])
    return pairs

def format_session_status(session_id, history):
    """
    生成当前会话的状态文本，用于 GUI 顶部提示。
    """
    total_messages = len(history)
    turns = sum(1 for msg in history if msg.get("role") == "assistant")
    return f"当前会话：{session_id} ｜ 轮次：{turns} ｜ 消息数：{total_messages}"

# --- 1. 配置程序所需的变量 ---
load_dotenv()
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

# --- 2. 初始化核心调度器 ---
# 这是关键一步：创建Orchestrator的单一实例，它将管理所有后端逻辑
orchestrator = Orchestrator(
    api_key=API_KEY,
    model_name=MODEL_NAME,
    api_url=API_URL,
    temperature=TEMPERATURE,
    memory_root=MEMORY_ROOT
)

# --- 3. 命令行界面 (CLI) 启动逻辑 ---
def start_cli():
    """启动命令行版本的 AI 助手 (简化版)。"""
    parser = argparse.ArgumentParser(
        description="一个支持多种记忆模式和文件注入的命令行 AI 助手。",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter 
    )
    parser.add_argument(
        'file_path',
        nargs='?',
        default=None,
        help="指定要加载到上下文中的文件路径。如果提供，AI会先阅读文件内容。"
    )
    parser.add_argument(
        '-m', '--mode',
        dest='memory_mode',
        choices=['no', 'short', 'long'],
        default='short',
        help="设置记忆模式: 'no' (无记忆), 'short' (短期会话记忆), 'long' (长期持久化记忆)。"
    )
    parser.add_argument(
        '--session',
        dest='session_id',
        default=DEFAULT_SESSION_ID,
        help="指定会话名称，用于区分不同主题的长期记忆。"
    )
    args = parser.parse_args()
    session_id = orchestrator.normalize_session_id(args.session_id)

    print("🚀 正在启动命令行 AI 助手...")
    print(f"🧠 记忆模式: {args.memory_mode}")
    print(f"🗂 会话名称: {session_id}")

    if args.memory_mode == 'long':
        conversation_history = orchestrator.load_memory(session_id)
        if conversation_history:
            print(f"🗄 已加载会话 '{session_id}' 的历史消息，共 {len(conversation_history)} 条。")
        else:
            print(f"🗄 会话 '{session_id}' 暂无历史，将从头开始。")
    else:
        conversation_history = []
        print("AI小助手：你好！一个新的旅程开始了。")

    file_context = None
    if args.file_path:
        if os.path.isdir(args.file_path):
            print("📁 检测到文件夹输入。")
            print("此功能已移至新脚本 `note_process/batch_summarize.py`。")
            print(f"   python note_process/batch_summarize.py \"{args.file_path}\"")
            sys.exit(0)
        elif os.path.isfile(args.file_path):
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

    while True:
        user_input = input("你：")
        if user_input.lower() in ["quit", "exit", "bye", "goodbye", "q", "e"]:
            if args.memory_mode == 'long':
                orchestrator.save_memory(session_id, conversation_history)
            print("AI小助手：期待下次与你相见！")
            break

        # 核心变化：将所有工作委托给 orchestrator
        conversation_history = orchestrator.handle_cli_request(
            user_input=user_input,
            conversation_history=conversation_history,
            memory_mode=args.memory_mode,
            session_id=session_id,
            file_context=file_context
        )
        
        print("\n" + "-"*30)

# --- 4. 图形用户界面 (GUI) 启动逻辑 ---
def start_gui():
    """启动 Gradio 图形用户界面 (简化版)。"""
    print("🚀 正在启动 Gradio 图形界面...")

    initial_session = orchestrator.normalize_session_id(DEFAULT_SESSION_ID)
    initial_history = orchestrator.load_memory(initial_session)
    initial_pairs = history_to_chatbot_pairs(initial_history)
    initial_status = format_session_status(initial_session, initial_history)
    print(f"🗄 GUI 会话 '{initial_session}' 已加载 {len(initial_history)} 条消息。")

    def chat_response(user_input, chatbot_history, conversation_state, session_id):
        """Gradio的响应函数，现在是一个围绕Orchestrator的薄包装。"""
        # 更新本地状态和UI
        # 用户消息将由 orchestrator 添加到 history，此处不再重复添加
        chatbot_history.append([user_input, ""])
        yield (chatbot_history, conversation_state, gr.update(value=format_session_status(session_id, conversation_state)))

        # 核心变化：将流式响应的逻辑委托给 orchestrator
        full_response = ""
        for response_chunk in orchestrator.handle_gui_request(user_input, conversation_state, session_id):
            full_response = response_chunk
            chatbot_history[-1][1] = full_response
            yield (chatbot_history, conversation_state, gr.update(value=format_session_status(session_id, conversation_state)))

    def switch_session(requested_session, conversation_history, current_session_id):
        """会话切换，委托给 orchestrator。"""
        new_session, new_history = orchestrator.switch_gui_session(
            requested_session, conversation_history, current_session_id
        )
        chatbot_pairs = history_to_chatbot_pairs(new_history)
        status_text = format_session_status(new_session, new_history)
        return (gr.update(value=new_session), gr.update(value=chatbot_pairs), new_history, new_session, gr.update(value=status_text))

    with gr.Blocks(title="AI 助手") as app:
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

        session_status = gr.Markdown(initial_status)
        chatbot = gr.Chatbot(label="通义千问", height=500, value=initial_pairs)

        with gr.Row():
            txt_input = gr.Textbox(show_label=False, lines=3, placeholder="询问任何问题", scale=8)
            btn_submit = gr.Button("发送", variant="primary", scale=1)

        load_button.click(
            switch_session,
            inputs=[session_input, conversation_state, session_state],
            outputs=[session_input, chatbot, conversation_state, session_state, session_status],
        )

        submit_inputs = [txt_input, chatbot, conversation_state, session_state]
        submit_outputs = [chatbot, conversation_state, session_status]
        txt_input.submit(chat_response, submit_inputs, submit_outputs).then(lambda: "", [], [txt_input])
        btn_submit.click(chat_response, submit_inputs, submit_outputs).then(lambda: "", [], [txt_input])

    app.launch()

# --- 5. 主程序执行入口 ---
if __name__ == "__main__":
    if '--gui' in sys.argv:
        start_gui()
    else:
        start_cli()
