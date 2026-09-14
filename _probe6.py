# -*- coding: utf-8 -*-
"""下载 main.js 并定位 bdms/a_bogus 调用。"""
import re
import ssl
import urllib.request

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"

url = "https://lf-welfare.amemv.com/obj/douyin-welfare-image/guji/shidian/static/js/main.f9ef818b.js"
req = urllib.request.Request(url, headers={"User-Agent": UA})
js = urllib.request.urlopen(req, context=ctx, timeout=60).read().decode("utf-8", "ignore")
open("_main.js", "w", encoding="utf-8").write(js)
print("main.js len:", len(js))
for kw in ["a_bogus", "bdms", "getReferer", "init(", "reader-book/get", "readerBookGet"]:
    cnt = js.count(kw)
    idxs = [m.start() for m in re.finditer(re.escape(kw), js)][:5]
    print(f"--- {kw}: {cnt} ---")
    for i in idxs:
        seg = js[max(0, i - 120): i + 160].replace("\n", " ")
        print("   ...", seg, "...")
