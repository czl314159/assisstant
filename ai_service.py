"""
模块名称: AI 服务模块 (ai_service.py)

功能描述:
    本模块封装了与大语言模型（LLM）API 交互的核心逻辑。
    它提供了一个可复用的 `AIAssistantService` 类，用于发送请求、处理流式响应和管理 API 认证。
    其他需要调用 AI 功能的脚本可以通过导入此类来简化开发。

配置:
    - 本模块依赖于 .env 文件中的以下环境变量:
        - `ALIYUN_API_KEY`: 阿里云 API 密钥。
        - `ALIYUN_API_URL`: API 的终端节点 URL。
        - `ALIYUN_MODEL_NAME`: 要使用的 AI 模型名称。
        - `TEMPERATURE`: 控制生成文本的随机性（可选，默认为 0.5）。
"""
import os
import requests
import json

class AIAssistantService:
    """
    封装与 AI 模型交互的所有逻辑，包括 API 请求、流式响应处理和错误管理。
    """
    def __init__(self, api_key, model_name, api_url, temperature):
        """
        初始化 AI 服务实例。

        :param api_key: 用于 API 认证的密钥。
        :param model_name: 要使用的 AI 模型名称。
        :param api_url: API 的终端节点 URL。
        :param temperature: 控制生成文本的随机性。
        """
        self.api_key = api_key
        self.model_name = model_name
        self.api_url = api_url
        self.temperature = temperature
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

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
            response = requests.post(self.api_url, headers=self.headers, json=data, stream=True)
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
