# -*- coding: utf-8 -*-
"""搜索 Zs（readerBookGet 请求客户端导出）定义位置。"""
import re

files = ["_main.js", "_chunk_7054.9ab3bd0e.js", "_chunk_4172.871bdc1d.js",
         "_chunk_static_js_async___session_layout.2d18aa8b.js",
         "_chunk_static_js_async___session__lang___book__.fa5a04ec.js"]
for f in files:
    js = open(f, encoding="utf-8").read()
    for pat in ["Zs:", "Zs=", "readerBookGet", "reader-book/get", "/get/?", "needCheckVersion"]:
        c = js.count(pat)
        if c:
            i = js.find(pat)
            print(f, "|", pat, "x", c, "| ctx:", js[max(0, i - 100): i + 150].replace("\n", " ")[:250])
