"""
脚本名称: HTML 到 Markdown 转换器 (html_to_md.py)

功能描述:
    这是一个强大的网页内容抓取和转换工具。它能够从指定的 URL 获取网页内容，
    智能提取主要文章内容，并将其转换为干净的 Markdown 格式。
    转换后的 Markdown 文件会包含 YAML Front Matter，用于知识管理，
    并支持保存和重用登录会话，以便访问需要认证的网站（例如《华尔街日报》）。
    脚本可以处理单个 URL，也可以从文件中读取多个 URL 进行批量处理。

使用方法:
    1.  **转换单个 URL**:
        `python html_to_md.py "https://example.com/article"`
        -   可选参数 `-o` 或 `--output` 指定输出目录或完整文件名。
            例如: `python html_to_md.py "https://example.com/article" -o /path/to/output/`
            或 `python html_to_md.py "https://example.com/article" -o /path/to/output/my_article.md`

    2.  **从包含多个 URL 的文件转换**:
        `python html_to_md.py /path/to/your/links.txt`
        -   `links.txt` 文件中每行一个 URL。

    3.  **启动交互式登录流程并保存会话状态**:
        `python html_to_md.py --login wsj`
        -   这会打开一个浏览器窗口，让你手动登录。登录成功后，会话状态将保存到 `.env` 中配置的路径。

配置:
    -   **WSJ 登录状态路径**: 如果需要保存《华尔街日报》的登录状态，请在 `.env` 文件中设置
        `WSJ_AUTH_STATE_PATH` 环境变量，例如: `WSJ_AUTH_STATE_PATH="/path/to/your/wsj_auth_state.json"`

依赖:
    -   `playwright` (需要额外运行 `playwright install` 安装浏览器驱动)
    -   `beautifulsoup4`
    -   `markdownify`
    -   `readability-lxml`
    -   `html5lib`
    -   `python-dotenv`
    -   `asyncio`
    -   `argparse`
    -   `os`, `re`, `datetime`, `json`, `random`, `urllib.parse` (Python 内置库)
"""


# 导入我们需要的库
import asyncio  # 导入 asyncio 库，因为 Playwright 是基于异步 I/O 的，需要它来运行
import argparse # 导入 argparse 库以处理命令行参数
from playwright.async_api import async_playwright # 从 playwright 库中导入异步 API
from bs4 import BeautifulSoup # 导入 BeautifulSoup 用于解析 HTML
from markdownify import markdownify # 导入 markdownify 用于将 HTML 转为 Markdown
import os # 导入 os 库，用于处理文件路径
import re # 导入 re 库，用于正则表达式操作，以净化文件名
from bs4.element import Tag # 导入 Tag 类型用于类型提示
from datetime import datetime # 导入 datetime 用于获取当前时间
import json # 导入 json 库，用于解析 JSON-LD 数据
import random # 导入 random 库，用于生成随机等待时间
from readability import Document # 导入 readability 库，用于智能提取文章正文
from urllib.parse import urljoin # 导入 urljoin 用于处理相对 URL 路径

from dotenv import load_dotenv

load_dotenv() # 在所有代码之前，运行这个函数，它会自动加载.env文件

# --- 全局常量 ---
# 定义一个常量字符串，用于在 Front Matter 之后、正文之前插入的总结提炼模板
SUMMARY_TEMPLATE = "\n# 总结提炼\n\n\n\n---\n\n"


