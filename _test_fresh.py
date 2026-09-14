# -*- coding: utf-8 -*-
"""用全新 fp/msToken 测试（排除过期参数因素）。"""
import json
import random
import ssl
import string
import subprocess
import urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"


def get_fp():
    e = list("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz")
    t = len(e)
    n = __import__("time").time().__str__()
    n = format(int(__import__("time").time() * 1000), "x")  # Date.now().toString(36)
    n = ""
    ms = int(__import__("time").time() * 1000)
    x = ms
    while x:
        n = "0123456789abcdefghijklmnopqrstuvwxyz"[x % 36] + n
        x //= 36
    r = [None] * 36
    r[8] = r[13] = r[18] = r[23] = "_"
    r[14] = "4"
    for o in range(36):
        if r[o] is None:
            i = int(random.random() * t)
            r[o] = e[3 & i | 8 if o == 19 else i]
    return "verify_" + n + "_" + "".join(r)


def get_ms_token(length=182):
    chars = string.ascii_letters + string.digits + "-_"
    return "".join(random.choice(chars) for _ in range(length))


fp = get_fp()
msToken = get_ms_token()
print("fp:", fp)
print("msToken len:", len(msToken))

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
})
resp = urllib.request.urlopen(req, context=ctx, timeout=30)
body = resp.read().decode("utf-8", "ignore")
print("status:", resp.status, "len:", len(body))
print("head:", body[:600])
