# -*- coding: utf-8 -*-
"""分析 7054 chunk 中 readerBookGet 调用与请求参数构造。"""
import re

js = open("_chunk_7054.9ab3bd0e.js", encoding="utf-8").read()
i = js.find("readerBookGet")
print("--- around readerBookGet ---")
print(js[max(0, i - 2500): i + 2500])
