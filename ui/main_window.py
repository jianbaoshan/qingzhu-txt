"""主窗口：搜索 / URL 下载两个模式 + 下载设置 + 日志进度。"""
import os
import re
from concurrent.futures import ThreadPoolExecutor

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (QCheckBox, QFileDialog, QGroupBox, QHBoxLayout,
                             QHeaderView, QLabel, QLineEdit, QPlainTextEdit,
                             QProgressBar, QPushButton, QTabWidget, QTableWidget,
                             QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget,
                             QMessageBox)

from adapters.base import detect_site, get_adapter_class
from adapters.generic import GenericAdapter
from core.downloader import DownloadSettings, DownloadWorker
from core.file_manager import open_in_file_manager
from core.models import Book

SOURCES = ["维基文库", "识典古籍", "CTEXT"]
DEFAULT_DIR = r"D:\书籍TXT下载"


# ---------------- 搜索线程 ----------------
class SearchWorker(QThread):
    results_ready = pyqtSignal(list)
    search_failed = pyqtSignal(str, str)   # 来源, 错误

    def __init__(self, keyword: str, sources: list[str], parent=None):
        super().__init__(parent)
        self.keyword = keyword
        self.sources = sources

    def run(self):
        from core.http_client import HttpClient
        books: list[Book] = []
        with ThreadPoolExecutor(max_workers=len(self.sources)) as ex:
            futs = {}
            for src in self.sources:
                cls = get_adapter_class(src)
                if cls is None:
                    continue
                # 每个任务独立 HttpClient，避免跨线程共享 Session
                futs[ex.submit(cls(HttpClient()).search_book, self.keyword)] = src
            for fut, src in futs.items():
                try:
                    books.extend(fut.result())
                except Exception as e:
                    self.search_failed.emit(src, str(e))
        self.results_ready.emit(books)


# ---------------- 目录解析线程 ----------------
class ParseWorker(QThread):
    parsed = pyqtSignal(object, str, str)   # chapters, site, title
    parse_failed = pyqtSignal(str)
    progress = pyqtSignal(str)              # 解析过程日志

    def __init__(self, url: str, parent=None):
        super().__init__(parent)
        self.url = url

    def run(self):
        from core.http_client import HttpClient
        site = detect_site(self.url)

        def progress_cb(msg: str):
            self.progress.emit(msg)

        try:
            if site is None:
                # 未命中的站点 → 走通用启发式适配器，支持任意小说网站目录链接
                adapter: GenericAdapter = GenericAdapter(HttpClient(), progress_cb=progress_cb)
                site = adapter.name
            else:
                adapter = get_adapter_class(site)(HttpClient(), progress_cb=progress_cb)
            chapters = adapter.get_chapter_list(self.url)
            title = adapter.resolve_title(self.url)
            self.parsed.emit(chapters, site, title)
        except Exception as e:
            self.parse_failed.emit(str(e))


