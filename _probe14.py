# -*- coding: utf-8 -*-
"""查看 layout chunk 中模块 525（请求客户端）源码。"""
import re

js = open("_chunk_static_js_async___session_layout.2d18aa8b.js", encoding="utf-8").read()
i = js.find("525:function")
print("idx", i)
seg = js[i:i + 9000]
print(seg[:9000])
