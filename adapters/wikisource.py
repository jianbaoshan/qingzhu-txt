"""维基文库适配器（zh.wikisource.org）。"""
import html
import re
import urllib.parse

from bs4 import BeautifulSoup

from adapters.base import BaseAdapter
from core.models import Book, Chapter, ParseError, SiteBlockedError

API = "https://zh.wikisource.org/w/api.php"


class WikisourceAdapter(BaseAdapter):
    name = "维基文库"
    domain = "wikisource.org"

    # ---- 搜索 ----
    def search_book(self, keyword: str) -> list[Book]:
        resp = self.http.get(API, params={
            "action": "query", "list": "search",
            "srsearch": keyword, "srnamespace": "0",
            "srlimit": "10", "format": "json",
        })
        try:
            data = resp.json()
        except ValueError:
            raise SiteBlockedError("网站访问受限，请稍后重试")
        results: list[Book] = []
        for item in data.get("query", {}).get("search", []):
            title = item.get("title", "")
            if not title or "消歧義" in title or "消歧义" in title:
                continue
            snippet = re.sub(r"<[^>]+>", "", item.get("snippet", ""))
            snippet = html.unescape(snippet)
            page_url = "https://zh.wikisource.org/wiki/" + urllib.parse.quote(title)
            results.append(Book(
                title=title, source=self.name, index_url=page_url,
                description=snippet.strip()[:200],
            ))
        return results

    # ---- 目录 ----
    def get_chapter_list(self, book_index_url: str) -> list[Chapter]:
        resp = self.http.get(book_index_url, encoding="utf-8")
        if not resp.text.strip():
            raise SiteBlockedError("网站访问受限，请稍后重试")
        soup = BeautifulSoup(resp.text, "html.parser")
        # 维基文库目录容器结构不统一（部分书在 mw-parser-output，部分在其他容器），
        # 统一在 #mw-content-text 内按“目录页标题 + / + 子页”规则提取章节链接。
        content = soup.select_one("#mw-content-text")
        if content is None:
            content = soup
        base_title = urllib.parse.unquote(
            book_index_url.split("/wiki/")[-1].split("#")[0]
        )
        base_href = "/wiki/" + urllib.parse.quote(base_title)
        chapters: list[Chapter] = []
        seen: set[str] = set()
        for a in content.select("a[href]"):
            href = a["href"]
            if href.startswith(base_href + "/") and "://" not in href:
                full = "https://zh.wikisource.org" + href
                if full in seen:
                    continue
                title = a.get_text(" ", strip=True).strip()
                if not title or title in ("上一章", "下一章", "返回目录"):
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
        content = soup.select_one("div.mw-parser-output")
        if content is None:
            content = soup
        # 删除注释、表格、导航、页脚等非正文元素
        for sel in ["sup.reference", "table", "div.navbox", "div.mw-editsection",
                    "div.vector-toc", "ol.references", ".mw-cite-backlink",
                    "div.printfonly", "span.mw-editsection", "div#footer", "dl"]:
            for el in content.select(sel):
                el.decompose()
        # 段落块之间换行
        for tag in content.find_all(["p", "div", "h1", "h2", "h3", "li", "br", "blockquote"]):
            tag.append("\n")
        text = content.get_text("\n", strip=False)
        text = re.sub(r"\u00a0", " ", text)
        from core.text_cleaner import clean_text
        return clean_text(text)
