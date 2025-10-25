# AI 助手指引

欢迎来到 Assistant 项目！这是一个 Python 工具集合，包含多个独立的实用脚本。以下指引将帮助你快速理解和开发这个项目。

## 项目架构

### 核心服务层
- `ai_service.py`: 提供与阿里云通义千问模型交互的核心服务类 `AIAssistantService`
  - 处理 API 认证、请求发送和流式响应
  - 使用工厂模式封装 API 调用细节

### 主要应用
- `ai_assistant.py`: AI 聊天机器人，支持 CLI 和 Web UI 两种界面
  - CLI 模式：使用 `args.memory_mode` 控制记忆模式（'no', 'short', 'long'）
  - Web UI 模式：基于 Gradio 实现，使用 `gr.State` 管理会话状态

### 工具脚本目录结构
```
note_process/    # 笔记处理相关工具
  ├── html_to_md.py     # HTML 转 Markdown
  ├── office_to_md.py   # Office 文档转 Markdown
  ├── modify_content.py # 内容格式化
  └── note_summarize.py # 笔记总结工具

data_process/    # 数据处理工具
  └── excel_process.py  # Excel 数据处理
```

## 关键开发模式

### 1. 流式响应处理
所有涉及 AI 响应的功能都使用生成器模式实现流式输出：
```python
for chunk in ai_service.stream_chat_completion(history):
    if "网络错误" in chunk or "未知错误" in chunk:
        has_error = True
    full_response += chunk
```

### 2. 环境配置
项目统一使用 `.env` 文件管理敏感配置：
```python
load_dotenv()  # 在所有代码开头加载环境变量
API_KEY = os.getenv("ALIYUN_API_KEY")
```

### 3. 错误处理模式
使用特定标记识别和处理错误：
```python
if "网络错误" in response or "未知错误" in response:
    # 出错时不保存到历史记录
    has_error = True
```

## 项目约定

### 文件命名
- Python 脚本使用小写字母和下划线：`example_script.py`
- 配置文件使用大写：`README.md`, `.env`

### 代码风格
- 使用类型提示增强代码可读性：`def func(param: str) -> bool:`
- 每个函数都应有详细的 docstring 说明功能和参数
- 使用 f-strings 进行字符串格式化：`f"处理文件：{filename}"`

### 错误处理
- 对可能失败的操作使用 try-except 并提供用户友好的错误信息
- 网络请求总是需要错误处理
- 使用 "❌" 等 emoji 增强错误信息可读性

## 常见任务

### 添加新的工具脚本
1. 在相应目录（`note_process/` 或 `data_process/`）创建脚本
2. 添加详细的模块级 docstring 说明用途和用法
3. 在 `requirements.txt` 添加新依赖
4. 更新 `README.md` 添加使用说明

### 修改 AI 助手功能
1. 对话历史相关改动在 `ai_assistant.py` 中修改
2. API 调用相关改动在 `ai_service.py` 中修改
3. Web UI 相关改动在 `start_gui()` 函数中修改