# --- 1. 配置浏览器上下文 ---
async def _setup_browser_context(browser, url):
    """
    根据 URL 配置并返回一个合适的浏览器上下文（BrowserContext）。
    目前主要用于为特定网站（如华尔街日报）加载登录 Cookies。
    :param browser: 当前的 Playwright 浏览器实例。
    :param url: 目标网页的 URL。
    :return: 一个配置好的、全新的浏览器上下文对象。
    """
    # 定义一个标准的、真实的 User-Agent
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    # 定义一个常见的浏览器视口大小和语言，以完善浏览器指纹
    viewport = {'width': 1920, 'height': 1080}
    locale = 'en-US'
    
    # 检查是否为 wsj.com 的链接，并尝试加载已保存的会话状态
    if "wsj.com" in url:
        auth_state_path = os.environ.get('WSJ_AUTH_STATE_PATH')
        if auth_state_path and os.path.exists(auth_state_path):
            print(f"💡 检测到 WSJ 链接，正在从 '{auth_state_path}' 加载会话状态...")
            try:
                # 基于已保存的会话状态文件创建上下文，这将恢复登录状态
                context = await browser.new_context(
                    user_agent=user_agent,
                    storage_state=auth_state_path,
                    viewport=viewport,
                    locale=locale
                )
                print("   ✅ 会话状态加载成功！")
                return context
            except Exception as e:
                print(f"   ❌ 加载会话状态时发生错误: {e}。将以未登录状态继续。")
    
    # 如果不匹配任何特殊规则（WSJ网址），或加载失败，则创建一个新的、干净的上下文
    print("   - 未匹配到特殊规则或加载状态失败，创建新的干净上下文。")
    context = await browser.new_context(
        user_agent=user_agent,
        viewport=viewport,
        locale=locale
    )
    return context

# --- 2. 使用playwright抓取HTML内容 ---
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
            
            # 调用辅助函数来获取一个配置好的浏览器上下文
            context = await _setup_browser_context(browser, url)

            # 我们直接从配置好的 context 创建新页面
            page = await context.new_page()
            print(f"🌍 正在导航到: {url}")

            # 访问我们想要抓取的 URL，并等待页面加载完成
            # await 关键字表示“等待这个操作完成再继续”
            # 增加 timeout 参数，将默认的30秒超时延长到60秒 (60000毫秒)
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            print("✅ 页面加载完成")

            # --- 新增：处理 Cookie 同意弹窗 ---
            print("🔎 正在检查并处理 Cookie 同意弹窗...")
            # 定义一个包含多种常见“同意”按钮文本和选择器的列表
            accept_selectors = [
                '#onetrust-accept-btn-handler',  # OneTrust 平台的标准 ID
                'button:has-text("Accept All")',
                'button:has-text("I Accept")',
                'button:has-text("Agree")',
                'button:has-text("Accept")',
            ]
            # 将所有选择器合并为一个，Playwright 会尝试匹配第一个出现的元素
            combined_selector = " , ".join(accept_selectors)
            try:
                # 尝试在 5 秒内找到并点击按钮。如果找不到，会抛出 TimeoutError。
                await page.locator(combined_selector).first().click(timeout=5000)
                print("   ✅ 已点击 Cookie 同意按钮。")
            except Exception:
                # 如果在超时时间内找不到按钮，或发生其他错误，则静默失败并继续。
                # 这样做是安全的，因为大多数情况下弹窗可能不存在。
                print("   - 未找到或无需处理 Cookie 同意弹窗。")

            # --- 新增：模拟人类浏览行为 ---
            print("🚶 正在模拟人类浏览行为...")
            # 1. 模拟页面滚动，以触发懒加载内容并使行为更逼真
            await page.evaluate("""
                async () => {
                    const distance = 100; // 每次滚动的距离
                    const delay = 100;    // 每次滚动后的延迟

                    // --- 新增：健壮的滚动退出机制，防止无限循环 ---
                    const maxScrolls = 100;      // 1. 设置最大滚动次数，作为硬性退出条件
                    let scrolls = 0;
                    let lastScrollY = -1;
                    let stuckCount = 0;
                    const maxStuckCount = 5; // 2. 如果连续5次滚动位置不变，则认为到达底部

                    while (scrolls < maxScrolls && stuckCount < maxStuckCount) {
                        const currentScrollY = window.scrollY;
                        window.scrollBy(0, distance);
                        await new Promise(resolve => setTimeout(resolve, delay));
                        scrolls++;

                        // 检查滚动位置是否变化
                        if (window.scrollY === currentScrollY) {
                            stuckCount++;
                        } else {
                            stuckCount = 0; // 如果滚动了，就重置计数器
                        }

                        // 这是一个额外的、快速退出的条件，如果已到达文档底部则立即停止
                        if (window.scrollY + window.innerHeight >= document.body.scrollHeight) {
                            break;
                        }
                    }
                }
            """)
            print("   - 页面已滚动到底部。")
            # 2. 在抓取内容前随机等待一段时间
            short_wait = random.uniform(2, 5)
            print(f"   - 随机等待 {short_wait:.2f} 秒...")
            await asyncio.sleep(short_wait)

            # 获取当前页面的完整 HTML 内容（也就是html_content）
            html_content = await page.content()
            print("📄 已获取页面 HTML 内容")

            await context.close() # 关闭上下文
            # 操作完成后，关闭浏览器
            await browser.close()
            print("✅ 浏览器已关闭")
            return html_content
        except Exception as e:
            print(f"❌ 在使用 Playwright 抓取网页时发生错误: {e}")
            return None


