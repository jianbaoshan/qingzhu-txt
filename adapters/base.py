"""站点适配器基类与统一接口。"""
from abc import ABC, abstractmethod

from core.http_client import HttpClient
from core.models import Book, Chapter


class BaseAdapter(ABC):
    """统一适配器接口：search_book / get_chapter_list / get_chapter_content。"""

    name = "未知站点"
    domain = ""

    def __init__(self, http: HttpClient, progress_cb=None):
        self.http = http
        self._progress_cb = progress_cb

    def _notify(self, msg: str) -> None:
        """向调用方（App 日志等）报告解析进度；未提供回调则忽略。"""
        if self._progress_cb:
            try:
                self._progress_cb(msg)
            except Exception:
                pass

    @abstractmethod
    def search_book(self, keyword: str) -> list[Book]:
        """输入书名，返回书籍列表。"""

    @abstractmethod
    def get_chapter_list(self, book_index_url: str) -> list[Chapter]:
        """传入书籍目录主页 url，返回全部章节 url 列表。"""

    @abstractmethod
    def get_chapter_content(self, chapter_url: str) -> str:
        """传入章节页面 url，返回清洗后的章节纯文本。"""

    def resolve_title(self, book_index_url: str) -> str:
        """从书籍链接推断书名（默认取路径最后一段，可被站点覆盖）。"""
        import urllib.parse
        path = urllib.parse.urlparse(book_index_url).path.rstrip("/")
        return urllib.parse.unquote(path.split("/")[-1] or "")

    @classmethod
    def supports_url(cls, url: str) -> bool:
        return cls.domain in url.lower()


def get_adapter_class(site_key: str):
    from adapters.wikisource import WikisourceAdapter
    from adapters.shidianguji import ShidiangujiAdapter
    from adapters.ctext import CtextAdapter
    table = {
        "维基文库": WikisourceAdapter,
        "识典古籍": ShidiangujiAdapter,
        "CTEXT": CtextAdapter,
    }
    return table.get(site_key)


def detect_site(url: str) -> str | None:
    """根据 URL 自动识别所属站点。"""
    for site, domain in [("维基文库", "wikisource.org"),
                         ("识典古籍", "shidianguji.com"),
                         ("CTEXT", "ctext.org")]:
        if domain in url.lower():
            return site
    return None
