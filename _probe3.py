# -*- coding: utf-8 -*-
"""提取 readerBookGet 定义与 URL 拼接。"""
import re
import requests

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
url = ("https://lf-welfare.amemv.com/obj/douyin-welfare-image/guji/shidian/"
       "7054.9ab3bd0e.js")
text = requests.get(url, headers={"User-Agent": UA}, timeout=30).text

i = text.find("readerBookGet")
print("=== context around readerBookGet ===")
print(text[max(0, i - 1500):i + 800])
