#!/usr/bin/env python
"""自动维护 README.md 中的自动生成区段。

目前在两个「<!-- AUTO:xxx --> ... <!-- /AUTO:xxx -->」标记之间维护：
  - project_tree   项目结构树（扫描 core/ adapters/ ui/ app.py，
                   描述取各文件模块 docstring 首行，自动随之变化）
  - adapters       数据源适配器清单

用法：
  python tools/update_readme.py

本脚本由 .githooks/pre-commit 在每次 commit 前自动运行（见下），
保证 README 的代码结构区段与仓库实际文件保持一致。
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
README = os.path.join(ROOT, "README.md")

# 参与树的目录（不展开 __pycache__ / 调试脚本 / 逆向 js）
PACKAGE_DIRS = ("core", "adapters", "ui")


def module_doc_first_line(path: str) -> str:
    """取模块 docstring 的第一行作为文件描述；无 docstring 则返回空。"""
    with open(path, encoding="utf-8") as f:
        for _ in range(10):
            line = f.readline()
            line = line.strip()
            if not line:
                continue
            if line.startswith("#"):
                continue
            if line.startswith('"""') or line.startswith("'''"):
                q = line[:3]
                content = line[3:].strip()
                if content:
                    return content.rstrip(q).strip()
                # docstring 在下一行才出现
                for _ in range(10):
                    inner = f.readline().strip()
                    if inner:
                        return inner.rstrip(q).strip()
            break
    return ""


def collect_tree() -> str:
    """生成项目结构树文本。"""
    top = os.path.join(ROOT, "app.py")
    rows: list[tuple[str, str]] = []   # (相对路径, 描述)
    if os.path.exists(top):
        rows.append(("app.py", module_doc_first_line(top)))

    for d in PACKAGE_DIRS:
        dpath = os.path.join(ROOT, d)
        if not os.path.isdir(dpath):
            continue
        names = sorted(n for n in os.listdir(dpath)
                       if n.endswith(".py") and not n.startswith("__"))
        for n in names:
            rel = os.path.join(d, n)
            rows.append((rel, module_doc_first_line(os.path.join(dpath, n))))

    max_w = max(len(r[0]) for r in rows) if rows else 0
    lines = ["```", f"{os.path.basename(ROOT)}\\"]
    for i, (rel, desc) in enumerate(rows):
        is_last = i == len(rows) - 1
        branch = "└─" if is_last else "├─"
        # 顶层 app.py 顶格，其余包内文件缩进一级
        if "/" in rel:
            d, n = rel.split("/", 1)
            prefix = "│   " if not is_last else "    "
            node = f"{prefix}{branch} {n}"
        else:
            node = f"{branch} {rel}"
        pad = " " * (max_w - len(rel))
        line = f"{node}{pad}  # {desc}" if desc else node
        lines.append("    " + line)
    lines.append("```")
    return "\n".join(lines)


def collect_adapters() -> str:
    """生成数据源适配器清单（含通用「任意网页」适配器）。"""
    rows = [
        ("维基文库", "wikisource.py", "zh.wikisource.org 公有领域古籍"),
        ("识典古籍", "shidianguji.py", "shidianguji.com 古籍（需 Node 环境逆向签名）"),
        ("CTEXT", "ctext.py", "ctext.org/zh 中文古籍库"),
        ("任意网页", "generic.py", "启发式适配任意小说网站，支持任意目录链接解析全书"),
    ]
    lines = ["| 数据源 | 适配器 | 支持站点 |", "| --- | --- | --- |"]
    for name, mod, site in rows:
        lines.append(f"| **{name}** | {mod} | {site} |")
    return "\n".join(lines)


def collect_features() -> str:
    """生成功能特性清单（可在此处手工维护，仍放在自动区段内）。"""
    return """- **模式一 · 书名搜索**：输入书名，勾选数据源，跨站检索；结果表格多选，一键下载全书 TXT
- **模式二 · 链接下载（任意网页）**：粘贴书籍目录链接，自动识别站点、解析全部章节（含目录分页、正文分页、镜像域名、重复章节恢复），批量导出全书
- **文本清洗**：剔除网页标签/脚注/页眉页脚/多余空行，强制 UTF-8，结果可直接喂给 TTS
- **可选分章节导出**：按章节拆分为独立 txt，适配 ebook2audiobook / EmotiVoice 等分批合成
- **反爬/健壮性**：UA 随机伪装、请求间隔、单章重试、失败自动跳过不崩溃；目录解析过程实时打印进度
- **实时进度**：进度条 + 带时间戳日志窗口
"""


REGIONS = {
    "project_tree": collect_tree,
    "adapters": collect_adapters,
    "features": collect_features,
}


def update() -> None:
    with open(README, encoding="utf-8") as f:
        content = f.read()

    changed = False
    for key, fn in REGIONS.items():
        body = fn().strip("\n")
        if key == "project_tree":
            body = (f"本站点仅列举应用自身模块；其余数据源逆向脚本（core/*.js）与调试文件不分发。\n\n"
                    f"{body}")

        open_mark = f"<!-- AUTO:{key} -->"
        close_mark = f"<!-- /AUTO:{key} -->"
        start = content.find(open_mark)
        end = content.find(close_mark)
        if start < 0 or end < 0:
            print(f"[skip] README 缺少标记 {key}（{open_mark}），跳过该区段。")
            continue
        start += len(open_mark)
        chunk = f"\n\n{body}\n\n"
        content = content[:start] + chunk + content[end:]
        changed = True

    if changed:
        with open(README, "w", encoding="utf-8") as f:
            f.write(content)
        print("README.md 自动区段已更新。")
    else:
        print("README.md 无标记区段被更新（请确认标记存在）。")


if __name__ == "__main__":
    sys.exit(update())