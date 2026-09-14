# -*- coding: utf-8 -*-
"""在 _sdk_glue.js 中查找 bdms.init 调用与配置。"""
import re

data = open("_sdk_glue.js", encoding="utf-8").read()
for kw in ["bdms.init", ".init(", "init:", "getReferer", "loadMap.bdms", "bdmsVersion", "version:", "aid:"]:
    for m in list(re.finditer(re.escape(kw), data))[:4]:
        i = m.start()
        print(f"--- {kw} @ {i} ---")
        print("   ", data[max(0, i - 150): i + 250].replace("\n", " "))
