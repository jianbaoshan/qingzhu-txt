"""数据模型与自定义异常。"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Book:
    """搜索到的一本书。"""
    title: str                 # 书名
    source: str                # 数据源名称（维基文库/识典古籍/CTEXT）
    index_url: str             # 书籍目录主页 URL
    description: str = ""      # 简介 / 作者 / 版本信息
    book_id: str = ""          # 站点内部 id（可选）
    chapter_hint_url: str = "" # 已知的章节入口 URL（用于识典古籍引导）

    @property
    def display_title(self) -> str:
        return self.title


@dataclass
class Chapter:
    """书中的一个章节。"""
    title: str      # 章节名
    url: str        # 章节页面 URL


class DownloadError(Exception):
    """通用下载错误。"""


class SiteBlockedError(DownloadError):
    """网站反爬拦截 / 无法访问。"""


class NotSupportedSiteError(DownloadError):
    """URL 不属于内置站点。"""


class ParseError(DownloadError):
    """目录 / 章节解析失败。"""


class NetworkError(DownloadError):
    """网络超时等。"""
