"""下载调度逻辑：解析目录 → 逐章抓取 → 清洗合并 → 保存文件。

在 QThread 中运行，通过信号向 UI 汇报日志与进度。
"""
import threading
import time
from dataclasses import dataclass

from PyQt6.QtCore import QThread, pyqtSignal

from adapters.base import BaseAdapter, get_adapter_class
from core.file_manager import (ensure_dir, safe_filename,
                               write_text_utf8)
from core.models import Book
from core.text_cleaner import clean_text


@dataclass
class DownloadSettings:
    output_dir: str = r"D:\书籍TXT下载"
    clean: bool = True
    retries: int = 2


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
            raise DownloadError(f"未知数据源：{book.source}")
        adapter = adapter_cls(self._new_http())

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
        merged = "\n\n\n".join(f"{t}\n\n{b}" for t, b in parts)
        book_name = safe_filename(book.display_title)
        book_dir = f"{self.settings.output_dir}\\{book_name}"
        ensure_dir(book_dir)

        main_path = f"{book_dir}\\{book_name}.txt"
        write_text_utf8(main_path, merged + "\n")
        self.log.emit(f"[{self._ts()}] ✅ 整本下载完成，文件：{main_path}")

        for idx, (title, body) in enumerate(parts, 1):
            if self._cancel.is_set():
                return
            name = f"第{idx:03d}回.txt" if "回" in title else f"第{idx:03d}节.txt"
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