# --- 3. 提取通用元数据 ---
def _extract_head_metadata(soup: BeautifulSoup) -> dict:
    """从 HTML 的 <head> 部分提取通用的元数据。"""
    metadata = {}
    # 定义元数据提取规则：(元数据键名, CSS选择器, 属性名)
    rules = [
        ('description', 'meta[name="description"]', 'content'),
        ('description', 'meta[property="og:description"]', 'content'),
        ('site_name', 'meta[property="og:site_name"]', 'content'),
    ]

    for key, selector, attr in rules:
        # 如果这个元数据还没被找到，就尝试查找
        if key not in metadata or not metadata[key]:
            element = soup.select_one(selector)
            # 增加健壮性检查：确保 element 存在，并且对应的属性也存在
            if element:
                value = element.get(attr)
                if value:
                    # 使用 str() 将获取到的值（可能是字符串或列表）显式转换为字符串，然后再调用 strip()
                    metadata[key] = str(value).strip()
    return metadata

# --- 4. 处理微信公众号HTML ---
def _process_wechat_html(soup: BeautifulSoup) -> tuple[Tag | None, dict]:
    """专门处理微信公众号文章的HTML，提取元数据和正文。"""
    print("💡 检测到微信公众号文章，启动专用处理器...")
    # 首先，尝试从 head 中提取通用元数据作为基础
    metadata = _extract_head_metadata(soup)
    
    # 然后，使用微信特定的选择器来覆盖和补充元数据，因为它们更准确
    title_element = soup.select_one('h1#activity-name')
    if title_element:
        metadata["title"] = title_element.get_text(strip=True)
        print(f"   ✒️ 成功提取微信标题: {metadata['title']}")

    author_element = soup.select_one('#js_name')
    if author_element:
        metadata["author"] = author_element.get_text(strip=True)
        print(f"   👤 成功提取微信作者: {metadata['author']}")

    published_element = soup.select_one('em#publish_time')
    if published_element:
        metadata["published"] = published_element.get_text(strip=True)
        print(f"   📅 成功提取微信发布日期: {metadata['published']}")

    # 提取正文内容
    wechat_selector = "#js_content"
    content_element = soup.select_one(wechat_selector)
    if content_element:
        print(f"   ✅ 成功匹配到微信正文内容: '{wechat_selector}'")
    else:
        print(f"   ❌ 未能通过 '{wechat_selector}' 找到内容。")
    return content_element, metadata

