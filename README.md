# 个人AI助理与自动化工具集

<p align="center">
  <strong>一个集成了AI对话、笔记处理和数据自动化的多功能Python工具箱。</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9%2B-blue" alt="Python Version">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License">
</p>

本项目是一个为提升个人生产力而设计的Python脚本集合。它不仅包含一个由大型语言模型驱动的、支持多种记忆模式的AI助手，还提供了一系列强大的自动化工具，用于处理从网页抓取、笔记整理到Excel数据操作的各种日常任务。

## 核心功能一览

- **🤖 多模式AI助手**:
  - **命令行 (CLI)** 与 **网页 (Web UI)** 双重交互界面。
  - 集成**阿里云通义千问**或兼容的API，支持流式响应。
  - 提供**短期、长期、无记忆**三种会话模式，长期模式支持多会话持久化。
  - 支持将本地文件内容**注入上下文**，让AI基于特定文档回答问题。

- **📝 强大的笔记处理工具集**:
  - **网页抓取与转换**: 从URL智能提取正文，转换为干净的Markdown，并支持需登录的网站。
  - **Office/PDF转换**: 批量将 `.docx`, `.pptx`, `.xlsx`, 和 `.pdf` 文件转换为Markdown。
  - **AI批量总结**: 自动为指定文件夹下的Markdown笔记生成内容摘要。
  - **周报自动汇总**: 聚合指定时间范围内的笔记，生成格式化的周报。
  - **元数据与内容修改**: 批量修改笔记的Front Matter和格式化段落。

- **📊 便捷的数据处理**:
  - **Excel行复制**: 根据指定列的数值，自动复制和处理Excel表格中的行。

## 项目结构导览

```
/
├── ai_assistant.py         # AI助手主程序 (CLI/Web UI入口)
├── ai_service.py           # 封装与大模型API的通信
├── memory_store.py         # 负责会话历史的存储与读取
│
├── note_process/           # 专为笔记处理和知识管理设计的工具
│   ├── weekly_gather.py    # 周报汇总
│   ├── html_to_md.py       # 网页抓取与转换
│   ├── note_summarize.py   # AI批量总结
│   ├── office_to_md.py     # Office/PDF转换
│   └── ...                 # 其他笔记处理脚本
│
├── data_process/           # 数据处理相关脚本
│   └── excel_process.py    # Excel自动化处理
│
├── requirements.txt        # 项目所有Python依赖
└── .env.example            # 环境变量配置示例 (需自行复制为 .env)
```

## 安装与配置指南

#### 1. 环境准备
- 确保您已安装 **Python 3.9** 或更高版本。

#### 2. 克隆并进入项目
```bash
git clone <您的项目仓库URL>
cd Assistant
```

#### 3. 创建并激活虚拟环境 (推荐)
这可以隔离项目依赖，避免与系统环境冲突。
```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
virtualenv\Scripts\activate
# macOS / Linux:
# source venv/bin/activate
```

#### 4. 安装所有依赖
项目所有依赖都记录在 `requirements.txt` 中。
```bash
pip install -r requirements.txt
```

#### 5. 安装浏览器驱动
`html_to_md.py` 脚本需要 Playwright 的浏览器二进制文件来抓取动态网页。
```bash
playwright install
```

#### 6. 配置环境变量
在项目根目录复制 `.env.example` 文件并重命名为 `.env`，然后根据您的实际情况填写其中的值。这是最关键的一步。

**`.env` 文件内容示例:** 
```env
# --- AI助手核心配置 ---
# 阿里云通义千问或其他兼容模型的API密钥
ALIYUN_API_KEY="sk-your_api_key_here"
# API的终端节点URL
ALIYUN_API_URL="https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
# 要使用的AI模型名称
ALIYUN_MODEL_NAME="qwen-long"

# --- 笔记处理工具配置 ---
# 周报汇总脚本(weekly_gather.py)所需的Obsidian库根目录绝对路径
OBSIDIAN_VAULT_ROOT="D:\path\to\your\obsidian_vault"
# 网页抓取脚本(html_to_md.py)保存登录状态的绝对路径
WSJ_AUTH_STATE_PATH="D:\path\to\your\wsj_auth_state.json"

# --- 可选配置 ---
# AI助手长期记忆会话的存储目录 (默认为 data/sessions)
# MEMORY_ROOT="data/sessions"
# AI模型温度参数 (默认为 0.5)
# TEMPERATURE=0.5
```

