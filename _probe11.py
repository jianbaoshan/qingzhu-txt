# -*- coding: utf-8 -*-
"""定位 7054 中包含 Ud 的模块及其 import 映射。"""
import re

js = open("_chunk_7054.9ab3bd0e.js", encoding="utf-8").read()
i = js.find("function Ud(U){return(0,a._)(")
head = js[:i]
starts = [m.start() for m in re.finditer(r"\d+:\s*function\([Ucf],\s*[Uce],\s*[Uen]\)\{", head)]
print("num:", len(starts), "last:", starts[-1] if starts else None)
if starts:
    seg = head[starts[-1]:i]
    print(seg[:4000])