# --- 5. 处理通用HTML ---
def _process_generic_html(soup: BeautifulSoup, html_content: str) -> tuple[Tag | None, dict]:
    """处理通用网页的HTML，通过多种策略提取元数据和正文。"""
    print("🤖 未匹配到特定规则，启动通用处理器...")
    # 首先，尝试从 head 中提取通用元数据作为基础
    metadata = _extract_head_metadata(soup)
    content_element = None

    # --- 新增策略1: 解析 JSON-LD 结构化数据 (最高优先级) ---
    # 许多现代网站使用 JSON-LD 来提供机器可读的元数据，这通常是最准确的信息来源。
    json_ld_scripts = soup.find_all('script', type='application/ld+json')
    for script in json_ld_scripts:
        # 检查 script 标签内是否有内容，因为 .string 在标签为空或包含子标签时可能返回 None
        if script.string:
            try:
                json_data = json.loads(script.string)

                # JSON-LD 数据可以是单个字典，也可以是字典列表。我们统一处理。
                items_to_process = []
                if isinstance(json_data, list):
                    items_to_process.extend(json_data)
                elif isinstance(json_data, dict):
                    items_to_process.append(json_data)

                # 遍历所有找到的 JSON-LD 项目
                for item in items_to_process:
                    if not isinstance(item, dict):
                        continue

                    # 查找并提取发布日期
                    if not metadata.get("published") and item.get("datePublished"):
                        metadata["published"] = item["datePublished"]
                        print(f"   📊 从 JSON-LD 提取到发布日期: {metadata['published']}")
                    
                    # 查找并提取作者信息
                    if not metadata.get("author") and item.get("author"):
                        author_data = item["author"]
                        if isinstance(author_data, dict) and author_data.get("name"):
                            metadata["author"] = author_data["name"]
                        elif isinstance(author_data, list) and len(author_data) > 0 and author_data[0].get("name"):
                            metadata["author"] = author_data[0]["name"]
                        if metadata.get("author"):
                            print(f"   📊 从 JSON-LD 提取到作者: {metadata['author']}")

            except (json.JSONDecodeError, TypeError):
                # 如果脚本内容不是有效的 JSON，则静默失败并继续
                # TypeError 也会被捕获，以防万一，尽管我们已经检查了 script.string
                continue

    # 策略2: 尝试预设的通用选择器列表来定位正文
    candidate_selectors = [
        'article', 'main', '#content', '#main-content', '#main',
        '.post-body', '.entry-content', '.article-body',
    ]
    for candidate in candidate_selectors:
        element = soup.select_one(candidate)
        if element:
            print(f"   ✅ 通过预设规则成功匹配到内容: '{candidate}'")
            content_element = element
            # 在通用检测流程中，尝试获取页面的 <title> 作为标题
            # 仅当 metadata 中还没有标题时，才使用 <title> 标签作为备用
            if not metadata.get("title") and soup.title and soup.title.string:
                metadata["title"] = soup.title.string.strip()
            break
    
    # 策略3: 如果预设规则失败，则使用 Readability 算法作为最终的正文提取尝试
    if not content_element:
        print("   - 预设规则失败，尝试使用 Readability 算法进行智能提取...")
        try:
            doc = Document(html_content)
            # Readability 提取的标题和作者优先级更高，覆盖从 head 中获取的
            if not metadata.get("title"):
                metadata["title"] = doc.title() 
            # 仅当通过其他方式都未找到作者时，才使用 Readability 的 byline 作为备用
            if not metadata.get("author"):
                metadata["author"] = getattr(doc, 'byline', '') 
            main_content_html = doc.summary()
            content_element = BeautifulSoup(main_content_html, "html5lib")
            print("   ✅ Readability 算法成功提取到主要内容！")
        except Exception as e:
            print(f"   ❌ Readability 算法提取失败: {e}")

    return content_element, metadata


# --- 6. 内容后处理 ---
def _post_process_content(content_element: Tag, url: str):
    """对提取出的内容进行后处理，主要是修正图片URL。"""
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
        if 'src' in img.attrs:
            # 先将属性值取出，并使用 str() 确保其为字符串类型，以防止 BeautifulSoup 返回列表或其他类型导致错误
            src_value = str(img['src'])
            # 对转换后的字符串进行判断和处理
            if not src_value.startswith(('http://', 'https://')):
            # 使用 urljoin 将相对路径与页面的基础 URL 组合，生成绝对路径
            # urljoin 能够智能处理各种相对路径情况
                img['src'] = urljoin(url, src_value)
            # print(f"   💡 修正图片URL: {img['src']}") # 调试用，可以取消注释查看修正过程


