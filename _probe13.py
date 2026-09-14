# -*- coding: utf-8 -*-
"""搜索模块 525（请求客户端）定义位置。"""
import glob

for f in ["_main.js", "_chunk_4172.871bdc1d.js", "_chunk_static_js_async___session_layout.2d18aa8b.js",
          "_chunk_static_js_async___session__lang___book__.fa5a04ec.js"]:
    js = open(f, encoding="utf-8").read()
    for pat in ["525:function", "Zs:", "getTccSpace", "readerBookGet", "reader-book"]:
        if pat in js:
            print(f, "->", pat, "x", js.count(pat))
    # 找 webpack 入口 module map
    m = __import__("re").findall(r'"525"\s*:\s*function', js)
    if m:
        print(f, "module 525 defined here")
