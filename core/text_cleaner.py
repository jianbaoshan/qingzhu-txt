"""通用文本清洗引擎：剔除网页残留、压缩空行、去除页眉页脚。"""
import re

# 需要删除的常见页眉页脚 / 导航文字
NAV_PATTERNS = [
    r"上一章",
    r"下一章",
    r"返回目录",
    r"目录(?:\s*$)",
    r"^登录后阅读",
    r"^手机阅读",
    r"^点击进入",
]

# 脚注 / 注释标记
NOTE_PATTERNS = [
    r"\[\d+\]",          # [1] [2]
    r"\[\s*注\s*\]",     # [注]
    r"《\d+》",           # 章回数字占位
]

HTML_ESCAPE = {
    "&nbsp;": " ", "&amp;": "&", "&lt;": "<", "&gt;": ">",
    "&quot;": '"', "&#39;": "'", "&apos;": "'", "&hellip;": "…",
    "&mdash;": "—", "&ndash;": "–", "&ldquo;": "“", "&rdquo;": "”",
    "&lsquo;": "‘", "&rsquo;": "’",
}


def unescape_html(text: str) -> str:
    for k, v in HTML_ESCAPE.items():
        text = text.replace(k, v)
    text = re.sub(r"&#(\d+);", lambda m: chr(int(m.group(1))) if int(m.group(1)) < 65536 else "", text)
    return text


def clean_text(raw: str, remove_nav: bool = True) -> str:
    """清洗正文文本。"""
    text = unescape_html(raw)
    # 删除脚注标记
    for p in NOTE_PATTERNS:
        text = re.sub(p, "", text)
    if remove_nav:
        for p in NAV_PATTERNS:
            text = re.sub(p, "", text)
    # 统一换行，压缩连续空行为最多两个换行
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [ln.rstrip() for ln in text.split("\n")]
    out: list[str] = []
    blank = 0
    for ln in lines:
        if ln.strip():
            out.append(ln)
            blank = 0
        else:
            blank += 1
            if blank <= 1:
                out.append("")
    return "\n".join(out).strip() + "\n"


def extract_paragraphs(container_text: str) -> str:
    """把（已转换为换行分隔的）HTML 容器文本整理为段落文本。"""
    return clean_text(container_text)