## 使用方法详解

### 🤖 AI 助手 (`ai_assistant.py`)

- **启动默认CLI (短期记忆)**:
  ```bash
  python ai_assistant.py
  ```
- **选择记忆模式**:
  ```bash
  # 使用长期持久化记忆
  python ai_assistant.py --mode long

  # 禁用记忆
  python ai_assistant.py --mode no
  ```
- **指定会话名称 (配合长期记忆)**:
  ```bash
  python ai_assistant.py --mode long --session "工作"
  ```
- **注入文件上下文进行提问**:
  ```bash
  python ai_assistant.py "D:\path\to\your\file.txt"
  ```
- **启动Web UI模式**:
  ```bash
  python ai_assistant.py --gui
  ```

### 📝 笔记处理工具集 (`note_process/`)

- **网页转Markdown (`html_to_md.py`)**:
  ```bash
  # 转换单个URL
  python -m note_process.html_to_md "https://example.com/article"

  # 从文件批量转换URL
  python -m note_process.html_to_md "D:\path\to\links.txt"

  # 启动交互式登录以保存网站(如华尔街日报)的Cookie
  python -m note_process.html_to_md --login wsj
  ```

- **周报汇总 (`weekly_gather.py`)**:
  ```bash
  # 直接运行，脚本会交互式询问
  python -m note_process.weekly_gather

  # 使用模板文件生成周报
  python -m note_process.weekly_gather --template "D:\path\to\template.md"
  ```

- **AI批量总结 (`note_summarize.py`)**:
  ```bash
  # 对指定文件夹下的所有笔记生成总结 (会提示输入Prompt)
  python -m note_process.note_summarize "D:\path\to\notes_folder"

  # 通过命令行直接提供Prompt
  python -m note_process.note_summarize "D:\path\to\notes_folder" --prompt "请总结以下内容：{content}"
  ```

- **Office/PDF转Markdown (`office_to_md.py`)**:
  ```bash
  # 转换单个文件
  python -m note_process.office_to_md "D:\path\to\document.docx"

  # 转换整个文件夹
  python -m note_process.office_to_md "D:\path\to\documents_folder"
  ```

- **修改Front Matter (`modify_frontmatter.py`)**:
修改文件夹下，符合`匹配键=匹配值`的文件的元数据，将其`目标键`设置为`目标值`。
  ```bash
  # 示例：将note_type为"备查笔记"的文件的content_type改为"知识教程"
  python -m note_process.modify_frontmatter "D:\note" note_type "备查笔记" content_type "知识教程"
  ```

### 📊 数据处理 (`data_process/`)

- **处理Excel (`excel_process.py`)**:
根据`新增记录`列的数值，复制对应行数，并输出为新文件。
  ```bash
  # 处理Excel文件的第一个工作表
  python -m data_process.excel_process "D:\path\to\data.xlsx"

  # 指定工作表名称或索引
  python -m data_process.excel_process "D:\path\to\data.xlsx" "Sheet2"
  ```

## 贡献指南

我们欢迎任何形式的贡献！无论是添加新功能、修复Bug，还是改进文档，都对我们意义重大。

1.  **Fork** 本项目。
2.  创建您的功能分支 (`git checkout -b feature/YourAmazingFeature`)。
3.  提交您的更改 (`git commit -m 'Add some AmazingFeature'`)。
4.  推送到分支 (`git push origin feature/YourAmazingFeature`)。
5.  提交一个 **Pull Request**。

## 许可

本项目基于 [MIT](LICENSE) 许可开源。