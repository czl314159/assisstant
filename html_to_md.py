
# 导入我们需要的库
import asyncio  # 导入 asyncio 库，因为 Playwright 是基于异步 I/O 的，需要它来运行
import argparse # 导入 argparse 库以处理命令行参数
from playwright.async_api import async_playwright # 从 playwright 库中导入异步 API
from bs4 import BeautifulSoup # 导入 BeautifulSoup 用于解析 HTML
from markdownify import markdownify # 导入 markdownify 用于将 HTML 转为 Markdown
import os # 导入 os 库，用于处理文件路径
import re # 导入 re 库，用于正则表达式操作，以净化文件名
from urllib.parse import urljoin # 导入 urljoin 用于处理相对 URL 路径

# --- 2. 抓取HTML内容 ---

async def fetch_html_from_url(url: str) -> str | None:
    """
    使用 Playwright 异步抓取指定 URL 的 HTML 内容。
    :param url: 目标网页的 URL。
    :return: 成功时返回 HTML 字符串，失败时返回 None。
    """
    print("🚀 脚本启动，准备连接 Playwright...")
    
    # 通过async with 语句来管理 Playwright 的生命周期，确保浏览器被正确关闭
    # async表示代码可以异步处理，所谓异步，是指可在执行中暂停，等待资源到位再重启
    # with表示上下文管理器，所谓上下文管理器，是指自动处理相关后台资源的开启和释放，如文件、网络连接等
    # async_playwright()是一个函数，启动相关资源，返回一个Playwright 主控制对象给p
    async with async_playwright() as p:
        try:
            # 异步（可await）启动一个 Chromium 浏览器实例（BrowserType对象）。headless=True 表示在后台运行，不显示浏览器窗口。
            # 你也可以换成 p.firefox.launch() 或 p.webkit.launch()
            # 该方法返回一个Browser对象，赋值给browser
            browser = await p.chromium.launch(headless=True)
            print("✅ 浏览器已启动")

            # 在浏览器中创建一个新的页面（Page对象），并设置一个真实的 User-Agent 来模拟普通用户，防止基础的反爬虫检测。
            # user_agent 是 browser.new_page 方法的一个关键字参数（keyword argument）。
            page = await browser.new_page(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
            )
            print("✅ 页面已创建，并设置了自定义 User-Agent")
            print(f"🌍 正在导航到: {url}")

            # 访问我们想要抓取的 URL，并等待页面加载完成
            # await 关键字表示“等待这个操作完成再继续”
            # 增加 timeout 参数，将默认的30秒超时延长到60秒 (60000毫秒)
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            print("✅ 页面加载完成")

            # 获取当前页面的完整 HTML 内容（也就是html_content）
            html_content = await page.content()
            print("📄 已获取页面 HTML 内容")

            # 操作完成后，关闭浏览器
            await browser.close()
            print("✅ 浏览器已关闭")
            return html_content
        except Exception as e:
            print(f"❌ 在使用 Playwright 抓取网页时发生错误: {e}")
            return None

# --- 2. 转化HTML内容为MD文件 ---

def convert_html_to_markdown(html_content: str, url: str) -> tuple[str, str] | None:
    """
    从 HTML 字符串中提取特定内容并转换为 Markdown。
    :param html_content: 包含完整网页的 HTML 字符串。
    :param url: 原始网页的 URL，用于平台特定规则的判断。
    :return: 成功时返回一个包含 (Markdown 字符串, 页面标题) 的元组，失败时返回 None。
    """
    
    print("\n🔍 开始解析内容...")
    # BeautifulSoup 接收前面生成的网页字符串，解析生成内部的树状数据结构
    # “html.parser”是解析器，还有lxml、html5lib
    # 这个 soup 对象现在是整个 HTML 文档的 Pythonic 表示,。
    # 你可以把它看作一个复杂的、嵌套的 Python 对象，它完整地映射了原始 HTML 的标签、属性和文本内容。
    soup = BeautifulSoup(html_content, "html5lib")

    # 初始化网页标题和内容元素变量
    page_title = "Untitled" # 默认标题
    # 初始化内容元素变量
    content_element = None

    # 步骤 1: 检查是否有平台特定规则（例如微信公众号）
    if "mp.weixin.qq.com" in url:
        print("💡 检测到微信公众号文章，尝试使用专用选择器 '#js_content'...")
        wechat_selector = "#js_content"
        content_element = soup.select_one(wechat_selector)
        if content_element:
            print(f"   ✅ 成功匹配到内容: '{wechat_selector}'") # 仍然打印匹配到的选择器，但不再记录到变量
        else:
            # 如果微信专用选择器也失败了（虽然不太可能），则打印提示并继续进行通用检测
            print(f"   ❌ 未能通过 '{wechat_selector}' 找到内容，将继续通用检测...")

    # 步骤 2: 如果以上方法都未成功，则启动通用的预设列表进行自动检测
    if not content_element:
        print("🤖 启动通用预设规则进行检测...")
        # 定义一个高质量的候选选择器列表，按可能性从高到低排序
        candidate_selectors = [
            'article', 'main', '#content', '#main-content', '#main',
            '.post-body', '.entry-content', '.article-body',
        ]
        for candidate in candidate_selectors:
            # 在通用检测流程中，尝试获取页面的 <title> 作为标题
            if soup.title and soup.title.string:
                page_title = soup.title.string.strip()

            print(f"   尝试候选选择器: '{candidate}'...")
            content_element = soup.select_one(candidate)
            if content_element: # 仍然打印匹配到的选择器，但不再记录到变量
                print(f"   ✅ 成功匹配到内容: '{candidate}'") 
                break # 找到后立即跳出循环
    
    # 步骤 3: 如果所有自动检测都失败，则提示并退出
    if not content_element:
        print("❌ 自动检测失败，未能找到主要内容区域。")
        return None

    print("✅ 成功找到内容元素") # 不再显示匹配的选择器

    # --- 新增：处理图片URL，确保它们是绝对路径并处理懒加载 ---
    # 遍历所有 img 标签
    for img in content_element.find_all('img'):
        # 1. 处理懒加载属性：检查是否有 data-src 或 data-original 等属性，并将其值赋给 src
        # 微信公众号文章通常使用 data-src 来存储真实的图片 URL
        if 'data-src' in img.attrs:
            # 如果 data-src 存在，就用它的值来更新 src 属性
            img['src'] = img['data-src']
            # 移除 data-src 属性，避免冗余，并且让 HTML 更“干净”
            del img['data-src'] 
        elif 'data-original' in img.attrs: # 某些网站可能使用 data-original
            img['src'] = img['data-original']
            del img['data-original']
        # 可以根据需要添加其他常见的懒加载属性，例如 _src 等

        # 2. 确保 src 属性是绝对路径
        # 只有当 src 属性存在且不是绝对路径（即不以 http:// 或 https:// 开头）时才进行处理
        if 'src' in img.attrs and not img['src'].startswith(('http://', 'https://')):
            # 使用 urljoin 将相对路径与页面的基础 URL 组合，生成绝对路径
            # urljoin 能够智能处理各种相对路径情况
            img['src'] = urljoin(url, img['src'])
            # print(f"   💡 修正图片URL: {img['src']}") # 调试用，可以取消注释查看修正过程

    # --- 结束图片URL处理 ---

    # 将 HTML 元素转换为 Markdown文档字符串，markdownify()函数
    # heading_style控制 markdownify 在将 HTML 标题标签（如 <h1>, <h2>, <h3> 等）转换为 Markdown 标题时所使用的样式。
    # strip=['a'] 参数可以在转换前移除所有<a>标签，以获得更干净的文本。
    markdown_text = markdownify(str(content_element), heading_style="ATX", strip=['a'])
    print(f"🔄 已将 HTML (标题: {page_title}) 转换为 Markdown")
    return markdown_text, page_title

