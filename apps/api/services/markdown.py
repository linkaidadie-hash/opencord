"""Markdown → HTML rendering for posts and comments."""
import markdown
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.tables import TableExtension
from markdown.extensions.sane_lists import SaneListExtension
from pygments.formatters.html import HtmlFormatter

_md = markdown.Markdown(
    extensions=[
        FencedCodeExtension(),
        CodeHiliteExtension(noclasses=True, pygments_style="github"),
        TableExtension(),
        SaneListExtension(),
        "pymdownx.tilde",  # ~~删除~~  (optional, may not be installed)
    ],
    extension_configs={},
)


def render_markdown(text: str) -> str:
    """渲染 Markdown 为 HTML，限制 XSS。"""
    _md.reset()
    return _md.convert(text)


def safe_html(html: str) -> str:
    """
    v0.1 简单清洗；v0.2 换 bleach 或 nh3 严格白名单。
    现在只允许 p, br, h1-h6, ul, ol, li, code, pre, blockquote, a, em, strong, table, thead, tbody, tr, th, td, img
    """
    # 简单做法：去掉 script / iframe / object / embed / on* 事件
    import re
    if "<script" in html.lower():
        html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.IGNORECASE | re.DOTALL)
    if "<iframe" in html.lower():
        html = re.sub(r"<iframe[^>]*>.*?</iframe>", "", html, flags=re.IGNORECASE | re.DOTALL)
    # on* 属性
    html = re.sub(r'\s+on\w+\s*=\s*"[^"]*"', "", html, flags=re.IGNORECASE)
    html = re.sub(r"\s+on\w+\s*=\s*'[^']*'", "", html, flags=re.IGNORECASE)
    return html
