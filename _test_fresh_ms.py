# -*- coding: utf-8 -*-
"""新鲜 msToken 测试：浏览器新鲜 a_bogus vs 本地生成 a_bogus。"""
import json
import subprocess
from curl_cffi import requests as creq

FRESH_MS = "n-M03mqPubqCIzy9qEu8aTDZCZy8zM5a-Z2jasb5ANKU1Dbqu1HNHkLrwW8vQsUPdrH84C8A9rYE0gH1t2dp7URu3Q_6iZDmryBwrynmjGEd2Ed6KszUfScxSL_p7d7Bv_Vdwh5kUe85040mcQzY0D9Tpn59pzR2hdwboO_Q0b7W5m8rh133"
FP = "verify_mu0vpwkn_fTU5MUeX_YtKL_4iAv_8eC1_82b6PVeLCRL0"
REAL_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
           "(KHTML, like Gecko) TraeCN/1.107.1 Chrome/142.0.7444.235 Electron/39.2.7 Safari/537.36")
FRESH_BOGUS = ("D6sVgtSwd2Rcap/SuKrueSIRKH6lrP8y71iQWCWHCOwDLZlbSh--CQtNaxznsoCutmkCpq3HaDz/YEdcp8tip99pFmpfSEXyesV9nX6o0qNgPlT0gNmQeuDFoXBe8R4qlAV5i1J6MUJy1fV-iqdL/d1S9KOF5O8hKpOSk/uCi9G61FyALZnaPBbBNXiqij==")
COOKIE_HEADER = ("gfkadpd=361265,34425; x-web-secsdk-uid=01782dab-4ed0-4a0b-a977-75549220eb16; "
                 "s_v_web_id=verify_mu0vpwkn_fTU5MUeX_YtKL_4iAv_8eC1_82b6PVeLCRL0; __is_image_close=0")

BASE = ("https://www.shidianguji.com/api/ancientlib/read/reader-book/get/"
        "?bookId=NA11023&version=0&needCheckVersion=false&isWebpSupported=true"
        f"&verifyFp={FP}&fp={FP}&msToken={FRESH_MS}")

HEADERS = {
    "User-Agent": REAL_UA,
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.shidianguji.com/book/NA11023",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Origin": "https://www.shidianguji.com",
    "Cookie": COOKIE_HEADER,
}

# 1. 浏览器新鲜 a_bogus
print("=== 1. 浏览器新鲜 a_bogus ===")
r = creq.get(BASE + "&a_bogus=" + FRESH_BOGUS, impersonate="chrome142", headers=HEADERS, timeout=30)
print("status:", r.status_code, "body:", r.text[:300])

# 2. 本地生成 a_bogus（同样 fresh msToken）
print("=== 2. 本地生成 a_bogus ===")
proc = subprocess.run(["node", "core/abogus_sign.js", BASE, REAL_UA],
                      capture_output=True, text=True, encoding="utf-8", timeout=60,
                      cwd="d:/study/trae/青竹小说-Windows")
out = json.loads(proc.stdout)
if "error" in out:
    print("本地签名失败:", out["error"])
else:
    my_bogus = out["a_bogus"]
    print("本地 a_bogus len:", len(my_bogus))
    r = creq.get(BASE + "&a_bogus=" + my_bogus, impersonate="chrome142", headers=HEADERS, timeout=30)
    print("status:", r.status_code, "body:", r.text[:300])
