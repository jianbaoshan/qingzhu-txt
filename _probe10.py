# -*- coding: utf-8 -*-
"""查看 main.js 中 ancientlib 出现处与请求层。"""
import re

js = open("_main.js", encoding="utf-8").read()
for m in re.finditer(r"ancientlib", js):
    i = m.start()
    print("---", i, "---")
    print(js[max(0, i - 200): i + 300].replace("\n", " "))
    print()
