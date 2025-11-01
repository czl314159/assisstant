"""
脚本名称: 批量总结工具 (note_summarize.py)

功能描述:
    本脚本专门用于批量处理指定文件夹内的 Markdown 文件。
    它会自动遍历文件夹，查找文件中预设的“# 总结提炼”区域，
    如果该区域为空，则调用 AI 模型对文件内容进行总结，并将结果写回原文件。

使用方法:
    在终端中运行: `python note_process/note_summarize.py <文件夹路径> [选项]`

    1.  **基本用法**:
        `python note_process/note_summarize.py "D:\\MyNotes"`
        -   程序会提示您输入用于 AI 总结的提示词模板。

    2.  **使用命令行指定提示词**:
        `python note_process/note_summarize.py "D:\\MyNotes" --prompt "请总结以下内容：{activeNote}"`

    3.  **从文件加载提示词**:
        `python note_process/note_summarize.py "D:\\MyNotes" --prompt-file "my_prompt_template.txt"`

    **重要**: 提示词模板中必须包含 `{activeNote}` 占位符，它将被替换为每个文件的实际内容。

配置:
    - 依赖于项目根目录的 `.env` 文件来获取 AI 服务的相关配置（API Key, URL, Model Name等）。

依赖:
    - `python-dotenv`
    - `requests` (通过 ai_service 间接使用)
"""
import os
import sys
import re
import argparse
from dotenv import load_dotenv

# --- 动态添加项目根目录到 sys.path ---
# 这段代码是为了解决脚本在子目录中运行时，无法找到位于根目录的模块（如 ai_service）的问题。
# 1. 获取当前脚本文件（note_summarize.py）的绝对路径。
#    __file__ 是一个 Python 内置变量，代表当前脚本的文件名。
current_file_path = os.path.abspath(__file__)
# 2. 获取 note_summarize.py 所在的目录，即 'd:\Documents\Assistant\note_process'。
current_dir = os.path.dirname(current_file_path)
# 3. 获取 'note_process' 目录的上级目录，即项目的根目录 'd:\Documents\Assistant'。
project_root = os.path.dirname(current_dir)
# 4. 将项目根目录添加到 Python 解释器的模块搜索路径列表 (sys.path) 的最前面。
#    这样，当执行 import ai_service 时，Python 就能在根目录中找到 ai_service.py 文件。
sys.path.insert(0, project_root)

from ai_service import AIAssistantService # 从我们创建的共享模块中导入服务类

load_dotenv()

# --- 1. 配置程序所需的变量 ---
API_KEY = os.getenv("ALIYUN_API_KEY")
if not API_KEY:
    print("错误：未找到ALIYUN_API_KEY环境变量！请在.env文件中设置。")
    sys.exit(1)

API_URL = os.getenv("ALIYUN_API_URL")
if not API_URL:
    print("错误：未找到ALIYUN_API_URL环境变量！请在.env文件中设置。")
    sys.exit(1)

MODEL_NAME = os.getenv("ALIYUN_MODEL_NAME")
if not MODEL_NAME:
    print("警告：未找到ALIYUN_MODEL_NAME环境变量！请在.env文件中设置。")
    sys.exit(1)

TEMPERATURE = float(os.getenv("TEMPERATURE", 0.5))

SUMMARY_HEADING_MARKER = "# 总结提炼\n"
SUMMARY_PATTERN = re.compile(rf"({re.escape(SUMMARY_HEADING_MARKER)})", re.DOTALL)

