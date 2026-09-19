"""通用启发式适配器：针对未内置的任意小说网站。

根据「书籍目录主页 URL」自动识别目录容器、章节链接与正文容器，实现任意站点全书抓取。
复用 core/text_cleaner 的清理逻辑与 core/models 的模型。

注意：本适配器仅在「粘贴链接」模式使用；按书名词搜某个任意站点不在支持范围内，
search_book 直接返回空列表。
"""
import re
import time
import urllib.parse

import requests
from bs4 import BeautifulSoup

from adapters.base import BaseAdapter
from core.models import Book, Chapter, ParseError, SiteBlockedError

# 常见目录容器，按优先级依次尝试
_CATALOG_SELECTORS = [
    "#list", "#chapterlist", "#chapterList", "#chapter_list",
    ".listmain", ".book-mulu", "#list-page", ".mulu", "#chapters",
]
# 常见正文容器，按优先级依次尝试
_CONTENT_SELECTORS = [
    "#content", "#chaptercontent", "#BookText", "#booktext",
    ".content", ".chapter-content", ".read-content", "#nr_nr",
    "#chapterContent", "#txt", ".txt", "article", ".word_read",
]
# 需要剔除的正文内嵌节点
_JUNK_TAGS = ["script", "style", "ins", "iframe", "form",
              "div.ad", "div[class*=ad]", "div[id*=tap]", "div[id*=pup]"]

_CHAPTER_RE = re.compile(r"第[0-9零一二三四五六七八九十百千万]+[章回节卷部]")

_TRUE_SIMPLE = set("这为很到说时就也们个我他你她它子在来\"有国和发着上面也等下到说能看没分就都是有到要在本" + "的了在是不出了就都有和你说我以一个为会上他这也要们")  # 简体高频字


def _trad_ratio(text: str) -> float:
    """粗估文本里简体占比，用于判断是否疑似繁体站。"""
    sample = [c for c in text if "\u4e00" <= c <= "\u9fff"][:800]
    if not sample:
        return 1.0
    hits = sum(1 for c in sample if c in _TRUE_SIMPLE)
    return hits / len(sample)


