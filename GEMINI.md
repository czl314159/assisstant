# GEMINI.md

## Project Overview

This project is a collection of Python scripts designed to provide a variety of utilities, with a focus on AI-powered assistance, data processing, and note management. The core of the project is an AI assistant that can be interacted with via a command-line interface (CLI) or a web-based graphical user interface (GUI).

The project is structured into several modules, each with a specific purpose:

- **`ai_assistant.py`**: The main entry point for the AI assistant.
- **`ai_service.py`**: A service module that handles communication with the AI model's API.
- **`data_process/`**: Scripts for processing data, such as the `excel_process.py` for working with Excel files.
- **`note_process/`**: A collection of scripts for managing and processing notes, including tools for converting documents to Markdown, summarizing content, and modifying file metadata.

## Building and Running

### 1. Installation

To get started, you need to install the required Python packages and set up the necessary browser components for web scraping.

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browsers (for html_to_md.py)
playwright install
```

### 2. Configuration

The project uses a `.env` file to manage environment variables, such as API keys and file paths. Before running the scripts, create a `.env` file in the root of the project and add the following variables:

```
ALIYUN_API_KEY="your_api_key"
ALIYUN_API_URL="your_api_url"
ALIYUN_MODEL_NAME="your_model_name"
WSJ_AUTH_STATE_PATH="/path/to/your/wsj_auth_state.json"
OBSIDIAN_VAULT_ROOT="/path/to/your/obsidian_vault"
```

### 3. Running the Scripts

The scripts in this project are designed to be run from the command line. Here are some examples of how to run the main scripts:

- **AI Assistant (CLI):**
  ```bash
  python ai_assistant.py
  ```

- **AI Assistant (Web UI):**
  ```bash
  python ai_assistant.py --gui
  ```

- **HTML to Markdown Converter:**
  ```bash
  python note_process/html_to_md.py "<URL>"
  ```

- **Office to Markdown Converter:**
  ```bash
  python note_process/office_to_md.py <file_or_folder_path>
  ```

- **Excel Data Processor:**
  ```bash
  python data_process/excel_process.py <excel_file_path>
  ```

## Development Conventions

- **Modularity**: The project is organized into modules with specific responsibilities, such as the `ai_service.py` module for handling AI API interactions.
- **Configuration**: Environment variables are used to separate configuration from code, which is a good practice for managing sensitive information like API keys.
- **Documentation**: The code is well-documented with docstrings and comments, which makes it easier to understand and maintain.
- **Command-Line Interface**: The scripts are designed to be run from the command line, with arguments for specifying input and options.
