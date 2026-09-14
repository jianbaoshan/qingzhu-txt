# -*- coding: utf-8 -*-
"""测试：UA Chrome/126 + cookies 环境下签名请求。"""
import json
import ssl
import subprocess
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
cookies = {
    "gfkadpd": "361265,34425",
    "x-web-secsdk-uid": "01782dab-4ed0-4a0b-a977-75549220eb16",
    "s_v_web_id": "verify_mu0vpwkn_fTU5MUeX_YtKL_4iAv_8eC1_82b6PVeLCRL0",
    "__is_image_close": "0",
}
cookie_header = "; ".join(f"{k}={v}" for k, v in cookies.items())

fp = "verify_mu0vpwkn_fTU5MUeX_YtKL_4iAv_8eC1_82b6PVeLCRL0"
msToken = ("GiPRRd5QQbxsInX4olq9mg1HyHossuhiXr-WShJWgSHYBlwj3XzZ6qouLTxSKTYyMvvXwnLRLcJ3wIf7ABsC1Zoa9bYG8Pjp6vE2FgOfH4BXYfeTFTeFIb1lwHlTo72hVkp7IL0Ezz5Mzdy5OEssKCNh7q5ZD38A0K8M5l1FI8b_8bdDptjK")
url = ("https://www.shidianguji.com/api/ancientlib/read/reader-book/get/"
       "?bookId=NA11023&version=0&needCheckVersion=false&isWebpSupported=true"
       f"&verifyFp={fp}&fp={fp}&msToken={msToken}")

r = subprocess.run(["node", "core/abogus_sign.js", url, UA], capture_output=True, text=True,
                   encoding="utf-8", timeout=60)
out = json.loads(r.stdout)
if "error" in out:
    print("sign error:", out["error"])
    raise SystemExit(1)
bogus = out["a_bogus"]
print("a_bogus len:", len(bogus))

final_url = url + "&a_bogus=" + bogus
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
req = urllib.request.Request(final_url, headers={
    "User-Agent": UA,
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.shidianguji.com/book/NA11023",
    "Cookie": cookie_header,
})
resp = urllib.request.urlopen(req, context=ctx, timeout=30)
body = resp.read().decode("utf-8", "ignore")
print("status:", resp.status, "len:", len(body))
print("head:", body[:600])
