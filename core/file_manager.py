"""本地文件管理：安全文件名、UTF-8 保存、分章导出。"""
import os
import re

from core.models import DownloadError

ILLEGAL_CHARS = re.compile(r'[\\/:*?"<>|\x00-\x1f]')


def safe_filename(name: str, default: str = "未命名") -> str:
    """过滤 Windows 非法字符并裁剪长度。"""
    name = ILLEGAL_CHARS.sub("_", name).strip(" .")
    name = re.sub(r"\s+", " ", name)
    if not name:
        name = default
    return name[:80]


def ensure_dir(path: str) -> None:
    try:
        os.makedirs(path, exist_ok=True)
    except OSError as e:
        raise DownloadError(f"无法创建目录 {path}，请更换输出文件夹") from e


def write_text_utf8(path: str, text: str) -> None:
    """强制 UTF-8 保存，防止 TTS 读取乱码。"""
    try:
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
    except OSError as e:
        raise DownloadError(f"磁盘无写入权限：{path}，请更换输出文件夹") from e


def open_in_file_manager(path: str) -> None:
    """用系统文件管理器打开路径。"""
    if not os.path.exists(path):
        return
    if os.path.isfile(path):
        path = os.path.dirname(path)
    try:
        os.startfile(path)  # type: ignore[attr-defined]
    except Exception:
        pass
