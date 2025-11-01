#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
自动汇总本周周日报（基于周日）
- 从 Collection/YYYYMMDD 文件夹中读取各笔记
- 提取 “# 总结提炼” 至下一个 “---” 之间内容
- 输出到 Collection/ 下的新文件

用法示例:

1. 直接运行 (不指定模板):
   在命令行中执行以下命令。脚本会提示确认是否在没有模板的情况下继续。
   > python -m note_process.weekly_gather

2. 使用模板文件:
   使用 --template 或 -t 参数指定一个 Markdown 文件作为周报的头部。
   > python -m note_process.weekly_gather --template "D:\\path\\to\\your\\template.md"
   (请将路径替换为您的实际模板文件路径)
"""

from datetime import datetime, timedelta
from pathlib import Path
import re
import os
import argparse
import sys
from dotenv import load_dotenv

load_dotenv() # 在所有代码之前，运行这个函数，它会自动加载.env文件

# ---------- 基本配置 ----------
# 从环境变量中读取 Obsidian 库的根路径
# 这是一个推荐的最佳实践，可以避免将个人路径硬编码到代码中
VAULT_ROOT_PATH_STR = os.getenv("OBSIDIAN_VAULT_ROOT")
if not VAULT_ROOT_PATH_STR:
    # 如果环境变量不存在，打印错误信息并终止脚本
    print("错误：环境变量 'OBSIDIAN_VAULT_ROOT' 未设置。")
    print("请在项目根目录的 .env 文件或您的操作系统中设置该变量，使其指向您的 Obsidian 库根目录。")
    sys.exit(1) # 使用非零状态码退出，表示程序因错误而终止

VAULT_ROOT = Path(VAULT_ROOT_PATH_STR)  # 将获取到的字符串路径转换为更易于操作的 Path 对象
COLLECT_BASE = "Collection"
SECTION_ANCHOR = "# 总结提炼"
HR_LINE = "---"
# --------------------------------

def yyyymmdd(d: datetime) -> str:
    return f"{d.year}{d.month:02d}{d.day:02d}"

def this_week_sunday(today: datetime) -> datetime:
    """获取本周周日日期（今天为周日则取今天）"""
    return today + timedelta(days=(6 - today.weekday()))

def read_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return p.read_text(encoding="utf-8", errors="ignore")

def parse_frontmatter_source(text: str) -> str:
    """解析 frontmatter 的 source 字段，兼容单双引号与 CRLF"""
    m = re.match(r"^---\r?\n([\s\S]*?)\r?\n---", text)
    if not m:
        return ""
    yaml_block = m.group(1)
    m2 = re.search(r"(?m)^\s*source\s*:\s*(.*)\s*$", yaml_block)
    if not m2:
        return ""
    source = m2.group(1).strip()
    return re.sub(r"^['\"]|['\"]$", "", source)

def extract_summary(text: str) -> str:
    """直接提取 #总结提炼 与 --- 之间的全部原文内容"""
    lines = text.splitlines()
    try:
        # 查找“# 总结提炼”标记的起始行号
        start = next(i for i, l in enumerate(lines) if l.strip() == SECTION_ANCHOR)
    except StopIteration:
        # 如果找不到标记，返回空字符串
        return ""
    # 从起始行之后开始，查找“---”标记的结束行号
    end = next((i for i in range(start+1, len(lines)) if lines[i].strip() == HR_LINE), -1)
    if end <= start:
        # 如果找不到结束标记，也返回空字符串
        return ""
    # 提取两个标记之间的所有行
    body = lines[start+1:end]
    # 将这些行重新组合成一个字符串并返回
    return "\n".join(body).strip()

def build_block(summary: str, source: str, note_title: str) -> str:
    """将原文内容和元数据组合成一个完整的 Markdown 块"""
    # 创建一个列表来收集元数据行，以便灵活处理
    meta_lines = []
    # 1. 添加带有 Markdown 引用格式的原文笔记链接
    meta_lines.append(f"> [[{note_title}]]")
    
    # 2. 如果来源信息（source）存在，则将其作为新的一行，同样添加引用格式
    if source:
        meta_lines.append(f"> {source}")
        
    # 3. 使用换行符将所有元数据行连接成一个最终的字符串
    meta = "\n".join(meta_lines)
    # 直接返回原文内容、元数据和分隔符，不再添加额外的二级标题
    return f"{summary}\n\n{meta}\n\n"

def main():
    # --- 1. 使用 argparse 解析命令行参数 ---
    parser = argparse.ArgumentParser(description="自动汇总本周的 Obsidian 笔记，生成周报。")
    parser.add_argument(
        "-t", "--template",
        dest="template_path", # 解析后的参数名
        default=None,
        help="指定一个 Markdown 文件作为周报的模板头部。"
    )
    args = parser.parse_args()

    # --- 2. 根据参数决定模板头部内容 ---
    template_content = "" # 默认模板内容为空字符串
    if args.template_path:
        # 如果用户提供了模板文件路径
        template_file = Path(args.template_path)
        if template_file.is_file():
            print(f"📄 正在从 '{template_file}' 加载模板...")
            template_content = template_file.read_text(encoding="utf-8")
        else:
            print(f"❌ 错误：指定的模板文件不存在 -> {args.template_path}")
            sys.exit(1)
    else:
        # 如果用户未提供模板文件，则进行交互式询问
        user_choice = input("未提供模板文件。是否继续生成一个不含头部的周报？(y/N): ").lower()
        if user_choice != 'y':
            print("操作已取消。")
            sys.exit(0)
        print("好的，将生成一个不含头部的周报。")

    target_str = yyyymmdd(this_week_sunday(datetime.now()))
    vault_root = VAULT_ROOT
    target_folder = vault_root / COLLECT_BASE / target_str

    if not target_folder.exists():
        print(f"[WARN] 文件夹不存在：{target_folder}")
        sys.exit(0)

    blocks = []
    for md in sorted(target_folder.glob("*.md")):
        text = read_text(md)
        source = parse_frontmatter_source(text)
        # 调用修改后的 extract_summary，它现在只返回一个值：原文内容
        summary = extract_summary(text)
        if summary:
            blocks.append(build_block(summary, source, md.stem))

    if not blocks:
        print("[INFO] 没有可汇总内容。")
        return

    out_file = vault_root / COLLECT_BASE / f"AI周报-{target_str}.md"
    out_file.write_text(template_content + "".join(blocks), encoding="utf-8")
    print(f"[OK] 已生成：{out_file}")

if __name__ == "__main__":
    main()
