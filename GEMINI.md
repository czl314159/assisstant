# GEMINI.md

This file provides guidance when working with code in this repository.

## Project Overview

This is a Python learning repository containing individual utility scripts and learning exercises. The repository is not a single application but a collection of standalone tools and examples for Python education and practical utilities.

## Core Components

### AI Assistant (`ai_assistant.py`)
The main application is a conversational AI chatbot with two interfaces:
- **CLI interface**: Terminal-based chatbot with persistent memory.
- **Web UI**: Gradio-based web interface for the same chatbot.

**Architecture**:
- Uses Aliyun's Qwen-flash model via OpenAI-compatible API.
- Implements streaming responses for real-time interaction.
- Maintains conversation history in `data/chat_log.json`.
- Supports file injection: can load external files into conversation context via command-line argument.

**Key features**:
- Persistent conversation memory across sessions (CLI only).
- Streaming text generation (uses generators and `yield`).
- Environment-based configuration (requires `.env` file with `ALIYUN_API_KEY`).
- Error handling for network and API failures.

### Utility Scripts

**`convert_office.py`**: Office-to-Markdown converter
- Converts .docx, .pptx, .xlsx, and .pdf files to Markdown.
- Uses the `markitdown` library.

**`excel_process.py`**: Excel row duplication tool
- Reads from `工作簿1.xlsx`.
- Duplicates rows based on "新增记录" column value.
- Outputs to `处理后的工作簿.xlsx`.

**`html_to_md.py`**: HTML-to-Markdown converter
- Fetches content from a URL and converts it to Markdown.
- Supports single URLs or a file containing multiple URLs.
- Can save login sessions for sites requiring authentication (e.g., Wall Street Journal).
- Uses `playwright`, `beautifulsoup4`, `markdownify`, and `readability-lxml`.

## Running the Project

### Setup Environment
```bash
# Install dependencies
pip install requests python-dotenv markitdown pandas gradio playwright beautifulsoup4 markdownify readability-lxml

# Install Playwright browsers
playwright install

# Create .env file with API key
echo "ALIYUN_API_KEY=your_api_key_here" > .env
```

### Run AI Assistant
```bash
# Basic CLI usage
python ai_assistant.py

# With file injection (load file into context)
python ai_assistant.py path/to/file.txt

# To run the Web UI
python ai_assistant.py --gui

# Exit CLI: type "quit", "exit", "bye", or "goodbye"
```

### Run Utilities
```bash
# Excel processor (requires 工作簿1.xlsx in root)
python excel_process.py

# Office converter
python convert_office.py <path_to_file_or_folder>

# HTML to Markdown converter
python html_to_md.py <URL_or_file_path>
```

## Important Configuration Details

### API Configuration (`ai_assistant.py`)
- **API_KEY**: Must be set in `.env` file as `ALIYUN_API_KEY`.
- **MODEL_NAME**: Currently set to "qwen-flash".
- **TEMPERATURE**: Set to 0.5.
- **PROXY_URL**: Set to `None` (can be configured if needed).
- **HISTORY_FILE**: `data/chat_log.json` (auto-created).

### Data Persistence
- The `data/` folder is auto-created on first run.
- Chat history is saved to `data/chat_log.json` when exiting the CLI.
- Web UI does NOT persist conversations.

## Architecture Notes

### Streaming Response Pattern
Both AI interfaces use Python generators for streaming:
```python
for chunk in get_ai_reply(conversation_state):
    # Process each chunk as it arrives
    full_response += chunk
```

This pattern is used consistently across both CLI and Web UI implementations.

### State Management
- **CLI**: Full conversation history persisted to JSON file.
- **Web UI**: Uses Gradio's `gr.State` for in-memory state management during a session.
- Both maintain conversation as a list of `{"role": "user/assistant", "content": "..."}` objects.

### Error Handling Strategy
- Network errors are caught and displayed to the user with a prefix.
- Errors contain "网络错误" or "未知错误" markers.
- Responses with errors are NOT saved to the conversation history.
- The system checks for error markers before persisting assistant responses.

## File Structure
```
.
├── ai_assistant.py       # CLI and Gradio chatbot
├── convert_office.py    # Office converter
├── excel_process.py     # Excel utility
├── html_to_md.py        # HTML to Markdown converter
├── .env                 # API keys (not in git)
├── data/                # Runtime data (not in git)
│   └── chat_log.json   # Conversation history
└── GEMINI.md            # This file
```

## Dependencies
Core libraries:
- `requests`: HTTP client for API calls.
- `python-dotenv`: Environment variable management.
- `gradio`: Web UI framework.
- `pandas`: Excel processing.
- `markitdown`: Office document conversion.
- `playwright`: For web scraping and browser automation.
- `beautifulsoup4`: For parsing HTML.
- `markdownify`: For converting HTML to Markdown.
- `readability-lxml`: For extracting the main content from a webpage.
