# -*- coding: utf-8 -*-
"""用 curl_cffi 模拟 Chrome TLS/HTTP2 指纹，重放真实 a_bogus。"""
from curl_cffi import requests as creq

REAL_URL_NO_SIG = ("https://www.shidianguji.com/api/ancientlib/read/reader-book/get/"
                   "?bookId=NA11023&version=0&needCheckVersion=false&isWebpSupported=true"
                   "&verifyFp=verify_mu0vpwkn_fTU5MUeX_YtKL_4iAv_8eC1_82b6PVeLCRL0"
                   "&fp=verify_mu0vpwkn_fTU5MUeX_YtKL_4iAv_8eC1_82b6PVeLCRL0"
                   "&msToken=ZnkvbvlZvtU9giXvO_9ncbROFBIi1kYd7sC-3fz8HCB2qPptfRkzHU66flI6jaa1HHLBObXkyPWaqcyKhiFfZ8CUtk_oseiEQJ-j4DAoCiFA1DoeEByYdlscnCIL-jH5w2_Z5tOoCt0UgIMmsBHRYCM-BoE4KnOBqzunR7kx7ySah3ZdBGav")

REAL_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
           "(KHTML, like Gecko) TraeCN/1.107.1 Chrome/142.0.7444.235 Electron/39.2.7 Safari/537.36")

REAL_BOGUS = ("xf0fDq6JYq55PpFtuCageb2RyHf/rB8yWZi/bnv7H5y1yhlbsh-3C3GWnoqN4NVDtWk9poVHGDzMYEVcp87TpCr"
              "kwmkkugkya05nnW6LZqNhPUs0DNDOezDzuXsC85Tq-/V9iAj62Ury1fn-irQg/d3S9KYe5YuhQ1OSk2uSi9Gh1M6ALZc1PQbdP7GqqD==")

COOKIE_HEADER = ("gfkadpd=361265,34425; x-web-secsdk-uid=01782dab-4ed0-4a0b-a977-75549220eb16; "
                 "s_v_web_id=verify_mu0vpwkn_fTU5MUeX_YtKL_4iAv_8eC1_82b6PVeLCRL0; __is_image_close=0")

url = REAL_URL_NO_SIG + "&a_bogus=" + REAL_BOGUS

# 模拟 Chrome 的 TLS/HTTP2 指纹
for imp in ["chrome", "chrome124", "chrome131", "chrome142"]:
    try:
        r = creq.get(url, impersonate=imp, headers={
            "User-Agent": REAL_UA,
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://www.shidianguji.com/book/NA11023",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Cookie": COOKIE_HEADER,
        }, timeout=30)
        body = r.text
        print(f"[{imp}] status={r.status_code} body={body[:200]}")
    except Exception as e:
        print(f"[{imp}] ERROR: {e}")
