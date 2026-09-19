"""下载调度逻辑：解析目录 → 逐章抓取 → 清洗合并 → 保存文件。

在 QThread 中运行，通过信号向 UI 汇报日志与进度。
"""
import re
import threading
import time
from dataclasses import dataclass

from PyQt6.QtCore import QThread, pyqtSignal

from adapters.base import BaseAdapter, get_adapter_class
from core.file_manager import (ensure_dir, safe_filename,
                               write_text_utf8)
from core.models import Book, DownloadError
from core.text_cleaner import clean_text


@dataclass
class DownloadSettings:
    output_dir: str = r"D:\书籍TXT下载"
    clean: bool = True
    retries: int = 2


def _int_to_cn(num: int) -> str:
    """把 1~9999 的整数转成中文（用于章节号，如 101 → 一百零一，10 → 十）。"""
    digits = "零一二三四五六七八九"
    units = ["", "十", "百", "千"]
    if num == 0:
        return "零"
    parts = []
    place = 0
    while num > 0:
        d = num % 10
        if d:
            parts.append(digits[d] + units[place])
        elif parts and not parts[-1].startswith("零"):
            parts.append(digits[0])
        num //= 10
        place += 1
    s = "".join(reversed(parts))
    # 十位上的"一十"去掉一（但保留 110 的"一百一十"等非首位情形）
    if s.startswith("一十"):
        s = s[1:]
    return s

_CHAPTER_PREFIX_RE = re.compile(r"^第\s*[0-9零一二三四五六七八九十百千]+\s*[章回节卷部]\s*")


def _chapter_title(idx: int, raw: str) -> str:
    """生成统一的章节内部标题：`第X章 章节名`（去掉原标题中的重复前缀）。"""
    cleaned = _CHAPTER_PREFIX_RE.sub("", raw).strip()
    return f"第{_int_to_cn(idx)}章 {cleaned}" if cleaned else f"第{_int_to_cn(idx)}章"


class DownloadWorker(QThread):
    log = pyqtSignal(str)
    progress = pyqtSignal(int, int)          # 已完成章节数, 总章节数
    book_done = pyqtSignal(str, str)         # 文件路径, 书名
    all_done = pyqtSignal()
    failed = pyqtSignal(str, str)            # 书名, 错误信息

    def __init__(self, books: list[Book], settings: DownloadSettings, parent=None):
        super().__init__(parent)
        self.books = books
        self.settings = settings
        self._cancel = threading.Event()

    def cancel(self):
        self._cancel.set()

    # ---------------- 主流程 ----------------
    def run(self):
        try:
            total_books = len(self.books)
            for book in self.books:
                if self._cancel.is_set():
                    break
                try:
                    self._download_one_book(book)
                except Exception as e:
                    self.failed.emit(book.display_title, str(e))
                    self.log.emit(f"❌ 《{book.display_title}》下载失败：{e}")
        finally:
            self.all_done.emit()

    def _download_one_book(self, book: Book):
        adapter_cls = get_adapter_class(book.source)
        if adapter_cls is None:
            # 未内置的站点统一走通用启发式适配器（如「任意网页」）
            from adapters.generic import GenericAdapter
            adapter_cls = GenericAdapter
        adapter = adapter_cls(self._new_http(), progress_cb=lambda m: self.log.emit(m))

        # 1. 解析目录
        index_url = book.chapter_hint_url or book.index_url
        self.log.emit(f"[{self._ts()}] 开始解析{book.source}《{book.display_title}》目录")
        chapters = adapter.get_chapter_list(index_url)
        if not chapters:
            raise DownloadError("未解析到任何章节")
        self.log.emit(f"[{self._ts()}] 目录解析完成，共 {len(chapters)} 个章节")

        # 2. 逐章抓取
        total = len(chapters)
        parts: list[tuple[str, str]] = []   # (章节标题, 正文)
        done = 0
        for idx, ch in enumerate(chapters, 1):
            if self._cancel.is_set():
                return
            self.log.emit(f"[{self._ts()}] 正在下载章节：{ch.title}")
            text = self._fetch_with_retry(adapter, ch.url, book, ch.title)
            if self.settings.clean:
                text = clean_text(text)
            parts.append((ch.title, text.strip()))
            done += 1
            self.progress.emit(done, total)

        # 3. 保存：整本合并 + 按章节拆分（每章一个 txt，按书名分文件夹）
        merged = "\n\n\n".join(f"{_chapter_title(i, t)}\n\n{b}" for i, (t, b) in enumerate(parts, 1))
        book_name = safe_filename(book.display_title)
        book_dir = f"{self.settings.output_dir}\\{book_name}"
        ensure_dir(book_dir)

        main_path = f"{book_dir}\\{book_name}.txt"
        write_text_utf8(main_path, merged + "\n")
        self.log.emit(f"[{self._ts()}] ✅ 整本下载完成，文件：{main_path}")

        for idx, (t, body) in enumerate(parts, 1):
            if self._cancel.is_set():
                return
            title = _chapter_title(idx, t)
            name = f"第{idx:03d}回.txt" if "回" in t else f"第{idx:03d}节.txt"
            write_text_utf8(f"{book_dir}\\{name}", f"{title}\n\n{body}\n")
        self.log.emit(f"[{self._ts()}] ✅ 已按章节拆分保存至：{book_dir}")

        self.book_done.emit(main_path, book.display_title)

    def _fetch_with_retry(self, adapter: BaseAdapter, url: str, book: Book, chapter_title: str) -> str:
        for attempt in range(self.settings.retries + 1):
            try:
                return adapter.get_chapter_content(url)
            except Exception as e:
                if attempt >= self.settings.retries:
                    self.log.emit(f"[{self._ts()}] ⚠️ 章节《{chapter_title}》失败：{e}，已跳过")
                    return ""
                self.log.emit(f"[{self._ts()}] ⚠️ 章节《{chapter_title}》重试（{attempt + 1}/{self.settings.retries}）")
                time.sleep(1.5 * (attempt + 1))
        return ""

    def _new_http(self):
        from core.http_client import HttpClient
        return HttpClient(retries=self.settings.retries)

    @staticmethod
    def _ts() -> str:
        return time.strftime("%Y-%m-%d %H:%M:%S")
