# d:\Documents\Assistant\orchestrator.py
from ai_service import AIAssistantService
from memory_store import MemoryStore
import os

class Orchestrator:
    """
    调度层 (Orchestrator)
    - 负责核心业务逻辑，作为AI的“大脑”。
    - 接收来自交互层的请求，并决定如何响应。
    - 管理与AI服务和记忆存储的交互。
    """
    def __init__(self, api_key, model_name, api_url, temperature, memory_root):
        self.ai_service = AIAssistantService(
            api_key=api_key,
            model_name=model_name,
            api_url=api_url,
            temperature=temperature,
        )
        self.memory_store = MemoryStore(root_dir=memory_root)

    def handle_cli_request(self, user_input, conversation_history, memory_mode, session_id, file_context=None):
        """处理来自CLI的单次请求，并流式打印响应。"""
        
        if file_context:
            final_input = f"""请基于以下文档内容来回答我的问题。
---
文档内容:
{file_context}
---
我的问题是：{user_input}
"""
        else:
            final_input = user_input
        
        conversation_history.append({"role": "user", "content": final_input})

        if memory_mode == 'no':
            history_to_send = [conversation_history[-1]]
        else:
            history_to_send = conversation_history

        print(f"AI助手：", end="")
        full_response = ""
        has_error = False
        for chunk in self.ai_service.stream_chat_completion(history_to_send):
            if "网络错误" in chunk or "未知错误" in chunk:
                has_error = True
            full_response += chunk
            print(chunk, end="", flush=True)
        print()

        if not has_error:
            conversation_history.append({"role": "assistant", "content": full_response})
            if memory_mode == 'long':
                self.memory_store.save(session_id, conversation_history)
        
        return conversation_history

    def handle_gui_request(self, user_input, conversation_state, session_id):
        """处理来自GUI的流式请求，作为生成器返回响应。"""
        session_id = self.memory_store.normalize_session_id(session_id)
        conversation_state.append({"role": "user", "content": user_input})

        full_response = ""
        has_error = False
        for chunk in self.ai_service.stream_chat_completion(conversation_state):
            if "网络错误" in chunk or "未知错误" in chunk:
                has_error = True
            full_response += chunk
            yield full_response

        if not has_error:
            conversation_state.append({"role": "assistant", "content": full_response})
            self.memory_store.save(session_id, conversation_state)
    
    def switch_gui_session(self, requested_session, conversation_history, current_session_id):
        """处理GUI的会话切换请求。"""
        current_session_id = self.memory_store.normalize_session_id(current_session_id)
        if conversation_history:
            self.memory_store.save(current_session_id, conversation_history)

        new_session = self.memory_store.normalize_session_id(requested_session)
        new_history = self.memory_store.load(new_session)
        print(f"🗄 已切换到会话 '{new_session}'，共 {len(new_history)} 条消息。")
        return new_session, new_history

    def load_memory(self, session_id):
        """加载指定会话的历史记录。"""
        return self.memory_store.load(session_id)
    
    def save_memory(self, session_id, history):
        """保存指定会话的历史记录。"""
        self.memory_store.save(session_id, history)

    def normalize_session_id(self, session_id):
        """规范化会话ID，移除不安全字符。"""
        return self.memory_store.normalize_session_id(session_id)