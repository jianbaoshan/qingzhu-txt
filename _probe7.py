# -*- coding: utf-8 -*-
"""下载候选 chunk 并搜索 a_bogus / bdms / init 用法。"""
import re
import ssl
import urllib.request

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
BASE = "https://lf-welfare.amemv.com/obj/douyin-welfare-image/guji/shidian/"

files = [
    "7054.9ab3bd0e.js",
    "static/js/async/__session/(lang$)/book/$.fa5a04ec.js",
    "static/js/async/__session/layout.2d18aa8b.js",
    "4172.871bdc1d.js",
    "5241.5a79988a.js",
    "1706.0b122746.js",
]

for f in files:
    try:
        req = urllib.request.Request(BASE + f, headers={"User-Agent": UA})
        js = urllib.request.urlopen(req, context=ctx, timeout=60).read().decode("utf-8", "ignore")
        safe = f.replace("/", "_").replace("(", "_").replace(")", "_").replace("$", "_")
        open("_chunk_" + safe, "w", encoding="utf-8").write(js)
        hits = {}
        for kw in ["a_bogus", "bdms", "getReferer", "reader-book/get", "readerBookGet", "verifyFp", "msToken", "sign"]:
            c = js.count(kw)
            if c:
                hits[kw] = c
        print(f, "len", len(js), "hits", hits)
    except Exception as e:
        print(f, "FAIL", e)
