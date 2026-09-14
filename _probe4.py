# -*- coding: utf-8 -*-
"""检查 robots.txt 与 sitemap。"""
import requests

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

for url in ["https://www.shidianguji.com/robots.txt",
            "https://www.shidianguji.com/sitemap.xml"]:
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=20)
        print(f"=== {url} status={r.status_code}")
        print(r.text[:800])
    except Exception as e:
        print(f"=== {url} error: {e}")
