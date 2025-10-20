# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python learning repository containing individual utility scripts and learning exercises. The repository is not a single application but a collection of standalone tools and examples for Python education and practical utilities.

## Core Components

### AI Assistant (`ai_assistant.py` and `main.py`)
The main application is a conversational AI chatbot with two interfaces:
- **CLI interface** (`ai_assistant.py`): Terminal-based chatbot with persistent memory
- **Web UI** (`main.py`): Gradio-based web interface for the same chatbot

**Architecture**:
- Uses Aliyun's Qwen-flash model via OpenAI-compatible API
- Implements streaming responses for real-time interaction
- Maintains conversation history in `data/chat_log.json`
- Supports file injection: can load external files into conversation context via command-line argument

**Key features**:
- Persistent conversation memory across sessions
- Streaming text generation (uses generators and `yield`)
- Environment-based configuration (requires `.env` file with `ALIYUN_API_KEY`)
- Error handling for network and API failures

### Utility Scripts

**`ExcelDataProcess.py`**: Excel row duplication tool
- Reads from `工作簿1.xlsx`
- Duplicates rows based on "新增记录" column value
- Outputs to `处理后的工作簿.xlsx`

**`convert_office.py`**: Office-to-Markdown converter
- Converts .docx, .pptx, .xlsx files to Markdown
- Uses the `markitdown` library
- Requires manual path configuration in the script

### Learning Scripts
Simple Python examples for beginners:
- `HelloWorld.py`: Basic print statement
- `Dic-Dic.py`, `Dic-List.py`, `List-Dic.py`: Dictionary and list operations

## Running the Project

### Setup Environment
```bash
# Install dependencies
pip install requests python-dotenv markitdown pandas gradio

# Create .env file with API key
echo "ALIYUN_API_KEY=your_api_key_here" > .env
```

### Run AI Assistant (CLI)
```bash
# Basic usage
python ai_assistant.py

# With file injection (load file into context)
python ai_assistant.py path/to/file.txt

# Exit: type "quit", "exit", "bye", or "goodbye"
```

### Run AI Assistant (Web UI)
```bash
# Launches Gradio web interface
python main.py
```

### Run Utilities
```bash
# Excel processor (requires 工作簿1.xlsx in root)
python ExcelDataProcess.py

# Office converter (edit input_file_path in script first)
python convert_office.py

# Learning scripts
python HelloWorld.py
```

## Important Configuration Details

### API Configuration (`ai_assistant.py`)
- **API_KEY**: Must be set in `.env` file as `ALIYUN_API_KEY`
- **MODEL_NAME**: Currently set to "qwen-flash"
- **TEMPERATURE**: Set to 0.5
- **PROXY_URL**: Set to `None` (can be configured if needed)
- **HISTORY_FILE**: `data/chat_log.json` (auto-created)

### Data Persistence
- The `data/` folder is auto-created on first run
- Chat history is saved to `data/chat_log.json` when exiting the CLI
- Web UI (`main.py`) does NOT persist conversations (simplified version)

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
- **CLI**: Full conversation history persisted to JSON file
- **Web UI**: Uses Gradio's `gr.State` for in-memory state management during session
- Both maintain conversation as list of `{"role": "user/assistant", "content": "..."}` objects

### Error Handling Strategy
- Network errors are caught and displayed to user with prefix
- Errors contain "网络错误" or "未知错误" markers
- Responses with errors are NOT saved to conversation history
- The system checks for error markers before persisting assistant responses

## File Structure
```
.
├── ai_assistant.py       # CLI chatbot (main AI logic)
├── main.py              # Gradio web UI wrapper
├── ExcelDataProcess.py  # Excel utility
├── convert_office.py    # Office converter
├── HelloWorld.py        # Learning examples
├── Dic-*.py, List-*.py  # Learning examples
├── .env                 # API keys (not in git)
├── data/                # Runtime data (not in git)
│   └── chat_log.json   # Conversation history
└── GEMINI.md           # Previous documentation
```

## Dependencies
Core libraries:
- `requests`: HTTP client for API calls
- `python-dotenv`: Environment variable management
- `gradio`: Web UI framework
- `pandas`: Excel processing
- `markitdown`: Office document conversion