# --- 7. 调度HTML转换 ---
def convert_html_to_markdown(html_content: str, url: str) -> tuple[str, dict] | None:
    """
    从 HTML 字符串中提取特定内容并转换为 Markdown。这是一个调度函数。
    :param html_content: 包含完整网页的 HTML 字符串。
    :param url: 原始网页的 URL，用于平台特定规则的判断。
    :return: 成功时返回一个包含 (Markdown 字符串, 元数据字典) 的元组，失败时返回 None。
    """
    print("\n🔍 开始解析内容...")
    # BeautifulSoup 接收前面生成的网页字符串，解析生成内部的树状数据结构
    # “html.parser”是解析器，还有lxml、html5lib
    # 这个 soup 对象现在是整个 HTML 文档的 Pythonic 表示,。
    # 你可以把它看作一个复杂的、嵌套的 Python 对象，它完整地映射了原始 HTML 的标签、属性和文本内容。
    soup = BeautifulSoup(html_content, "html5lib")

    content_element = None
    # 初始化一个空的元数据字典
    metadata = {}

    # --- 调度中心 ---
    # 根据 URL 判断应该使用哪个处理器
    if "mp.weixin.qq.com" in url:
        content_element, metadata = _process_wechat_html(soup)
    else:
        content_element, metadata = _process_generic_html(soup, html_content)
    
    # 如果所有方法都未能找到内容，则退出
    if not content_element:
        print("❌ 所有自动检测方法均失败，未能找到主要内容区域。")
        return None
    
    print("✅ 成功找到内容元素")
    
    # 对提取出的内容进行后处理（例如修正图片链接）
    _post_process_content(content_element, url)

    # 将 HTML 元素转换为 Markdown文档字符串，markdownify()函数
    # heading_style控制 markdownify 在将 HTML 标题标签（如 <h1>, <h2>, <h3> 等）转换为 Markdown 标题时所使用的样式。
    # strip=['a'] 参数可以在转换前移除所有<a>标签，以获得更干净的文本。
    markdown_text = markdownify(str(content_element), heading_style="ATX", strip=['a'])
    print(f"🔄 已将 HTML (标题: {metadata.get('title', 'N/A')}) 转换为 Markdown")
    return markdown_text, metadata

# --- 8. 创建Front Matter ---
def _create_front_matter(metadata: dict, url: str) -> str:
    """根据提取的元数据生成 YAML Front Matter 字符串。"""
    # 使用 isoformat() 获取符合 ISO 8601 标准的日期时间字符串
    created_time = datetime.now().isoformat()

    # 构建 Front Matter 字典
    front_matter_data = {
        "note_type": "文献笔记",
        "content_type": "新闻报道",
        "created": created_time,
        "published": metadata.get("published", ""),
        "source": url,
        "author": metadata.get("author", ""),
        "description": metadata.get("description", ""),
        "site_name": metadata.get("site_name", ""),
    }

    # 将字典格式化为 YAML 字符串
    yaml_lines = ["---"]
    for key, value in front_matter_data.items():
        yaml_lines.append(f"{key}: {value}")
    yaml_lines.append("---")

    return "\n".join(yaml_lines)


# --- 9. 保存内容到文件 ---
def save_to_file(content: str, user_specified_path: str | None, page_title: str):
    """
    将字符串内容保存到指定路径的文件中。
    :param content: 要保存的字符串内容。
    :param user_specified_path: 用户通过命令行指定的输出路径，可能为 None。
    :param page_title: 从网页中提取的标题，用于在用户未指定路径时生成文件名。
    """
    try:
        # 将净化文件名的逻辑内联到这里：移除文件名中的非法字符，然后添加 .md 后缀
        sanitized_title_filename = re.sub(r'[\\/*?:"<>|]', "", str(page_title)).strip() + ".md"

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

