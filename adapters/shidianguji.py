"""识典古籍适配器（www.shidianguji.com）—— 基于服务端渲染（SSR）数据解析。"""
import json
import re
import urllib.parse

from bs4 import BeautifulSoup

from adapters.base import BaseAdapter
from core.models import Book, Chapter, ParseError, SiteBlockedError

BASE = "https://www.shidianguji.com"


class ShidiangujiAdapter(BaseAdapter):
    name = "识典古籍"
    domain = "shidianguji.com"

    # ---------- 内部工具 ----------
    @staticmethod
    def _extract_router_data(html_text: str) -> dict:
        m = re.search(r"window\._ROUTER_DATA\s*=\s*(\{.*?\})\s*</script>", html_text, re.S)
        if not m:
            raise ParseError("页面数据解析失败（识典古籍）")
        try:
            return json.loads(m.group(1))
        except ValueError:
            raise ParseError("页面数据解析失败（识典古籍）")

    @staticmethod
    def _book_loader(router: dict) -> dict:
        """按优先级匹配 loader：书籍路由 > 搜索路由 > 其余含书数据的路由。"""
        loaders = router.get("loaderData") or {}
        for key, value in loaders.items():
            if "book" in key and isinstance(value, dict):
                return value
        for key, value in loaders.items():
            if "search" in key and isinstance(value, dict):
                return value
        for key, value in loaders.items():
            if isinstance(value, dict) and ("bookInfo" in value or "paragraphList" in value
                                            or "paragraphs" in value or "recommendBooks" in value):
                return value
        return {}

    def _search_data(self, keyword: str) -> dict:
        url = f"{BASE}/search/" + urllib.parse.quote(keyword)
        resp = self.http.get(url, encoding="utf-8")
        if not resp.text.strip():
            raise SiteBlockedError("网站访问受限，请稍后重试")
        router = self._extract_router_data(resp.text)
        loader = self._book_loader(router)
        return loader.get("data") or {}

    # ---------- 搜索 ----------
    def search_book(self, keyword: str) -> list[Book]:
        data = self._search_data(keyword)
        books: list[Book] = []
        # 推荐书籍列表（书库命中）
        rec_books = (data.get("recommendBooks") or {}).get("books") or []
        for b in rec_books:
            bid = b.get("bookId") or ""
            title = b.get("bookName") or ""
            if not title:
                continue
            add_names = b.get("addNames") or []
            if add_names:
                title = f"{title}（{'、'.join(add_names)}）"
            authors = b.get("authors") or []
            author = "、".join(f"{a.get('persName', '')} {a.get('responsibleTypeStr', '')}".strip()
                               for a in authors if a.get("persName"))
            desc = f"{b.get('dynastyCategoryName', '') or ''} {author}".strip()
            edition = b.get("edition") or ""
            if edition:
                desc = f"{desc} · {edition}" if desc else edition
            books.append(Book(
                title=title, source=self.name,
                index_url=f"{BASE}/book/{bid}",
                description=desc, book_id=bid,
            ))
        # 段落命中（含章节入口，可用于下载）
        for p in data.get("paragraphs") or []:
            bi = p.get("bookInfo") or {}
            bid = bi.get("bookId") or ""
            if not bid or any(b.book_id == bid for b in books):
                continue
            title = bi.get("bookName") or ""
            authors = bi.get("authors") or []
            author = "、".join(f"{a.get('persName', '')} {a.get('responsibleTypeStr', '')}".strip()
                               for a in authors if a.get("persName"))
            chapter_url = ""
            cid = p.get("chapterId") or ""
            if cid:
                chapter_url = f"{BASE}/book/{bid}/chapter/{cid}"
            books.append(Book(
                title=title, source=self.name,
                index_url=f"{BASE}/book/{bid}",
                description=(author or "").strip(),
                book_id=bid, chapter_hint_url=chapter_url,
            ))
        return books

    # ---------- 目录 ----------
    def get_chapter_list(self, book_index_url: str) -> list[Chapter]:
        m = re.search(r"/book/([A-Za-z0-9_\-]+)(?:/chapter/([A-Za-z0-9_\-]+))?", book_index_url)
        if not m:
            raise ParseError("无法识别的识典古籍链接")
        book_id, chapter_id = m.group(1), m.group(2)
        if not chapter_id:
            # 书籍主页不含服务端目录数据，需要任一章节链接作为引导
            raise ParseError(
                "识典古籍书籍主页无法直接解析目录，请粘贴该书任意章节页面链接"
                "（格式：shidianguji.com/book/{书id}/chapter/{章节id}）"
            )
        url = f"{BASE}/book/{book_id}/chapter/{chapter_id}"
        resp = self.http.get(url, encoding="utf-8")
        if not resp.text.strip():
            raise SiteBlockedError("网站访问受限，请稍后重试")
        soup = BeautifulSoup(resp.text, "html.parser")
        chapters: list[Chapter] = []
        seen: set[str] = set()
        for a in soup.select(f'a[href*="/book/{book_id}/chapter/"]'):
            href = a["href"]
            if "://" in href:
                full = href
            else:
                full = BASE + href
            title = a.get_text(" ", strip=True).strip()
            if not title or title in ("上一篇", "下一篇", "目录"):
                continue
            if full in seen:
                continue
            seen.add(full)
            chapters.append(Chapter(title=title, url=full))
        if not chapters:
            raise ParseError("解析目录失败，请确认粘贴的是书籍目录或章节页面链接")
        return chapters

    # ---------- 正文 ----------
    def resolve_title(self, book_index_url: str) -> str:
        """从章节页获取书名。"""
        m = re.search(r"/book/([A-Za-z0-9_\-]+)(?:/chapter/([A-Za-z0-9_\-]+))?", book_index_url)
        if not m:
            return "未命名书籍"
        book_id, chapter_id = m.group(1), m.group(2)
        url = f"{BASE}/book/{book_id}"
        if chapter_id:
            url = f"{url}/chapter/{chapter_id}"
        try:
            resp = self.http.get(url, encoding="utf-8")
            router = self._extract_router_data(resp.text)
            loader = self._book_loader(router)
            bi = loader.get("bookInfo") or {}
            name = bi.get("bookName") or ""
            if name:
                return name
        except Exception:
            pass
        return book_id

    def get_chapter_content(self, chapter_url: str) -> str:
        resp = self.http.get(chapter_url, encoding="utf-8")
        if not resp.text.strip():
            raise SiteBlockedError("网站访问受限，请稍后重试")
        router = self._extract_router_data(resp.text)
        loader = self._book_loader(router)
        paragraphs = loader.get("paragraphList") or []
        chapter_title = self._current_chapter_title(resp.text, chapter_url, loader)
        lines: list[str] = []
        for para in paragraphs:
            if para.get("paragraphType") not in (None, 1):
                continue
            raw = para.get("content") or ""
            if isinstance(raw, str):
                try:
                    content = json.loads(raw)
                except ValueError:
                    continue
            else:
                content = raw
            text_lines = []
            for ln in content.get("lines") or []:
                txt = (ln.get("content") or "").strip()
                if txt:
                    text_lines.append(txt)
            if text_lines:
                lines.append("".join(text_lines))
        body = "\n\n".join(lines)
        from core.text_cleaner import clean_text
        cleaned = clean_text(body)
        return f"{chapter_title}\n\n{cleaned}" if chapter_title else cleaned

    @staticmethod
    def _current_chapter_title(html_text: str, chapter_url: str, loader: dict) -> str:
        """从章节页导航里找到当前章节的标题。"""
        soup = BeautifulSoup(html_text, "html.parser")
        target = chapter_url.split(".com", 1)[-1]
        for a in soup.select("a[href]"):
            href = a.get("href", "")
            if href.endswith(target) or href == target:
                t = a.get_text(" ", strip=True).strip()
                if t and t not in ("上一篇", "下一篇", "目录"):
                    return t
        # 兜底：bookInfo 书名
        bi = loader.get("bookInfo") or {}
        return bi.get("bookName") or ""
