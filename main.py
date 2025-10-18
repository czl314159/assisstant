import gradio as gr
from dotenv import load_dotenv

load_dotenv()  # 加载 .env 文件中的环境变量

import ai_assistant

# --- 2. 为 Gradio UI 编写的接口函数 ---

def chat_response(user_input, chatbot_history, conversation_state):
    """处理用户输入，并流式返回AI响应"""
    # 将用户输入添加到对话历史状态
    conversation_state.append({"role": "user", "content": user_input})
    # 更新Chatbot UI以立即显示用户输入
    chatbot_history.append([user_input, ""])
    yield chatbot_history, conversation_state

    # 流式获取AI回复
    full_response = ""
    has_error = False
    for chunk in ai_assistant.get_ai_reply(conversation_state):
        if "网络错误" in chunk or "未知错误" in chunk:
            has_error = True
        full_response += chunk
        chatbot_history[-1][1] = full_response
        yield chatbot_history, conversation_state

    # 如果没有错误，将完整的AI回复添加到对话历史状态并保存
    if not has_error:
        conversation_state.append({"role": "assistant", "content": full_response})
        # 注意：为了极致精简，这里移除了每次对话都保存历史的功能。
        # 历史记录将在程序退出时由用户手动或脚本的其他机制保存。

# --- 3. 构建 Gradio 界面 ---

with gr.Blocks(theme=gr.themes.Soft(), title="AI 助手") as demo:
    # 用于在后端存储完整对话历史（包含system role等）
    # 注意：为了极致精简，这里不再从文件加载历史，而是从一个空列表开始。
    conversation_state = gr.State(value=[])

    gr.Markdown("# 🤖 AI 助手")
    gr.Markdown("一个极简的智能对话助手。")

    # 主要聊天界面
    chatbot = gr.Chatbot(label="对话窗口", height=500)
    
    with gr.Row():
        txt_input = gr.Textbox(show_label=False, placeholder="在这里输入你的问题...", scale=4)
        btn_submit = gr.Button("发送", variant="primary", scale=1)

    # --- 绑定事件 ---
    # 提交文本消息的逻辑
    txt_input.submit(chat_response, [txt_input, chatbot, conversation_state], [chatbot, conversation_state])
    txt_input.submit(lambda: "", [], [txt_input]) # 提交后清空输入框
    btn_submit.click(chat_response, [txt_input, chatbot, conversation_state], [chatbot, conversation_state])
    btn_submit.click(lambda: "", [], [txt_input]) # 点击后清空输入框

if __name__ == "__main__":
    # 启动Gradio应用
    demo.launch()