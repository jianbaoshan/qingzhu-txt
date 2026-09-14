# -*- coding: utf-8 -*-
"""测试 CSRF token 机制：HEAD 请求获取 x-ware-csrf-token，然后带 token 请求。"""
import json
import subprocess
from curl_cffi import requests as creq

FP = "verify_mu0vpwkn_fTU5MUeX_YtKL_4iAv_8eC1_82b6PVeLCRL0"
FRESH_MS = "n-M03mqPubqCIzy9qEu8aTDZCZy8zM5a-Z2jasb5ANKU1Dbqu1HNHkLrwW8vQsUPdrH84C8A9rYE0gH1t2dp7URu3Q_6iZDmryBwrynmjGEd2Ed6KszUfScxSL_p7d7Bv_Vdwh5kUe85040mcQzY0D9Tpn59pzR2hdwboO_Q0b7W5m8rh133"
REAL_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
           "(KHTML, like Gecko) TraeCN/1.107.1 Chrome/142.0.7444.235 Electron/39.2.7 Safari/537.36")
COOKIE_HEADER = ("gfkadpd=361265,34425; x-web-secsdk-uid=01782dab-4ed0-4a0b-a977-75549220eb16; "
                 "s_v_web_id=verify_mu0vpwkn_fTU5MUeX_YtKL_4iAv_8eC1_82b6PVeLCRL0; __is_image_close=0")

BASE_PATH = "/api/ancientlib/read/reader-book/get/"

HEADERS = {
    "User-Agent": REAL_UA,
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.shidianguji.com/book/NA11023",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Origin": "https://www.shidianguji.com",
    "Cookie": COOKIE_HEADER,
}

# 1. HEAD 请求获取 csrf token
print("=== 1. HEAD 获取 csrf token ===")
r = creq.head("https://www.shidianguji.com" + BASE_PATH, impersonate="chrome142",
              headers={**HEADERS,
                       "x-secsdk-csrf-request": "1",
                       "x-secsdk-csrf-version": "1.2.22"},
              timeout=30)
print("status:", r.status_code)
print("x-ware-csrf-token:", r.headers.get("x-ware-csrf-token"))
print("all headers:", dict(r.headers))

# 2. 如果拿到 token，带 token 请求 GET
token = r.headers.get("x-ware-csrf-token")
if token:
    token_val = token.split(",")[1] if "," in token else token
    print("token_val:", token_val)
    base_url = ("https://www.shidianguji.com/api/ancientlib/read/reader-book/get/"
                "?bookId=NA11023&version=0&needCheckVersion=false&isWebpSupported=true"
                f"&verifyFp={FP}&fp={FP}&msToken={FRESH_MS}")
    proc = subprocess.run(["node", "core/abogus_sign.js", base_url, REAL_UA],
                          capture_output=True, text=True, encoding="utf-8", timeout=60,
                          cwd="d:/study/trae/青竹小说-Windows")
    out = json.loads(proc.stdout)
    bogus = out["a_bogus"]
    print("a_bogus len:", len(bogus))
    r2 = creq.get(base_url + "&a_bogus=" + bogus, impersonate="chrome142",
                  headers={**HEADERS, "x-secsdk-csrf-token": token_val}, timeout=30)
    print("=== 2. GET with csrf token ===")
    print("status:", r2.status_code, "body:", r2.text[:400])
else:
    print("未获取到 x-ware-csrf-token")
