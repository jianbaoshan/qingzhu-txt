# -*- coding: utf-8 -*-
"""打印章节页 SSR 全部 39 个章节链接标题。"""
import requests
from bs4 import BeautifulSoup

BASE = "https://www.shidianguji.com"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

book_id = "NA11023"
chapter_id = "1k291us1d4tnq"
url = f"{BASE}/book/{book_id}/chapter/{chapter_id}"
r = requests.get(url, headers={"User-Agent": UA}, timeout=20)
soup = BeautifulSoup(r.text, "html.parser")
links = []
for a in soup.select(f'a[href*="/book/{book_id}/chapter/"]'):
    title = a.get_text(" ", strip=True).strip()
    if title and title not in ("上一篇", "下一篇", "目录"):
        links.append((title, a["href"]))
print("total:", len(links))
for t, h in links:
    print(f"  {t}  ->  {h}")
