# -*- coding: utf-8 -*-
import re
text = open("_sdk_glue.js", encoding="utf-8").read()
urls = set()
for m in re.finditer(r"https?://[^\"'\s\\]+", text):
    urls.add(m.group(0))
for u in sorted(urls):
    print(u)