# --- 10. 从文件提取URL ---
def _extract_urls_from_file(file_path: str) -> list[str]:
    """
    从给定的文件中读取内容，并使用正则表达式提取所有 URL。
    :param file_path: 包含 URL 的文件路径。
    :return: 一个包含所有找到的 URL 的列表。
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        # 使用正则表达式查找所有 http/https 链接
        urls = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', content)
        # 使用 set 去重，然后转回 list
        unique_urls = list(set(urls))
        print(f"📄 从文件 '{file_path}' 中找到 {len(unique_urls)} 个唯一链接。")
        return unique_urls
    except FileNotFoundError:
        print(f"❌ 文件未找到: {file_path}")
        return []
    except Exception as e:
        print(f"❌ 读取文件时发生错误: {e}")
        return []

# --- 11. 处理交互式登录 ---
async def handle_login(site: str):
    """
    处理特定网站的交互式登录流程，并保存会话状态。
    :param site: 网站的标识符，例如 'wsj'。
    """
    site_configs = {
        'wsj': {
            'login_url': 'https://www.wsj.com/login',
            'env_var': 'WSJ_AUTH_STATE_PATH'
        }
        # 未来可以添加其他网站的配置
    }

    if site not in site_configs:
        print(f"❌ 不支持的登录网站: '{site}'。目前只支持 'wsj'。")
        return

    config = site_configs[site]
    auth_file_path = os.environ.get(config['env_var'])

    if not auth_file_path:
        print(f"❌ 错误: 请先设置环境变量 '{config['env_var']}' 来指定会话状态文件的保存路径。")
        return

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False) # 必须以非无头模式启动
        context = await browser.new_context()
        page = await context.new_page()

        # --- 核心修改：注入脚本以隐藏自动化特征 ---
        # 某些网站会检测 navigator.webdriver 属性来判断是否为自动化浏览器。
        # 我们在页面加载任何脚本之前，通过 add_init_script 将这个属性的值伪装成 false。
        await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => false})")

        await page.goto(config['login_url'])
        
        print("\n" + "="*50)
        print("🚀 交互式登录流程已启动 🚀")
        print(f"请在弹出的浏览器窗口中手动完成 '{site.upper()}' 的登录。")
        print("登录成功后，请不要关闭浏览器，回到这里按下 'Enter' 键继续...")
        print("="*50 + "\n")
        
        input() # 等待用户按 Enter

        # 保存完整的会话状态到指定文件
        await context.storage_state(path=auth_file_path)
        print(f"✅ 会话状态已成功保存到: {auth_file_path}")

        await browser.close()


# --- 12. 主程序入口 ---
async def main():
    """
    程序的主异步入口，负责编排整个抓取、转换和保存的工作流。
    """
    # 使用 argparse 解析命令行参数
    parser = argparse.ArgumentParser(description="一个通用的网页内容抓取并转换为 Markdown 的工具。")
    parser.add_argument("input_source", nargs='?', default=None, help="要抓取的目标网页 URL，或包含多个 URL 的文件路径。")
    # 修改-o参数，使其默认值为None，以便我们判断用户是否真的输入了它
    parser.add_argument("-o", "--output", help="输出的 Markdown 文件路径。如果未提供，将根据网页标题自动生成。")
    parser.add_argument("--login", help="启动交互式登录流程以保存特定网站的会话状态。例如: --login wsj")
    args = parser.parse_args()

    # --- 模式调度 ---
    if args.login:
        # 如果用户指定了 --login 参数，则执行登录流程并退出
        await handle_login(args.login)
        return

    if not args.input_source:
        parser.error("错误: 必须提供一个 URL 或文件路径作为输入源，或者使用 --login 选项。")
        return

    urls_to_process = []
    # 判断输入是文件还是 URL
    if os.path.isfile(args.input_source):
        urls_to_process = _extract_urls_from_file(args.input_source)
    else:
        # 如果不是一个有效的文件路径，则假定它是一个 URL
        urls_to_process.append(args.input_source)

    for i, url in enumerate(urls_to_process):
        print(f"\n--- 正在处理第 {i+1}/{len(urls_to_process)} 个链接: {url} ---")
        # 1. 提取
        html_content = await fetch_html_from_url(url)
        if not html_content:
            continue # 如果当前 URL 失败，则跳过并继续处理下一个

        # 2. 转换
        conversion_result = convert_html_to_markdown(html_content, url)
        if not conversion_result:
            continue
        
        markdown_text, metadata = conversion_result

        # 2.5. 生成 Front Matter
        front_matter = _create_front_matter(metadata, url)

        # 将 Front Matter 和正文内容拼接起来
        final_content = f"{front_matter}{SUMMARY_TEMPLATE}{markdown_text}"

        # 3. 保存
        save_to_file(final_content, args.output, metadata.get("title", "Untitled"))
        
        # --- 新增：在处理多个链接时，增加一个较长的随机等待，以避免访问频率过快 ---
        if len(urls_to_process) > 1 and i < len(urls_to_process) - 1:
            long_wait = random.uniform(10, 30)
            print(f"\n⏳ 批量处理间隔，随机等待 {long_wait:.2f} 秒...")
            await asyncio.sleep(long_wait)

if __name__ == "__main__":
    # 因为我们的核心函数是异步的，所以需要使用 asyncio.run() 来启动它
    asyncio.run(main())
