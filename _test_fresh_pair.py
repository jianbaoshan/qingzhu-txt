# -*- coding: utf-8 -*-
"""立即测试：同一次页面加载的新鲜 msToken + 新鲜浏览器 a_bogus，从 Python 重放。"""
from curl_cffi import requests as creq

# 来自同一时刻捕获的完整 URL
FRESH_URL = ("https://www.shidianguji.com/api/ancientlib/read/reader-book/get/"
             "?bookId=NA11023&version=0&needCheckVersion=false&isWebpSupported=true"
             "&verifyFp=verify_mu0vpwkn_fTU5MUeX_YtKL_4iAv_8eC1_82b6PVeLCRL0"
             "&fp=verify_mu0vpwkn_fTU5MUeX_YtKL_4iAv_8eC1_82b6PVeLCRL0"
             "&msToken=YQCA-fSuavO8IeoyF06cn5wWEDzO7ReQfC7jNWOgM7c1rG1Xq7oVqSOf2QNDLywbvAgpPuzrqBt_e5aIvlZZGf3AqHgO5PxZWkqjTULXGlRNII7vEzIQzDjF--5kcUsIh8omAVRbFXnyCGrVG_TWek6lqy_-yOOz-gETaQqUPAocI1Q27Rjw"
             "&a_bogus=m6U5kqSEmNmbFpMGYKrDeS95uwjMrsuy5riKbn67exENLqFTcX-rC5bcaxzxsZ5LUWk9pqVHrDFlbdxcpm7hp9rkFmpvuDsfas5An6moZqqhaeG0LHmQeuhFwXBeWbTql%2FVViIjI0UrLZnx-irQY%2Fd1SyKOFQmWhKpxSk%2FTSi9G6Z0LAE3c-PBGpNXNtUU5j")

REAL_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
           "(KHTML, like Gecko) TraeCN/1.107.1 Chrome/142.0.7444.235 Electron/39.2.7 Safari/537.36")
COOKIE_HEADER = ("gfkadpd=361265,34425; x-web-secsdk-uid=01782dab-4ed0-4a0b-a977-75549220eb16; "
                 "s_v_web_id=verify_mu0vpwkn_fTU5MUeX_YtKL_4iAv_8eC1_82b6PVeLCRL0; __is_image_close=0")

HEADERS = {
    "User-Agent": REAL_UA,
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.shidianguji.com/book/NA11023",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Origin": "https://www.shidianguji.com",
    "Cookie": COOKIE_HEADER,
    "sec-ch-ua": '"Chromium";v="142", "Microsoft Edge";v="142", "Not:A-Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
}

r = creq.get(FRESH_URL, impersonate="chrome142", headers=HEADERS, timeout=30)
print("status:", r.status_code)
print("body:", r.text[:600])