class GenericAdapter(BaseAdapter):
    name = "任意网页"
    domain = ""

    # ---- 仅 URL 模式，不提供按书名搜索 ----
    def search_book(self, keyword: str) -> list[Book]:
        return []

    # ---- 标题 ----
    def resolve_title(self, book_index_url: str) -> str:
        try:
            soup = BeautifulSoup(self._fetch(book_index_url), "html.parser")
            h1 = soup.select_one("h1")
            if h1 and h1.get_text(strip=True):
                title = h1.get_text(strip=True)
            else:
                title_tag = soup.find("title")
                title = title_tag.get_text(strip=True) if title_tag else ""
                # 去站点后缀，如"《X》_最新章节_新笔趣阁" / "X_全文阅读"
                for sep in ["_最新章节", "_全文", "最新章节列表", "全文免费阅读"]:
                    if sep in title:
                        title = title.split(sep)[0]
                        break
                title = re.sub(r"[\s_\-|【】]", "", title.rstrip("》"))
        except Exception:
            title = self._title_from_path(book_index_url)
        return title or self._title_from_path(book_index_url)

    @staticmethod
    def _title_from_path(url: str) -> str:
        path = urllib.parse.urlparse(url).path.rstrip("/")
        return urllib.parse.unquote(path.split("/")[-1] or "未命名书籍")

    # ---- 目录 ----
    # 明显非正文的目录杂项（公告/感言/请假/求票等），解析时跳过
    _JUNK_TITLES = ("感言", "公告", "请假", "求票", "求订阅", "新书", "上架")

    def get_chapter_list(self, book_index_url: str) -> list[Chapter]:
        links: list[tuple[str, str]] = []   # (absolute_url, title)
        seen: set[tuple[str, str]] = set()
        base_host = urllib.parse.urlparse(book_index_url).netloc

        self._notify("正在抓取首页目录…")
        html = self._fetch(book_index_url)
        soup = BeautifulSoup(html, "html.parser")
        self._collect_links(soup, book_index_url, base_host, links, seen)

        # 首页常只展示前若干章，存在「查看更多章节/章节目录」入口指向完整目录分页页，
        # 检测到则跳转到完整目录页继续收集。注意：只有当首页目录明显不完整（章节数较少）
        # 时才跟随——部分站点首页已罗列全书，且其「更多章节」入口反而指向另一份镜像副本
        # （如 gnhmfs 指向 book/180860/），追进去会把整本再收集一遍造成重复。
        entry = self._find_full_catalog(soup, book_index_url)
        if entry and len(links) < 300:
            try:
                entry = urllib.parse.urljoin(book_index_url, entry)
                html = self._fetch(entry)
                soup = BeautifulSoup(html, "html.parser")
                self._collect_links(soup, entry, base_host, links, seen)
                book_index_url = entry
            except Exception:
                pass

        # 目录分页：很多站点一页只放固定数量章节（如每页 100 章），需翻页拼全。
        # 分页形态多样：页码模板 / <select> 下拉 / 「下一页」链接。注意部分站点分页容器
        # 类名不含 page（如 bqg5555 的 div.index-container），_discover_pagination 探测不到，
        # 因此需要无条件尝试 <select> 下拉分页。
        next_url, total = self._discover_pagination(soup)
        select_pages = self._select_page_urls(soup, book_index_url)
        page_urls: list[str] = []
        if next_url:
            # 下一页可能是 scheme 相对（//host/...）或相对路径，统一转成绝对地址
            next_url = urllib.parse.urljoin(book_index_url, next_url)
            builder = self._page_url_builder(book_index_url, next_url)
            if builder is not None and total:
                page_urls = [builder(p) for p in range(2, total + 1)]
            elif select_pages:
                # 无法推导页码模板：若分页是 <select> 下拉，遍历其全部选项地址
                page_urls = [u for u in select_pages if u != book_index_url]
            else:
                # 跟随「下一页」链接（有界翻页）——只能顺序发现
                cur, guard = next_url, 0
                while cur and guard < 1000:
                    page_urls.append(cur)
                    guard += 1
                    try:
                        su = BeautifulSoup(self._fetch(cur), "html.parser")
                    except Exception:
                        break
                    nxt, _ = self._discover_pagination(su)
                    if not nxt or nxt == cur:
                        break
                    cur = nxt
        elif select_pages:
            # 无常规分页器：遍历 <select> 下拉的全部选项页
            page_urls = [u for u in select_pages if u != book_index_url]

        # 并行抓取全部目录分页（分页页互相独立，串行对大量分页站点过慢），
        # 完成后按页面顺序合并、去重。
        if page_urls:
            self._append_pages_parallel(page_urls, base_host, links, seen)

        if not links:
            raise ParseError("未能从该网页解析出章节链接，请确认粘贴的是书籍目录页链接")

        # 保留页面顺序的全部章节（按 URL 去重），仅剔除明显非正文的杂项标题。
        # 不做数字连续过滤：有些站点章节 URL 编号并非 +1 连续，截断会误删正确章节。
        filtered = [(u, t) for u, t in links
                    if not any(k in t for k in self._JUNK_TITLES)]
        if not filtered:
            filtered = links

        # 部分站点目录存在相邻章节 href 重复（站点数据错误，如 bqg5555 的第三章指向第二章的页）。
        # 直接按 URL 去重会整章丢失；对重复条目用其页面「下一页」导航解析出真实 URL 补回。
        resolved = self._resolve_duplicates(filtered)
        return [Chapter(title=t, url=u) for u, t in self._dedup(resolved)]

    def _append_pages_parallel(self, page_urls: list[str], base_host: str,
                               links: list, seen: set):
        """并行抓取目录分页页，按传入顺序合并章节（单页失败重试 2 次后跳过该页）。"""
        from concurrent.futures import ThreadPoolExecutor

        def grab(page_url: str) -> list[tuple[str, str]]:
            for attempt in range(3):
                try:
                    time.sleep(0.3)
                    html = self._fetch(page_url)
                    soup = BeautifulSoup(html, "html.parser")
                    local: list[tuple[str, str]] = []
                    local_seen: set = set()
                    self._collect_links(soup, page_url, base_host, local, local_seen)
                    return local
                except Exception:
                    if attempt >= 2:
                        return []
                    time.sleep(1.0 * (attempt + 1))
            return []

        self._notify(f"正在抓取目录分页（共 {len(page_urls)} 页）…")
        with ThreadPoolExecutor(max_workers=8) as ex:
            results = list(ex.map(grab, page_urls))
        for local in results:
            for item in local:
                if item not in seen:
                    seen.add(item)
                    links.append(item)
        self._notify("目录分页抓取完成")

    def _resolve_duplicates(self, filtered: list[tuple[str, str]]) -> list[tuple[str, str]]:
        """目录里 href 重复的条目（站点数据错误），沿其页面「下一页」解析真实 URL 补回。

        重复 URL 互相独立，并行解析（每个 URL 仅解析一次），再按原顺序重建列表。
        """
        from collections import Counter
        from concurrent.futures import ThreadPoolExecutor

        dup_urls = [u for u, c in Counter(u for u, _ in filtered).items() if c > 1]
        nav: dict[str, str | None] = {}
        if dup_urls:
            self._notify(f"正在恢复 {len(dup_urls)} 个重复章节的真实地址…")
            with ThreadPoolExecutor(max_workers=8) as ex:
                nav = dict(zip(dup_urls, ex.map(self._resolve_chapter_via_nav, dup_urls)))
            self._notify("重复章节恢复完成")

        resolved: list[tuple[str, str]] = []
        seen_url: set[str] = set()
        for u, t in filtered:
            if u not in seen_url:
                seen_url.add(u)
                resolved.append((u, t))
                continue
            true_url = nav.get(u)
            if true_url and true_url not in seen_url:
                seen_url.add(true_url)
                resolved.append((true_url, t))
        return resolved

    def _resolve_chapter_via_nav(self, chapter_url: str) -> str | None:
        """目录里相邻章节 href 重复时，沿该页「下一页」导航找到真正的下一章 URL。

        若该章正文分页（{id}.html → {id}_2.html…），先跟随到最后一页再取「下一页」。
        """
        cur = chapter_url
        for _ in range(30):
            try:
                html = self._fetch(cur)
            except Exception:
                return None
            soup = BeautifulSoup(html, "html.parser")
            nxt = self._next_link_href(soup, cur)
            if nxt is None or not self._is_next_page_of(cur, nxt):
                return nxt
            cur = nxt
        return None

    def _collect_links(self, soup: BeautifulSoup, page_url: str,
                       base_host: str, links: list, seen: set):
        """从一页目录里收集同源章节链接，追加到 links（保持页面顺序、去重）。

        去重键为 (url, title)：部分站点目录存在相邻章节 href 重复但标题不同的条目
        （如 bqg5555 第三章 href 误指向第二章），仅按 url 去重会整章丢失。
        """
        root = self._select_catalog(soup)
        for a in root.select("a[href]"):
            href = a.get("href") or ""
            abs_url = urllib.parse.urljoin(page_url, href)
            if not abs_url.startswith("http"):
                continue
            # 仅取同源章节页链接。注意：部分站点目录链接指向镜像/内容 CDN 域名
            # （如 gnhmfs.com 的书页链接指向 myssgns.com），host 可与书页域名不同，
            # 因此不能按精确 host 过滤——host 不同时要求其形态像章节链接即可。
            # 是否误收了跨书外链，由 _select_catalog/_best_catalog 已选的容器兜底。
            host = urllib.parse.urlparse(abs_url).netloc
            if host != base_host and not GenericAdapter._is_chapter_like(a):
                continue
            title = a.get_text(" ", strip=True)
            if not title or title in ("上一章", "下一章", "目录", "简介"):
                continue
            if (abs_url, title) in seen:
                continue
            seen.add((abs_url, title))
            links.append((abs_url, title))

    @staticmethod
    def _discover_pagination(soup: BeautifulSoup):
        """在目录页里定位分页容器，返回 (下一页URL, 总页数)；无则 (None, None)。"""
        pagelink = None
        for sel in (".pagelink", ".page", ".pagebox", ".listpage",
                    ".pages", ".page_all", "div[class*=page]"):
            n = soup.select_one(sel)
            if n is not None:
                pagelink = n
                break
        if pagelink is None:
            return None, None
        total = None
        m = re.search(r"(\d+)\s*/\s*(\d+)", pagelink.get_text(" "))
        if m:
            total = int(m.group(2))
        else:
            m = re.search(r"共\s*(\d+)\s*页", pagelink.get_text(" "))
            if m:
                total = int(m.group(1))
        next_url = None
        for a in pagelink.select("a[href]"):
            t = a.get_text().strip()
            if any(k in t for k in ("下一页", "下页", "next")):
                next_url = a["href"]
                break
        if next_url is None:
            return None, total
        return next_url, total

    @staticmethod
    def _page_url_builder(index_url: str, next_url: str):
        """推导页码模板：index_url 中某个数字段 +1 后等于 next_url 的那个位置即页码。
        返回 build(page)->url；无法推导则返回 None。"""
        for m in re.finditer(r"\d+", index_url):
            alt = index_url[:m.start()] + str(int(m.group(0)) + 1) + index_url[m.end():]
            if alt == next_url:
                s, e = m.start(), m.end()
                return lambda p: index_url[:s] + str(p) + index_url[e:]
        return None

    @staticmethod
    def _select_page_urls(soup: BeautifulSoup, current_url: str) -> list[str]:
        """从 <select> 下拉分页里提取全部页地址（转绝对 URL、去重）。"""
        urls: list[str] = []
        seen: set[str] = set()
        for opt in soup.select("select option[value]"):
            v = (opt.get("value") or "").strip()
            if not v or v.startswith("javascript"):
                continue
            abs_v = urllib.parse.urljoin(current_url, v)
            if abs_v in seen:
                continue
            seen.add(abs_v)
            urls.append(abs_v)
        return urls

    @staticmethod
    def _find_full_catalog(soup: BeautifulSoup, page_url: str) -> str | None:
        """查找「查看更多章节/章节目录/全部章节」类入口链接，指向完整目录页。"""
        hints = ("查看更多", "章节目录", "全部章节", "更多章节", "查看全部", "完整目录")
        base_host = urllib.parse.urlparse(page_url).netloc
        for a in soup.select("a[href]"):
            t = a.get_text(" ", strip=True)
            if not any(h in t for h in hints):
                continue
            href = (a.get("href") or "").strip()
            if not href or href.startswith("javascript"):
                continue
            abs_url = urllib.parse.urljoin(page_url, href)
            if not abs_url.startswith("http"):
                continue
            if urllib.parse.urlparse(abs_url).netloc != base_host:
                continue
            if abs_url == page_url:
                continue
            return abs_url
        return None

    @staticmethod
    def _dedup(seq: list[tuple[str, str]]) -> list[tuple[str, str]]:
        out: list[tuple[str, str]] = []
        s: set[str] = set()
        for u, t in seq:
            if u not in s:
                s.add(u)
                out.append((u, t))
        return out

    def _select_catalog(self, soup: BeautifulSoup) -> BeautifulSoup:
        for sel in _CATALOG_SELECTORS:
            node = soup.select_one(sel)
            if node is not None and set(node.select("a[href]")):
                return node
        # 兜底：目录通常是 <ul>/<dl> 列表，优先在列表里按「章节特征」数量挑选，
        # 避免误选顶部导航 / 推荐位等含少量链接的容器；找不到再退到 <div>。
        for scope in ("ul, dl", "div"):
            node = self._best_catalog(soup.select(scope))
            if node is not None:
                return node
        return soup

    @staticmethod
    def _is_chapter_like(a) -> bool:
        """判断 <a> 是否像章节链接：排除 /infos/ /tags/ 等明显非章节路径段。"""
        href = (a.get("href") or "")
        if re.search(r"/chapter/|/read/|/book/", href):
            return True
        if re.search(r"/(?:infos?|tags?|sort|top|list|search|sitemap|map|login|register|mybook|jilu|user|help|full)/", href, re.I):
            return False
        if re.search(r"/\d+\.html(?:\?.*)?$", href):
            return True
        return bool(_CHAPTER_RE.search(a.get_text(" ", strip=True)))

    @staticmethod
    def _best_catalog(nodes) -> BeautifulSoup | None:
        """在候选节点里选章节特征链接最多的；同样数量时选链接总数更少（更纯净）的。"""
        best, best_key = None, (-1, 10**9)
        for node in nodes:
            a = node.select("a[href]")
            chapter_like = sum(1 for x in a if GenericAdapter._is_chapter_like(x))
            if chapter_like > 0 and (chapter_like, -len(a)) > best_key:
                best, best_key = node, (chapter_like, -len(a))
        return best

    # ---- 正文 ----
    def get_chapter_content(self, chapter_url: str) -> str:
        html = self._fetch(chapter_url)

        # 部分站点正文由脚本以 base64 渲染（如 biquge123.la 的 qsbs.bb），
        # 且正文本身按页拆分（{id}.html → {id}_1.html → {id}_2.html…），需循环跟随。
        decoded = self._decode_qsbs(html)
        soup = BeautifulSoup(html, "html.parser")
        if decoded is not None:
            parts = [decoded]
        else:
            part = self._extract_content_html(soup)
            if part is None:
                raise ParseError("正文解析失败，页面结构未识别")
            parts = [part]

        # 跟随正文分页（base64 渲染与常规 HTML 两种模式通用）：
        # 仅当「下一页」指向当前章节的下一页（{id}_{n+1}.html）时继续拼接，否则停止。
        cur = chapter_url
        for _ in range(30):  # 防御性上限：单章分页通常个位数
            nxt = self._next_link_href(soup, cur)
            if nxt is None or not self._is_next_page_of(cur, nxt):
                break
            page_html = self._fetch(nxt)
            page_soup = BeautifulSoup(page_html, "html.parser")
            if decoded is not None:
                page_part = self._decode_qsbs(page_html)
                if page_part is None:
                    page_part = self._extract_content_html(page_soup)
            else:
                page_part = self._extract_content_html(page_soup)
            if page_part is None:
                break
            parts.append(page_part)
            cur = nxt
            soup = page_soup

        content = BeautifulSoup("\n".join(parts), "html.parser")
        for tag in content.find_all(["br"]):
            tag.replace_with("\n")
        for tag in content.find_all(["p", "div", "blockquote", "h1", "h2", "h3", "section"]):
            tag.append("\n")

        from core.text_cleaner import clean_text
        text = clean_text(content.get_text("\n"))

        # 剔除站内页眉/页脚广告行与分页标记（如"一秒记住【笔趣阁】…无弹窗！"、
        # "章节报错（免登陆）"、"（本章未完…）"、"第三百七十章(第2/2页)"）
        text = self._strip_chrome(text)

        # 去掉开头内嵌的"第X章 ..."标题行（统一章节标题由下载器生成）
        lines = text.split("\n")
        while lines and not lines[0].strip():
            lines.pop(0)
        if lines:
            first = lines[0].strip()
            # 形如"第X章 …"的章节标题，或形如"…（第1页）"的站内页标题行
            if _CHAPTER_RE.match(first) or re.search(r"（第\d+页）$", first):
                lines.pop(0)
        text = "\n".join(lines).strip() + "\n"
        # 部分站点在正文开头注入"!"占位符，去除
        if text.startswith(("!", "！")):
            text = text.lstrip("!！").lstrip() + "\n"

        # 疑似繁体则转简体
        if _trad_ratio(text) < 0.5:
            converted = self._to_simplified(text)
            if converted is not None:
                text = converted
        # 规整站内非断行空格与行首缩进（&nbsp; 生成的占位缩进）
        text = text.replace("\u00a0", " ")
        text = re.sub(r"(?m)^[ \t]+", "", text)
        return text

    def _extract_content_html(self, soup: BeautifulSoup) -> str | None:
        """从正文页选取正文容器并剔除内嵌杂项，返回其 HTML；无法识别返回 None。"""
        content = None
        for sel in _CONTENT_SELECTORS:
            content = soup.select_one(sel)
            if content is not None:
                break
        if content is None:
            # 兜底：取正文文本最长的 <div>
            content = max(
                (d for d in soup.find_all("div")
                 if len(d.get_text("", strip=True)) > 200),
                key=lambda d: len(d.get_text("", strip=True)),
                default=None,
            )
        if content is None:
            return None
        for el in content.select(",".join(_JUNK_TAGS)):
            el.decompose()
        # 剔除站内推荐位 / 阅读模式提示等非正文段落
        for p in content.find_all("p"):
            ptext = p.get_text(" ", strip=True)
            if any(k in ptext for k in ("相邻推荐", "请勿开启浏览器阅读模式", "阅读模式，否则")):
                p.decompose()
        return str(content)

    # 站点正文以 base64 渲染的脚本调用，如 biquge123.la：document.writeln(qsbs.bb('...'))
    _QSB_B64_RE = re.compile(r"qsbs\.bb\(\s*['\"]([A-Za-z0-9+/=]+)['\"]\s*\)")

    @classmethod
    def _decode_qsbs(cls, html: str) -> str | None:
        """若页面正文由 qsbs.bb(base64) 渲染，返回解码后的 HTML 文本；否则返回 None。"""
        blocks = cls._QSB_B64_RE.findall(html)
        if not blocks:
            return None
        import base64
        parts = []
        for b in blocks:
            try:
                parts.append(base64.b64decode(b).decode("utf-8", errors="replace"))
            except Exception:
                continue
        return "\n".join(parts)

    @staticmethod
    def _next_link_href(soup: BeautifulSoup, base_url: str) -> str | None:
        """取页面里「下一章/下页/下一页」链接的绝对地址；无则 None。"""
        for a in soup.select("a[href]"):
            if a.get_text(" ", strip=True) not in ("下一章", "下页", "下一页"):
                continue
            href = (a.get("href") or "").strip()
            if not href or href.startswith("javascript"):
                continue
            return urllib.parse.urljoin(base_url, href)
        return None

    @staticmethod
    def _is_next_page_of(current_url: str, next_href: str) -> bool:
        """正文分页判断：next_href 是否指向当前章节的后续页（同 id、页码递增）。

        站点分页编号不一：biquge123.la 用 {id}.html → {id}_1.html，bqg5555.cc 用
        {id}.html → {id}_2.html；因此只要同 id 且页码大于当前页即可判定为续页。
        """
        m = re.search(r"/(\d+)(?:_(\d+))?\.html(?:[?#].*)?$", current_url)
        if not m:
            return False
        cid, cpage = m.group(1), int(m.group(2) or 0)
        nm = re.search(r"/(\d+)(?:_(\d+))?\.html(?:[?#].*)?$", next_href)
        if not nm:
            return False
        nid, npage = nm.group(1), int(nm.group(2) or 0)
        return nid == cid and npage > cpage

    # 页眉/页脚常见广告行（整行匹配即删除）
    _CHROME_LINES = (
        "章节报错（免登陆）", "章节报错", "报错（免登陆）",
        "存书签", "关灯", "字号：小", "字号",
        "目录", "章节目录", "上一章", "下一章", "返回目录",
    )
    # 分页标记，如"第三百七十章(第2/2页)"、"（本章未完，请点击下一页继续阅读）"
    _PAGE_MARK_RE = re.compile(
        r"^(?:第[0-9零一二三四五六七八九十百千万]+[章回节卷部]\s*\(\s*第\d+/\d+页\s*\)"
        r"|（?本章未完[^）\n]*）?|【?本章未完[^】\n]*】?|(?:第|后续)?[一二三四五六七八九十]+\s*/\s*\d+\s*页)$"
    )

    @classmethod
    def _strip_chrome(cls, text: str) -> str:
        """删除正文里残留的站内导航/广告整行与分页标记。"""
        lines = text.split("\n")
        out: list[str] = []
        for ln in lines:
            s = ln.strip()
            # 纯 URL / 残缺协议头的广告行
            if re.match(r"^https?:", s):
                continue
            # 整行命中常见广告/导航文案
            if any(s == k or s.startswith(k) for k in cls._CHROME_LINES):
                continue
            # 匹配"一秒记住【xxx】…无弹窗！"这类推广话术
            if ("一秒记住" in s or "记住本站" in s or "无弹窗" in s) and len(s) <= 60:
                continue
            # 匹配分页标记（"第X章(第Y/Z页)"、"本章未完…"）
            if cls._PAGE_MARK_RE.match(s):
                continue
            out.append(ln)
        return "\n".join(out).strip() + "\n"

    @staticmethod
    def _to_simplified(text: str) -> str | None:
        """用 opencc 做繁→简；环境不可用则返回 None（跳过）。"""
        try:
            import opencc
        except ImportError:
            return None
        try:
            return opencc.OpenCC("t2s").convert(text)
        except Exception:
            return None

    # ---- 网络 ----
    def _fetch(self, url: str) -> str:
        ua = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
        ref = urllib.parse.urldefrag(url).url
        try:
            resp = requests.get(
                url, timeout=20,
                headers={"User-Agent": ua, "Referer": ref,
                         "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"},
            )
            resp.raise_for_status()
        except requests.RequestException as e:
            raise SiteBlockedError(f"网络请求失败：{e}")
        resp.encoding = resp.apparent_encoding or "utf-8"
        return resp.text