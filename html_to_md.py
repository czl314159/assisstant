# 导入我们需要的库
import asyncio  # 导入 asyncio 库，因为 Playwright 是基于异步 I/O 的，需要它来运行
from playwright.async_api import async_playwright # 从 playwright 库中导入异步 API
from bs4 import BeautifulSoup # 导入 BeautifulSoup 用于解析 HTML
from markdownify import markdownify # 导入 markdownify 用于将 HTML 转为 Markdown
import os # 导入 os 库，用于处理文件路径

# --- 1. 配置区域 ---
# 在这里修改你要抓取的网址、内容选择器和保存路径

# 目标网页的 URL
TARGET_URL = "https://playwright.dev/python/docs/intro" 
# 内容所在的 CSS 选择器 (这是一个例子，你需要根据目标网页的结构进行修改)
# 如何找到它？在浏览器中右键点击你想要抓取的内容，选择“检查”，然后在开发者工具中找到最能代表这块内容的标签和它的 id 或 class。
# 比如，如果内容在一个 <article> 标签里，就可以用 "article"
# 如果在一个 <div id="main-content"> 里，就可以用 "#main-content"
# 如果在一个 <div class="post-body"> 里，就可以用 ".post-body"
CONTENT_SELECTOR = "article"
# 希望保存 Markdown 文件的路径
OUTPUT_FILE_PATH = "output.md"

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

            # 在浏览器中创建一个新的页面（Page对象）
            page = await browser.new_page()
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

def convert_html_to_markdown(html_content: str, selector: str) -> str | None:
    """
    从 HTML 字符串中提取特定内容并转换为 Markdown。
    :param html_content: 包含完整网页的 HTML 字符串。
    :param selector: 用于定位内容的 CSS 选择器。
    :return: 成功时返回 Markdown 字符串，失败时返回 None。
    """
    
    print("\n🔍 开始使用 BeautifulSoup 解析内容...")
    # BeautifulSoup 接收前面生成的网页字符串，解析生成内部的树状数据结构
    # “html.parser”是解析器，还有lxml、html5lib
    # 这个 soup 对象现在是整个 HTML 文档的 Pythonic 表示,。
    # 你可以把它看作一个复杂的、嵌套的 Python 对象，它完整地映射了原始 HTML 的标签、属性和文本内容。
    soup = BeautifulSoup(html_content, "html5lib")

    # 在已经解析的 HTML 文档中，根据一个 CSS 选择器来查找并返回第一个匹配的 HTML 元素。
    # bs4.element.Tag 对象：content_element 将是一个代表该 HTML 标签及其所有子内容的 Tag 对象。
    content_element = soup.select_one(selector)
    
    if not content_element:
        print(f"❌ 未能找到匹配选择器 '{selector}' 的内容。请检查选择器是否正确，或网页结构是否已改变。")
        return None
    print(f"✅ 成功找到内容元素 (匹配选择器: '{selector}')")

    # 将 HTML 元素转换为 Markdown文档字符串，markdownify()函数
    # heading_style控制 markdownify 在将 HTML 标题标签（如 <h1>, <h2>, <h3> 等）转换为 Markdown 标题时所使用的样式。
    # strip=['a'] 参数可以在转换前移除所有<a>标签，以获得更干净的文本。
    markdown_text = markdownify(str(content_element), heading_style="ATX", strip=['a'])
    print("🔄 已将 HTML 转换为 Markdown")
    return markdown_text

def save_to_file(content: str, output_path: str):
    """
    将字符串内容保存到指定路径的文件中。
    :param content: 要保存的字符串内容。
    :param output_path: 目标文件路径。
    """
    try:
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"💾 文件已成功保存到: {os.path.abspath(output_path)}")
    except Exception as e:
        print(f"❌ 保存文件时发生错误: {e}")

# --- 3. 主流程编排函数 ---

async def main(url, selector, output_path):
    """
    程序的主异步入口，负责编排整个抓取、转换和保存的工作流。
    """
    # 1. 提取
    html_content = await fetch_html_from_url(url)
    if not html_content:
        return

    # 2. 转换
    markdown_text = convert_html_to_markdown(html_content, selector)
    if not markdown_text:
        return

    # 3. 保存
    save_to_file(markdown_text, output_path)

# --- 4. 程序主入口 ---

if __name__ == "__main__":
    # 因为我们的核心函数是异步的，所以需要使用 asyncio.run() 来启动它
    asyncio.run(main(TARGET_URL, CONTENT_SELECTOR, OUTPUT_FILE_PATH))
