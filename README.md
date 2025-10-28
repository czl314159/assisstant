# Python 学习与实用工具脚本

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9%2B-blue" alt="Python Version">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License">
  <img src="https://img.shields.io/github/actions/workflow/status/{username}/{repository}/ci.yml?branch=main" alt="CI/CD Status">
  <img src="https://img.shields.io/codecov/c/github/{username}/{repository}" alt="Code Coverage">
</p>

本代码库包含一系列独立的 Python 脚本，用于学习和实际应用。

## 核心功能

- **🤖 AI 助手 (`ai_assistant.py`)**:
  - 支持 **CLI** 和 **Web UI** 两种交互模式。
  - 集成阿里云**通义千问**模型，支持流式响应。
  - 提供多种记忆策略与多会话持久化，并可注入文件上下文。

- **🌐 HTML 转 Markdown (`note_process/html_to_md.py`)**:
  - 智能提取网页正文，生成干净的 Markdown 文件。
  - 自动处理元数据，支持需登录网站（如华尔街日报）。

- **📄 Office/PDF 转 Markdown (`note_process/office_to_md.py`)**:
  - 批量将 `.docx`, `.pptx`, `.xlsx`, 和 `.pdf` 文件转换为 Markdown。

- **📊 Excel 数据处理 (`data_process/excel_process.py`)**:
  - 根据指定列的数值，灵活地复制和处理 Excel 行。

- **📝 笔记处理工具**:
  - `note_summarize.py`: 批量总结 Markdown 文件。
  - `modify_content.py`: 自动格式化文本段落。
  - `modify_frontmatter.py`: 批量修改 Front Matter。
  - `weekly_gather.py`: 自动汇总周报。

## 安装指南

### 1. 克隆项目
```bash
git clone https://github.com/{username}/{repository}.git
cd Assistant-CLI
```

### 2. 创建虚拟环境 (推荐)
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

### 3. 安装依赖
项目所有依赖都记录在 `requirements.txt` 中。
```bash
pip install -r requirements.txt
```

### 4. 安装浏览器驱动
`html_to_md.py` 脚本需要 Playwright 的浏览器二进制文件。
```bash
playwright install
```

### 5. 配置环境变量
在项目根目录创建一个 `.env` 文件，用于存放 API 密钥等敏感信息。
```env
# AI 助手的 API 密钥
ALIYUN_API_KEY="your_api_key_here"
ALIYUN_API_URL="your_api_url_here"
ALIYUN_MODEL_NAME="your_model_name_here"

# 周报汇总脚本的 Obsidian 库根路径
OBSIDIAN_VAULT_ROOT="/path/to/your/obsidian_vault"

# 可选: 长期记忆会话存储目录
# MEMORY_ROOT="data/sessions"
```

## 使用方法

### AI 助手
- **默认 CLI (短期记忆)**  
  ```bash
  python ai_assistant.py
  ```
- **选择记忆模式**  
  ```bash
  python ai_assistant.py --mode long      # 长期记忆
  python ai_assistant.py --mode no        # 不保留历史
  ```
- **指定会话名称（配合长期记忆）**  
  ```bash
  python ai_assistant.py --mode long --session 工作
  ```
- **注入文件上下文**  
  ```bash
  python ai_assistant.py /path/to/file.txt --mode long
  ```
- **Web UI 模式**  
  ```bash
  python ai_assistant.py --gui
  ```

### HTML 转 Markdown
- **转换单个 URL**:
  ```bash
  python note_process/html_to_md.py "<URL>"
  ```
- **从文件批量转换**:
  ```bash
  python note_process/html_to_md.py /path/to/your/links.txt
  ```
- **登录网站 (以华尔街日报为例)**:
  ```bash
  python note_process/html_to_md.py --login wsj
  ```

### Office/PDF 转 Markdown
```bash
python note_process/office_to_md.py /path/to/your/file_or_folder
```

### Excel 数据处理
```bash
python data_process/excel_process.py /path/to/your/data.xlsx "SheetName"
```

## 贡献指南

我们欢迎任何形式的贡献！无论是添加新功能、修复 Bug，还是改进文档，都对我们意义重大。

### 如何贡献
1. **Fork 项目**: 在 GitHub 上 Fork 本项目。
2. **创建分支**: `git checkout -b feature/YourFeature`
3. **提交更改**: `git commit -m 'Add some feature'`
4. **推送分支**: `git push origin feature/YourFeature`
5. **创建 Pull Request**: 提交你的 PR，等待我们审核。

### 开发约定
- **代码风格**: 遵循 PEP 8，使用类型提示，并为每个函数编写详细的 docstring。
- **错误处理**: 对可能失败的操作使用 `try-except`，并提供友好的错误信息。
- **命名规范**: 脚本使用小写下划线命名法（如 `example_script.py`）。

## 许可
本项目基于 [MIT](LICENSE) 许可开源。
