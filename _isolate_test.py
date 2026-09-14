# -*- coding: utf-8 -*-
"""隔离测试：真实 a_bogus 在 Python 请求中是否可用。
1. 真实 URL + 真实 a_bogus + 无cookie → ?
2. 真实 URL + 真实 a_bogus + 真实cookie → ?
3. 真实 URL + 本地 a_bogus + 真实cookie → ?
"""
import json
import ssl
import subprocess
import urllib.request

REAL_URL_NO_SIG = ("https://www.shidianguji.com/api/ancientlib/read/reader-book/get/"
                   "?bookId=NA11023&version=0&needCheckVersion=false&isWebpSupported=true"
                   "&verifyFp=verify_mu0vpwkn_fTU5MUeX_YtKL_4iAv_8eC1_82b6PVeLCRL0"
                   "&fp=verify_mu0vpwkn_fTU5MUeX_YtKL_4iAv_8eC1_82b6PVeLCRL0"
                   "&msToken=ZnkvbvlZvtU9giXvO_9ncbROFBIi1kYd7sC-3fz8HCB2qPptfRkzHU66flI6jaa1HHLBObXkyPWaqcyKhiFfZ8CUtk_oseiEQJ-j4DAoCiFA1DoeEByYdlscnCIL-jH5w2_Z5tOoCt0UgIMmsBHRYCM-BoE4KnOBqzunR7kx7ySah3ZdBGav")

REAL_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
           "(KHTML, like Gecko) TraeCN/1.107.1 Chrome/142.0.7444.235 Electron/39.2.7 Safari/537.36")

REAL_BOGUS = ("xf0fDq6JYq55PpFtuCageb2RyHf/rB8yWZi/bnv7H5y1yhlbsh-3C3GWnoqN4NVDtWk9poVHGDzMYEVcp87TpCr"
              "kwmkkugkya05nnW6LZqNhPUs0DNDOezDzuXsC85Tq-/V9iAj62Ury1fn-irQg/d3S9KYe5YuhQ1OSk2uSi9Gh1M6ALZc1PQbdP7GqqD==")

COOKIES = {
    "gfkadpd": "361265,34425",
    "x-web-secsdk-uid": "01782dab-4ed0-4a0b-a977-75549220eb16",
    "s_v_web_id": "verify_mu0vpwkn_fTU5MUeX_YtKL_4iAv_8eC1_82b6PVeLCRL0",
    "__is_image_close": "0",
}
COOKIE_HEADER = "; ".join(f"{k}={v}" for k, v in COOKIES.items())


def request(name, url, use_cookie):
    headers = {
        "User-Agent": REAL_UA,
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://www.shidianguji.com/book/NA11023",
        "Accept-Language": "zh-CN,zh;q=0.9",
    }
    if use_cookie:
        headers["Cookie"] = COOKIE_HEADER
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(url, headers=headers)
    try:
        resp = urllib.request.urlopen(req, context=ctx, timeout=30)
        body = resp.read().decode("utf-8", "ignore")
        print(f"[{name}] status={resp.status} len={len(body)} body={body[:300]}")
    except Exception as e:
        print(f"[{name}] ERROR: {e}")


# 1. 真实 a_bogus，无 cookie
request("真实sig 无cookie", REAL_URL_NO_SIG + "&a_bogus=" + REAL_BOGUS, False)

# 2. 真实 a_bogus + cookie
request("真实sig 有cookie", REAL_URL_NO_SIG + "&a_bogus=" + REAL_BOGUS, True)

# 3. 本地 a_bogus + cookie：用真实 UA 和真实 URL 重新生成
r = subprocess.run(["node", "core/abogus_sign.js", REAL_URL_NO_SIG, REAL_UA],
                   capture_output=True, text=True, encoding="utf-8", timeout=60,
                   cwd="d:/study/trae/青竹小说-Windows")
out = json.loads(r.stdout)
if "error" in out:
    print("本地签名失败:", out["error"])
else:
    my_bogus = out["a_bogus"]
    print("本地 a_bogus len:", len(my_bogus))
    request("本地sig 有cookie", REAL_URL_NO_SIG + "&a_bogus=" + my_bogus, True)
