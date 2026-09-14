"""CTEXT 中国哲学书电子化计划适配器（ctext.org/zh）。

注意：该站点当前对程序化请求启用了 Cloudflare 人机验证，
程序会自动识别并提示【网站访问受限】；解析逻辑按站点公开结构实现。
"""
import re
import urllib.parse

from bs4 import BeautifulSoup

from adapters.base import BaseAdapter
from core.models import Book, Chapter, ParseError, SiteBlockedError

BASE = "https://ctext.org"


class CtextAdapter(BaseAdapter):
    name = "CTEXT"
    domain = "ctext.org"

    # ---- 搜索 ----
    def search_book(self, keyword: str) -> list[Book]:
        url = f"{BASE}/searchbooks.pl"
        resp = self.http.get(url, params={"if": "gb", "searchu": keyword}, encoding="utf-8")
        if not resp.text.strip():
            raise SiteBlockedError("网站访问受限，请稍后重试")
        soup = BeautifulSoup(resp.text, "html.parser")
        books: list[Book] = []
        for a in soup.select("a[href]"):
            href = a["href"]
            m = re.match(r"^/zh/([^/?#]+)$", href)
            if not m:
                continue
            title = a.get_text(" ", strip=True)
            if not title:
                continue
            books.append(Book(
                title=title, source=self.name,
                index_url=f"{BASE}{href}",
                description="中国哲学书电子化计划",
            ))
        # 去重
        seen: set[str] = set()
        unique: list[Book] = []
        for b in books:
            if b.index_url in seen:
                continue
            seen.add(b.index_url)
            unique.append(b)
        return unique

    # ---- 目录 ----
    def get_chapter_list(self, book_index_url: str) -> list[Chapter]:
        resp = self.http.get(book_index_url, encoding="utf-8")
        if not resp.text.strip():
            raise SiteBlockedError("网站访问受限，请稍后重试")
        soup = BeautifulSoup(resp.text, "html.parser")
        # 目录通常在 #menu 内；退而求其次解析所有内部链接
        menu = soup.select_one("#menu")
        if menu is None:
            menu = soup
        base_path = urllib.parse.urlparse(book_index_url).path  # 形如 /zh/三国演义
        chapters: list[Chapter] = []
        seen: set[str] = set()
        for a in menu.select("a[href]"):
            href = a["href"]
            if "://" in href:
                continue
            full = BASE + href
            if full in seen:
                continue
            m = re.match(r"^/zh/[^/]+/([^/?#]+)", href)
            if not m:
                continue
            title = a.get_text(" ", strip=True)
            if not title or title in ("目录", "上一章", "下一章"):
                continue
            seen.add(full)
            chapters.append(Chapter(title=title, url=full))
        if not chapters:
            raise ParseError("解析目录失败，请确认粘贴的是书籍总目录页面")
        return chapters

    # ---- 正文 ----
    def get_chapter_content(self, chapter_url: str) -> str:
        resp = self.http.get(chapter_url, encoding="utf-8")
        if not resp.text.strip():
            raise SiteBlockedError("网站访问受限，请稍后重试")
        soup = BeautifulSoup(resp.text, "html.parser")
        content = soup.select_one("div.ctext")
        if content is None:
            content = soup.select_one("div#content_1")
        if content is None:
            raise ParseError("正文解析失败（CTEXT）")
        for el in content.select("script, style, div#menu, table"):
            el.decompose()
        for tag in content.find_all(["p", "br", "div", "blockquote", "h1", "h2", "h3"]):
            tag.append("\n")
        text = content.get_text("\n", strip=False)
        from core.text_cleaner import clean_text
        return clean_text(text)
