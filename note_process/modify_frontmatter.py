# 用法：修改指定文件夹中，符合条件（笔记属性键值对）的 Markdown 文件的 front matter 中的键值对
# 示例：python modify_frontmatter.py "D:\note" note_type 备查笔记 content_type 知识教程
# 示例说明：上述命令会修改note下，所有笔记属性 note_type 为 备查笔记 的 Markdown 文件，
# 将其 front matter 中的 content_type 键设置为 知识教程（若无该键则新增）


import sys
import pathlib #导入pathlib模块，用于处理文件路径
import re #导入正则表达式模块

if len(sys.argv) != 6:
    print("用法: python modify_frontmatter.py <目录> <匹配键> <匹配值> <目标键> <目标值>")
    print("示例: python modify_frontmatter.py D:\\note note_type 备查笔记 content_type 知识教程")
    sys.exit(1)

root      = pathlib.Path(sys.argv[1])
match_key = sys.argv[2]
match_val = sys.argv[3]
set_key   = sys.argv[4]
set_val   = sys.argv[5]

# 仅匹配文件开头的 front matter 块
FM = re.compile(r'^---\s*\r?\n(.*?)\r?\n---\s*', re.DOTALL | re.MULTILINE)

# 仅处理：<匹配键>: <匹配值> ；容忍引号
NOTE_OK = re.compile(
    rf'^{re.escape(match_key)}:\s*("?){re.escape(match_val)}\1\s*$',
    re.MULTILINE
)

# 匹配一整行目标键（可带缩进），提取旧值；保留原缩进
LINE_RE = re.compile(
    rf'^(?P<prefix>\s*){re.escape(set_key)}\s*:\s*(?P<value>.*?)\s*$',
    re.MULTILINE
)

def read_text(p: pathlib.Path):
    try:
        return p.read_text(encoding="utf-8-sig"), "utf-8-sig"
    except UnicodeDecodeError:
        return p.read_text(encoding="utf-8"), "utf-8"

def norm(v: str) -> str:
    # 去掉行内注释与引号、首尾空白
    v = v.split("#", 1)[0].strip()
    if (len(v) >= 2) and ((v[0] == v[-1]) and v[0] in ('"', "'")):
        v = v[1:-1]
    return v.strip()

updated = 0
for f in root.rglob("*.md"):
    text, enc = read_text(f)
    m = FM.search(text)
    if not m:
        continue

    fm = m.group(1)
    if not NOTE_OK.search(fm):
        continue

    mline = LINE_RE.search(fm)
    if mline:
        old = norm(mline.group("value"))
        if old == set_val:
            continue  # 值相同，跳过
        prefix = mline.group("prefix")
        fm_new = LINE_RE.sub(f"{prefix}{set_key}: {set_val}", fm, count=1)
    else:
        nl = "\r\n" if "\r\n" in fm else "\n"
        fm_new = fm + ("" if fm.endswith(nl) else nl) + f"{set_key}: {set_val}"

    new_text = text[:m.start(1)] + fm_new + text[m.end(1):]
    f.write_text(new_text, encoding=enc)
    updated += 1
    print(f"[OK] {f}")

print(f"\n完成：修改或新增 {updated} 个文件。")