# --- 2. 核心功能函数 ---
def process_folder_for_summaries(folder_path, ai_service, prompt_template):
    """
    遍历指定文件夹下的所有Markdown文件，查找总结提炼区域，
    如果该区域为空，则调用AI进行总结并写入文件。
    :param folder_path: 要处理的文件夹路径。
    :param ai_service: AI 服务实例。
    :param prompt_template: 用于生成AI请求的提示词模板。
    """
    print(f"📁 开始扫描文件夹：'{folder_path}'")
    processed_count = 0
    skipped_count = 0
    error_count = 0

    if "{activeNote}" not in prompt_template:
        print("⚠️ 警告：提供的提示词模板中未找到 '{activeNote}' 占位符。AI可能无法获取文件内容。")

    for root, _, files in os.walk(folder_path):
        for file_name in files:
            if not file_name.lower().endswith('.md'):
                continue

            file_path = os.path.join(root, file_name)
            print(f"\n--- 正在处理文件: {file_name} ---")

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                match = SUMMARY_PATTERN.search(content)
                if not match:
                    print(f"   ⏭️ 跳过：未找到总结提炼的标题标记 ('{SUMMARY_HEADING_MARKER.strip()}')。")
                    skipped_count += 1
                    continue

                summary_prompt = prompt_template.format(activeNote=content)
                temp_history = [{"role": "user", "content": summary_prompt}]
                
                print("   🤖 正在请求 AI 生成内容...")
                ai_summary = "".join(ai_service.stream_chat_completion(temp_history))

                if not ai_summary.strip():
                    print(f"   ⏭️ 跳过：AI 未返回有效内容。")
                    skipped_count += 1
                    continue

                # --- 新增：将模型名称附加到总结末尾 ---
                # 1. 从 AI 服务实例中获取当前使用的模型名称
                model_name = ai_service.model_name
                # 2. 创建一个格式化的、包含模型信息的 Markdown 字符串
                model_info_str = f"\n\n> 总结由 *{model_name}* 生成"
                # 3. 将 AI 总结、模型信息和必要的换行符拼接成最终要插入的内容
                content_to_insert = ai_summary.strip() + model_info_str + "\n"

                # 使用正则表达式替换，将拼接好的完整内容插入到“# 总结提炼”标题下方
                new_content = SUMMARY_PATTERN.sub(r"\1" + content_to_insert, content, 1)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"   ✅ 成功插入内容并更新文件。")
                processed_count += 1
                    
            except Exception as e:
                print(f"   ❌ 处理文件时发生错误: {e}")
                error_count += 1
                continue
    
    print("\n--- 批处理完成 ---")
    print(f"成功更新: {processed_count} 个文件")
    print(f"跳过: {skipped_count} 个文件")
    print(f"失败: {error_count} 个文件")
    print("------------------")

# --- 3. 主程序入口 ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="批量为 Markdown 文件生成 AI 总结。")
    parser.add_argument("folder_path", help="包含 Markdown 文件的文件夹路径。")
    prompt_group = parser.add_mutually_exclusive_group()
    prompt_group.add_argument('--prompt', dest='prompt_string', help="直接在命令行中提供提示词模板。")
    prompt_group.add_argument('--prompt-file', dest='prompt_file_path', help="从指定文件中加载提示词模板。")
    args = parser.parse_args()

    if not os.path.isdir(args.folder_path):
        print(f"❌ 错误：提供的路径 '{args.folder_path}' 不是一个有效的文件夹。")
        sys.exit(1)

    prompt_template = ""
    if args.prompt_string:
        prompt_template = args.prompt_string
    elif args.prompt_file_path:
        try:
            with open(args.prompt_file_path, 'r', encoding='utf-8') as f:
                prompt_template = f.read()
        except Exception as e:
            print(f"❌ 读取提示词文件 '{args.prompt_file_path}' 时出错: {e}")
            sys.exit(1)
    else:
        default_prompt = "请你仔细阅读以下文本，并提炼出主要内容和关键信息，生成一份简洁的总结。请直接输出总结内容，不要包含任何额外的前缀或后缀。\n\n文本内容:\n```\n{activeNote}\n```"
        print("\n批处理模式需要一个提示词模板。模板中必须包含 '{activeNote}' 占位符。")
        print(f"\n示例 (默认模板):\n---\n{default_prompt}\n---")
        user_prompt = input("\n请输入你的提示词模板 (直接按 Enter 使用默认模板): \n")
        prompt_template = user_prompt.strip() or default_prompt

    ai_service = AIAssistantService(API_KEY, MODEL_NAME, API_URL, TEMPERATURE)
    process_folder_for_summaries(args.folder_path, ai_service, prompt_template)
