# Python 学习与实用工具脚本

本代码库包含一系列独立的 Python 脚本，用于学习和实际应用。

##核心脚本

### 1. AI 助手 (`ai_assistant.py`)

一个具有两种界面的对话式 AI 聊天机器人：
- **CLI 界面**：一个基于终端的聊天机器人，具有持久化内存。
- **Web UI**：一个基于 Gradio 的 Web 界面，用于更可视化的交互。

**功能**：
- 由阿里云的通义千问（Qwen-flash）模型驱动。
- 支持流式响应，实现实时交互。
- 在 CLI 模式下保存对话历史。
- 可以将文件内容“注入”到对话中，以进行上下文感知的响应。

### 2. HTML 到 Markdown 转换器 (`html_to_md.py`)

一个强大的网络爬虫，可将网页的主要内容转换为干净的 Markdown 文件，并附带用于知识管理的 YAML Front Matter。

**功能**：
- 使用多种方法进行智能内容提取。
- 提取标题、作者和发布日期等元数据。
- 通过保存和重用登录会话，支持需要登录/付费的网站（例如《华尔街日报》）。
- 可以处理单个 URL 或包含多个 URL 的文件。

### 3. Office 和 PDF 到 Markdown 转换器 (`convert_office.py`)

一个用于将 Microsoft Office 文档（`.docx`、`.pptx`、`.xlsx`）和 PDF 文件转换为 Markdown 格式的实用工具。

### 4. Excel 数据处理器 (`excel_process.py`)

一个用于处理 Excel 文件的脚本。它读取电子表格，根据特定列中的值复制行，并将结果导出到新的 Excel 文件中。

## 设置与安装

1.  **克隆代码库**

2.  **创建虚拟环境（推荐）**

3.  **安装依赖项**

    从 `requirements.txt` 安装所有必需的库：
    ```bash
    pip install -r requirements.txt
    ```

4.  **安装 Playwright 浏览器**

    `html_to_md.py` 脚本需要 Playwright 的浏览器二进制文件。
    ```bash
    playwright install
    ```

5.  **配置环境变量**

    在项目根目录中创建一个名为 `.env` 的文件。此文件用于存储 API 密钥和其他机密。

    ```env
    # AI 助手的 API 密钥
    ALIYUN_API_KEY="your_api_key_here"

    # 为 HTML 到 Markdown 转换器保存《华尔街日报》登录状态的路径
    WSJ_AUTH_STATE_PATH="/path/to/your/wsj_auth_state.json"
    ```

## 使用方法

### AI 助手

-   **CLI 模式**：
    ```bash
    python ai_assistant.py
    ```
-   **带文件注入的 CLI**：
    ```bash
    python ai_assistant.py /path/to/your/file.txt
    ```
-   **Web UI 模式**：
    ```bash
    python ai_assistant.py --gui
    ```

### HTML 到 Markdown 转换器

-   **转换单个 URL**：
    ```bash
    python html_to_md.py "<URL>"
    ```
-   **从 URL 文件转换**：
    ```bash
    python html_to_md.py /path/to/your/links.txt
    ```
-   **保存到特定输出路径**：
    ```bash
    python html_to_md.py "<URL>" -o /path/to/output/
    ```
-   **登录网站（例如《华尔街日报》）**：
    这将打开一个浏览器窗口供您登录。登录后，会话将被保存以备将来使用。
    ```bash
    python html_to_md.py --login wsj
    ```

### Office 和 PDF 到 Markdown 转换器

```bash
python convert_office.py /path/to/your/file_or_folder
```
该脚本将转换指定的文件或指定文件夹中的所有支持的文件。

### Excel 数据处理器

1.  将名为 `工作簿1.xlsx` 的 Excel 文件放在根目录中。
2.  运行脚本：
    ```bash
    python excel_process.py
    ```
3.  输出将另存为 `处理后的工作簿.xlsx`。
