# -*- coding: utf-8 -*-
"""抓取 shidianguji 书籍主页 HTML，列出 script 资源。"""
import re
import ssl
import urllib.request

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"

req = urllib.request.Request("https://www.shidianguji.com/book/NA11023", headers={"User-Agent": UA})
html = urllib.request.urlopen(req, context=ctx, timeout=30).read().decode("utf-8", "ignore")
print("html len:", len(html))
for m in re.finditer(r'<script[^>]*src="([^"]+)"', html):
    print("SRC:", m.group(1))
