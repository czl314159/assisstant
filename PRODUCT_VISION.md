# AI知识助理产品设计思路 (V1.0)

---

## 1. 产品愿景 (Product Vision)

**构建一个以自然语言为核心交互方式，协助进行个人知识管理的AI Agent。**

- 最终目标是想打造一个能够理解用户意图、自主调度工具、并能与用户共同成长的智能化“数字伙伴”，使用户能将注意力更多地集中在文字创作。

- 产品形态：初步考虑以命令行形式实现，类似于Claude Code和Gemini CLI；未来希望能够通过Obsidian插件实现可视化界面。

## 2. 产品定位与目标用户

- **产品定位**：一个高度可定制、可扩展的个人知识管理AI Agent框架。

- **目标用户**：使用markdown文件作为数据载体的知识管理者等。

## 3. 核心设计原则

- **对话驱动 (Conversation-Driven)**：自然语言是首要且唯一的交互界面。用户通过“说”来下达指令，而不是通过“点”或“敲”来执行命令。

- **工具赋能 (Tool-Augmented)**：AI的核心价值在于调用和编排已有的功能工具。AI本身不执行具体任务，而是作为“大脑”来调度“四肢”（即功能脚本）。

- **可扩展 (Personalized & Extensible)**：所有工具都围绕个人的具体需求构建，且整个架构应设计为易于添加新的“工具”或“技能”。

- **本地优先与数据私有 (Local-First & Data-Private)**：系统的核心操作对象是用户的本地markdown文件，确保了数据的私密性和用户对数据的绝对控制权。

## 4. 概念架构 (Conceptual Architecture)

产品将遵循一个更加清晰的三层Agent架构模型：

```
+----------------------------------------------------+
|             交互层 (Interaction Layer)             |
|               (ai_assistant.py)                    |
+--------------------------+-------------------------+
                           ^
                           | (Request)
                           v
+--------------------------+-------------------------+
|           调度层 (Orchestration Layer)             |
|               (orchestrator.py)                    |
| (意图识别 -> 参数提取 -> 安全审查 -> 工具决策)     |
+--------------------------+-------------------------+
                           ^
                           | (Function Call)
                           v
+--------------------------+-------------------------+
|              工具层 (Tooling Layer)                |
| (原子能力: execute_shell, weekly_gather, etc.)     |
+----------------------------------------------------+
```

- **交互层 (`ai_assistant.py`)**：负责接收用户输入并呈现系统输出，是产品的“脸面”。
- **调度层 (`orchestrator.py`)**：产品的“大脑”，核心AI逻辑所在地。它负责将用户的自然语言指令翻译成对工具层的函数调用，并内置安全审查机制。
- **工具层 (Python Functions)**：产品的“工具箱”，由一系列独立的、功能明确的Python函数构成，负责执行所有具体任务（如文件操作、API调用、Shell命令执行等）。

## 5. 核心功能模块

- **交互层 (`ai_assistant.py`)**
  - 作为程序主入口，负责启动和管理应用。
  - 提供命令行界面(CLI)或Web用户界面(Web UI)的交互逻辑。
  - 接收用户输入，并将其传递给调度层。
  - 从调度层获取结果，并将其呈现给用户。

- **调度层 (`orchestrator.py`)**
  - **意图识别器 (Intent Recognizer)**：通过LLM分析用户输入，判断其属于“普通闲聊”还是“特定任务”。
  - **参数提取器 (Parameter Extractor)**：若为特定任务，则通过LLM从用户输入中提取执行该任务所需的参数。
  - **工具调度器 (Tool Dispatcher)**：根据识别出的意图，调用工具层中对应的函数，并将提取的参数传入。
  - **安全审查器 (Security Reviewer)**：对于高风险操作（如执行shell命令），在执行前向用户请求确认。
  - **结果反馈器 (Result Presenter)**：将工具层的执行结果（如成功信息、文件路径、错误提示）包装成流畅的自然语言，准备返回给交互层。

- **工具层 (由`note_process/`和`data_process/`中的脚本改造而来)**
  - **初始内置工具集**：
    - `system.execute_shell(command: str)`: 执行一个shell/bash命令。**（安全警告：此操作必须经过用户明确授权）**
    - `knowledge_capture.fetch_web_page(url: str)`
    - `knowledge_synthesis.gather_weekly_notes(template_path: str)`
    - `file_conversion.convert_office_file(file_path: str)`
    - `data_automation.process_excel_rows(file_path: str, sheet_name: str)`
    - ... (所有现有脚本都将改造为类似的函数化接口)
