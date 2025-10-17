# GEMINI.md

## Project Overview

This directory contains a collection of Python scripts for learning and utility purposes. It is not a single application but a set of individual tools.

The main scripts are:

*   **`ai_assistant.py`**: A command-line chatbot that uses the Aliyun Qwen-flash model. It saves chat history and requires an API key.
*   **`convert_office.py`**: A utility to convert Microsoft Office documents (.docx, .pptx, .xlsx) into Markdown format.
*   **`ExcelDataProcess.py`**: A script for processing Excel files. It reads a spreadsheet, duplicates rows based on specified criteria, and exports the result to a new file.
*   **Learning Scripts**: `HelloWorld.py`, `Dic-Dic.py`, `Dic-List.py`, and `List-Dic.py` are beginner-level scripts for learning Python syntax and data structures.

## Building and Running

There is no central build process. Scripts are intended to be run individually.

### Dependencies

The following Python libraries are required for some of the scripts:

*   `requests`
*   `python-dotenv`
*   `markitdown`
*   `pandas`

You can install them using pip:

```bash
pip install requests python-dotenv markitdown pandas
```

### Running the Scripts

**AI Assistant**

1.  Create a `.env` file in the root directory.
2.  Add your Aliyun API key to the `.env` file:
    ```
    ALIYUN_API_KEY="your_api_key_here"
    ```
3.  Run the script from the command line:
    ```bash
    python ai_assistant.py
    ```

**Office to Markdown Converter**

1.  Modify the `input_file_path` variable in `convert_office.py` to point to your Office document.
2.  Run the script:
    ```bash
    python convert_office.py
    ```
    The output Markdown file will be saved in the same directory as the input file.

**Excel Data Processor**

1.  Place your Excel file named `工作簿1.xlsx` in the root directory.
2.  Run the script:
    ```bash
    python ExcelDataProcess.py
    ```
    The output file will be named `处理后的工作簿.xlsx`.

**Learning Scripts**

These can be run directly to see their output:

```bash
python HelloWorld.py
python Dic-Dic.py
# etc.
```

## Development Conventions

*   The scripts are written in Python.
*   The `ai_assistant.py` script uses a `.env` file for managing secrets.
*   The `data` directory is used to store the chat log for the AI assistant.