def save_to_file(content: str, user_specified_path: str | None, page_title: str):
    """
    将字符串内容保存到指定路径的文件中。
    :param content: 要保存的字符串内容。
    :param user_specified_path: 用户通过命令行指定的输出路径，可能为 None。
    :param page_title: 从网页中提取的标题，用于在用户未指定路径时生成文件名。
    """
    try:
        # 净化后的网页标题作为基础文件名
        sanitized_title_filename = sanitize_filename(page_title) + ".md"

        if user_specified_path: # 用户指定了 -o 参数
            # 判断用户指定的是一个目录还是一个完整的文件路径
            if os.path.isdir(user_specified_path) or user_specified_path.endswith(('/', '\\')):
                # 如果用户指定的是一个目录，则将标题作为文件名与目录组合
                output_path = os.path.join(user_specified_path, sanitized_title_filename)
            else:
                # 如果用户指定的是一个完整的文件路径（包含文件名），则直接使用
                output_path = user_specified_path
        else:
            # 用户未指定 -o 参数，则在当前目录使用标题作为文件名
            output_path = sanitized_title_filename

        # 确保输出目录存在
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # 使用 with open() 语句确保文件操作的安全性和资源的自动释放
        with open(output_path, "w", encoding="utf-8") as f: 
            f.write(content)
        print(f"💾 文件已成功保存到: {os.path.abspath(output_path)}") # 使用 os.path.abspath 获取绝对路径，让输出更明确
    except Exception as e:
        print(f"❌ 保存文件时发生错误: {e}")

def sanitize_filename(filename: str) -> str:
    """
    移除或替换文件名中的非法字符。
    :param filename: 原始文件名（通常是网页标题）。
    :return: 清理后可以安全用作文件名的字符串。
    """
    # 移除非法字符： \ / : * ? " < > |
    return re.sub(r'[\\/*?:"<>|]', "", filename).strip()

# --- 3. 主流程编排函数 ---

async def main():
    """
    程序的主异步入口，负责编排整个抓取、转换和保存的工作流。
    """
    # 使用 argparse 解析命令行参数
    parser = argparse.ArgumentParser(description="一个通用的网页内容抓取并转换为 Markdown 的工具。")
    parser.add_argument("url", help="要抓取的目标网页 URL。") # 位置参数，必需
    # 修改-o参数，使其默认值为None，以便我们判断用户是否真的输入了它
    parser.add_argument("-o", "--output", help="输出的 Markdown 文件路径。如果未提供，将根据网页标题自动生成。")
    args = parser.parse_args()

    # 1. 提取
    html_content = await fetch_html_from_url(args.url)
    if not html_content:
        return

    # 2. 转换
    conversion_result = convert_html_to_markdown(html_content, args.url) # 现在只传递 HTML 内容和 URL
    if not conversion_result:
        return
    
    markdown_text, page_title = conversion_result

    # 3. 保存
    save_to_file(markdown_text, args.output, page_title)

# --- 4. 程序主入口 ---

if __name__ == "__main__":
    # 因为我们的核心函数是异步的，所以需要使用 asyncio.run() 来启动它
    asyncio.run(main())