# ---------------- 主窗口 ----------------
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("青竹txt书籍下载 - 书籍 TXT 批量下载器")
        self.resize(900, 650)
        self._books: list[Book] = []
        self._tab2_book: Book | None = None
        self._search_worker: SearchWorker | None = None
        self._parse_worker: ParseWorker | None = None
        self._download_worker: DownloadWorker | None = None
        self._build_ui()

    # ================= UI 构建 =================
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.addLayout(self._build_source_bar())
        root.addWidget(self._build_tabs())
        root.addWidget(self._build_settings_bar())
        root.addLayout(self._build_progress_bar())

    def _build_source_bar(self) -> QHBoxLayout:
        bar = QHBoxLayout()
        bar.addWidget(QLabel("数据源："))
        self.src_checks: dict[str, QCheckBox] = {}
        for name in SOURCES:
            cb = QCheckBox(name)
            cb.setChecked(True)
            self.src_checks[name] = cb
            bar.addWidget(cb)
        bar.addStretch()
        return bar

    def _build_tabs(self) -> QTabWidget:
        tabs = QTabWidget()
        tabs.addTab(self._build_search_tab(), "📖 按书名搜索下载")
        tabs.addTab(self._build_url_tab(), "🔗 根据网页链接下载全书")
        return tabs

    # ----- Tab1 搜索 -----
    def _build_search_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)

        row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("请输入书籍名称，例：三国演义、聊斋志异")
        self.search_btn = QPushButton("开始搜索")
        self.search_btn.clicked.connect(self.on_search)
        self.search_input.returnPressed.connect(self.on_search)
        row.addWidget(self.search_input, 1)
        row.addWidget(self.search_btn)
        lay.addLayout(row)

        self.result_table = QTableWidget(0, 5)
        self.result_table.setHorizontalHeaderLabels(["选择", "书名", "来源网站", "简介", "状态"])
        header = self.result_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.result_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        lay.addWidget(self.result_table, 1)

        btn_row = QHBoxLayout()
        self.download_btn = QPushButton("下载选中书籍")
        self.download_btn.clicked.connect(self.on_download_selected)
        btn_row.addStretch()
        btn_row.addWidget(self.download_btn)
        lay.addLayout(btn_row)
        return w

    # ----- Tab2 URL -----
    def _build_url_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)

        self.url_input = QPlainTextEdit()
        self.url_input.setPlaceholderText(
            "粘贴书籍目录主页完整 URL，支持任意小说网站的目录链接\n"
            "提示：请粘贴书籍总目录页面链接，不要粘贴单章节页面链接。\n"
            "（内置站点：维基文库、识典古籍、CTEXT 会自动使用专用解析；其余任意网站将自动启发式识别章节）"
        )
        self.url_input.setFixedHeight(100)
        lay.addWidget(self.url_input)

        row = QHBoxLayout()
        self.parse_btn = QPushButton("解析目录")
        self.parse_btn.clicked.connect(self.on_parse_url)
        row.addWidget(self.parse_btn)
        row.addStretch()
        lay.addLayout(row)

        self.parse_result_label = QLabel("解析结果展示文本")
        lay.addWidget(self.parse_result_label)

        btn_row = QHBoxLayout()
        self.url_download_btn = QPushButton("开始下载全书 TXT")
        self.url_download_btn.clicked.connect(self.on_download_from_url)
        self.url_download_btn.setEnabled(False)
        btn_row.addStretch()
        btn_row.addWidget(self.url_download_btn)
        lay.addLayout(btn_row)
        lay.addStretch()
        return w

    # ----- 下载设置 -----
    def _build_settings_bar(self) -> QGroupBox:
        box = QGroupBox("下载设置")
        lay = QHBoxLayout(box)

        lay.addWidget(QLabel("输出保存目录："))
        self.dir_input = QLineEdit(DEFAULT_DIR)
        lay.addWidget(self.dir_input, 1)
        dir_btn = QPushButton("选择文件夹")
        dir_btn.clicked.connect(self.on_choose_dir)
        lay.addWidget(dir_btn)

        self.clean_check = QCheckBox("下载后自动文本清洗")
        self.clean_check.setChecked(True)
        self.clean_check.setToolTip("去除网页标签、广告、多余空行，推荐打开")
        lay.addWidget(self.clean_check)

        self.utf8_check = QCheckBox("强制保存 UTF-8 编码")
        self.utf8_check.setChecked(True)
        self.utf8_check.setEnabled(False)
        lay.addWidget(self.utf8_check)
        return box

    def _build_progress_bar(self) -> QVBoxLayout:
        lay = QVBoxLayout()
        self.progress = QProgressBar()
        self.progress.setValue(0)
        lay.addWidget(self.progress)

        log_row = QHBoxLayout()
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setPlaceholderText("实时日志窗口")
        log_row.addWidget(self.log_view, 1)
        lay.addLayout(log_row)

        btn_row = QHBoxLayout()
        open_btn = QPushButton("打开输出文件夹")
        open_btn.clicked.connect(lambda: open_in_file_manager(self.dir_input.text().strip()))
        btn_row.addStretch()
        btn_row.addWidget(open_btn)
        lay.addLayout(btn_row)
        return lay

    # ================= 事件处理 =================
    def log(self, msg: str):
        self.log_view.append(msg)

    def _selected_sources(self) -> list[str]:
        return [k for k, cb in self.src_checks.items() if cb.isChecked()]

    # ----- 搜索 -----
    def on_search(self):
        keyword = self.search_input.text().strip()
        if not keyword:
            QMessageBox.information(self, "提示", "请输入书籍名称")
            return
        sources = self._selected_sources()
        if not sources:
            QMessageBox.information(self, "提示", "请至少勾选一个数据源")
            return
        self.log(f"[搜索] 关键词：{keyword}，数据源：{'、'.join(sources)}")
        self.search_btn.setEnabled(False)
        self.result_table.setRowCount(0)
        self._books.clear()
        self._search_worker = SearchWorker(keyword, sources, self)
        self._search_worker.results_ready.connect(self.on_search_results)
        self._search_worker.search_failed.connect(
            lambda src, err: self.log(f"⚠️ {src} 搜索失败：{err}"))
        self._search_worker.finished.connect(lambda: self.search_btn.setEnabled(True))
        self._search_worker.start()

    def on_search_results(self, books: list[Book]):
        self._books = books
        self.result_table.setRowCount(len(books))
        for row, b in enumerate(books):
            check = QTableWidgetItem()
            check.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            check.setCheckState(Qt.CheckState.Unchecked)
            check.setData(Qt.ItemDataRole.UserRole, row)
            self.result_table.setItem(row, 0, check)
            self.result_table.setItem(row, 1, QTableWidgetItem(b.display_title))
            self.result_table.setItem(row, 2, QTableWidgetItem(b.source))
            self.result_table.setItem(row, 3, QTableWidgetItem(b.description))
            self.result_table.setItem(row, 4, QTableWidgetItem("未下载"))
        self.log(f"[搜索] 共找到 {len(books)} 条结果")

    # ----- 下载选中 -----
    def on_download_selected(self):
        selected: list[Book] = []
        for row in range(self.result_table.rowCount()):
            item = self.result_table.item(row, 0)
            if item and item.checkState() == Qt.CheckState.Checked:
                idx = item.data(Qt.ItemDataRole.UserRole)
                if idx is not None and 0 <= idx < len(self._books):
                    selected.append(self._books[idx])
        if not selected:
            QMessageBox.information(self, "提示", "请先勾选要下载的书籍")
            return
        self.start_download(selected)

    # ----- URL 解析 -----
    def on_parse_url(self):
        url = self.url_input.toPlainText().strip()
        if not url:
            QMessageBox.information(self, "提示", "请先粘贴书籍目录链接")
            return
        self.log(f"[解析] 正在解析链接：{url}")
        self.parse_btn.setEnabled(False)
        self.url_download_btn.setEnabled(False)
        self._tab2_book = None
        self._parse_worker = ParseWorker(url, self)
        self._parse_worker.parsed.connect(self.on_url_parsed)
        self._parse_worker.parse_failed.connect(self.on_parse_failed)
        self._parse_worker.progress.connect(self.on_parse_progress)
        self._parse_worker.finished.connect(lambda: self.parse_btn.setEnabled(True))
        self._parse_worker.start()

    def on_parse_progress(self, msg: str):
        self.log(f"[解析] {msg}")

    def on_url_parsed(self, chapters, site: str, title: str):
        self.parse_result_label.setText(f"检测到共 {len(chapters)} 个章节（来源：{site}）")
        self.log(f"[解析] ✅ 检测到共 {len(chapters)} 个章节，来源：{site}")
        self._tab2_book = Book(
            title=title or "未命名书籍",
            source=site,
            index_url=self.url_input.toPlainText().strip(),
        )
        self._tab2_chapters = chapters
        self.url_download_btn.setEnabled(True)

    def on_parse_failed(self, err: str):
        self.parse_result_label.setText("解析目录失败")
        self.log(f"[解析] ❌ {err}")
        QMessageBox.warning(self, "解析失败", err)

    def on_download_from_url(self):
        if self._tab2_book is None:
            QMessageBox.information(self, "提示", "请先解析目录")
            return
        self.start_download([self._tab2_book])

    # ----- 统一下载入口 -----
    def start_download(self, books: list[Book]):
        out_dir = self.dir_input.text().strip() or DEFAULT_DIR
        settings = DownloadSettings(
            output_dir=out_dir,
            clean=self.clean_check.isChecked(),
        )
        if not self._mark_rows_downloading(books):
            return
        self.set_busy(True)
        self.progress.setValue(0)
        self._download_worker = DownloadWorker(books, settings, self)
        self._download_worker.log.connect(self.log)
        self._download_worker.progress.connect(self.on_progress)
        self._download_worker.book_done.connect(self.on_book_done)
        self._download_worker.failed.connect(self.on_book_failed)
        self._download_worker.all_done.connect(self.on_all_done)
        self._download_worker.start()

    def _mark_rows_downloading(self, books: list[Book]) -> bool:
        matched = False
        for row in range(self.result_table.rowCount()):
            item = self.result_table.item(row, 0)
            if not item:
                continue
            idx = item.data(Qt.ItemDataRole.UserRole)
            if idx is not None and 0 <= idx < len(self._books):
                if self._books[idx] in books:
                    self.result_table.item(row, 4).setText("下载中")
                    matched = True
        if not matched and not self._tab2_book:
            return False
        return True

    def on_progress(self, done: int, total: int):
        if total > 0:
            self.progress.setMaximum(total)
            self.progress.setValue(done)

    def on_book_done(self, file_path: str, title: str):
        for row in range(self.result_table.rowCount()):
            item = self.result_table.item(row, 0)
            if not item:
                continue
            idx = item.data(Qt.ItemDataRole.UserRole)
            if idx is not None and 0 <= idx < len(self._books):
                if self._books[idx].display_title == title:
                    self.result_table.item(row, 4).setText("已完成")
        self.log(f"🎉 《{title}》下载完成")

    def on_book_failed(self, title: str, err: str):
        for row in range(self.result_table.rowCount()):
            item = self.result_table.item(row, 0)
            if not item:
                continue
            idx = item.data(Qt.ItemDataRole.UserRole)
            if idx is not None and 0 <= idx < len(self._books):
                if self._books[idx].display_title == title:
                    self.result_table.item(row, 4).setText("失败")

    def on_all_done(self):
        self.set_busy(False)
        self.log("✅ 全部任务处理完毕")

    def set_busy(self, busy: bool):
        self.search_btn.setEnabled(not busy)
        self.download_btn.setEnabled(not busy)
        self.parse_btn.setEnabled(not busy)
        self.url_download_btn.setEnabled(not busy and self._tab2_book is not None)

    # ----- 目录选择 -----
    def on_choose_dir(self):
        path = QFileDialog.getExistingDirectory(self, "选择输出文件夹",
                                                self.dir_input.text().strip() or DEFAULT_DIR)
        if path:
            self.dir_input.setText(path)

    def closeEvent(self, event):
        if self._download_worker is not None and self._download_worker.isRunning():
            self._download_worker.cancel()
        super().closeEvent(event)
