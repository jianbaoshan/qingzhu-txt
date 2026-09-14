# -*- coding: utf-8 -*-
"""对比真实浏览器 a_bogus 与本地生成 a_bogus 的解密 payload，找出差异字段。"""
import base64
import json
import subprocess

S4 = "Dkdpgh2ZmsQB80/MfvV36XI1R45-WUAlEixNLwoqYTOPuzKFjJnry79HbGcaStCe"

REAL_BOGUS = ("xf0fDq6JYq55PpFtuCageb2RyHf/rB8yWZi/bnv7H5y1yhlbsh-3C3GWnoqN4NVDtWk9poVHGDzMYEVcp87TpCr"
              "kwmkkugkya05nnW6LZqNhPUs0DNDOezDzuXsC85Tq-/V9iAj62Ury1fn-irQg/d3S9KYe5YuhQ1OSk2uSi9Gh1M6ALZc1PQbdP7GqqD==")

# 真实请求（不含 a_bogus）与 UA
REAL_URL = ("https://www.shidianguji.com/api/ancientlib/read/reader-book/get/"
            "?bookId=NA11023&version=0&needCheckVersion=false&isWebpSupported=true"
            "&verifyFp=verify_mu0vpwkn_fTU5MUeX_YtKL_4iAv_8eC1_82b6PVeLCRL0"
            "&fp=verify_mu0vpwkn_fTU5MUeX_YtKL_4iAv_8eC1_82b6PVeLCRL0"
            "&msToken=ZnkvbvlZvtU9giXvO_9ncbROFBIi1kYd7sC-3fz8HCB2qPptfRkzHU66flI6jaa1HHLBObXkyPWaqcyKhiFfZ8CUtk_oseiEQJ-j4DAoCiFA1DoeEByYdlscnCIL-jH5w2_Z5tOoCt0UgIMmsBHRYCM-BoE4KnOBqzunR7kx7ySah3ZdBGav")

REAL_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
           "(KHTML, like Gecko) TraeCN/1.107.1 Chrome/142.0.7444.235 Electron/39.2.7 Safari/537.36")


def s4_decode(s):
    std = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
    trans = str.maketrans(S4, std)
    padded = s + "=" * ((4 - len(s) % 4) % 4)
    return base64.b64decode(padded.translate(trans))


def rc4_variant_decrypt(key, data):
    S = list(range(255, -1, -1))
    j = 0
    kl = len(key)
    for i in range(256):
        j = (j * S[i] + j + key[i % kl]) % 256
        S[i], S[j] = S[j], S[i]
    out = bytearray()
    i = j = 0
    for b in data:
        i = (i + 1) % 256
        j = (j + S[i]) % 256
        S[i], S[j] = S[j], S[i]
        out.append(b ^ S[(S[i] + S[j]) % 256])
    return bytes(out)


def ungarble_3to4(data):
    A, B, C, D, E, F = 145, 110, 66, 189, 44, 211
    out = bytearray()
    for i in range(0, len(data) - len(data) % 4, 4):
        a, b, c, d = data[i], data[i + 1], data[i + 2], data[i + 3]
        out.append((a & B) | (d & A))
        out.append((b & D) | (d & C))
        out.append((c & F) | (d & E))
    return bytes(out)


def decrypt(bogus):
    raw = s4_decode(bogus)
    rc4_out = raw[4:]
    dec = rc4_variant_decrypt(b"\xd3", rc4_out)
    version_garbled = dec[:8]
    encrypted = dec[8:]
    payload = ungarble_3to4(encrypted)
    return version_garbled, payload


# 1. 解密真实 a_bogus
vg_real, payload_real = decrypt(REAL_BOGUS)
print("=== 真实 a_bogus ===")
print("bogus len:", len(REAL_BOGUS))
print("version_garbled:", list(vg_real))
print("payload len:", len(payload_real))
print("payload hex:", payload_real.hex())
print()

# 2. 用本地脚本对同一 URL + 真实 UA 生成 a_bogus
r = subprocess.run(["node", "core/abogus_sign.js", REAL_URL, REAL_UA],
                   capture_output=True, text=True, encoding="utf-8", timeout=60,
                   cwd="d:/study/trae/青竹小说-Windows")
out = json.loads(r.stdout)
if "error" in out:
    print("本地签名失败:", out["error"])
    raise SystemExit(1)
my_bogus = out["a_bogus"]
print("本地 a_bogus len:", len(my_bogus))

vg_mine, payload_mine = decrypt(my_bogus)
print("=== 本地 a_bogus ===")
print("version_garbled:", list(vg_mine))
print("payload len:", len(payload_mine))
print("payload hex:", payload_mine.hex())
print()

# 3. 逐字节对比 payload
print("=== payload 逐字节对比（. 相同，不同显示真实/本地 hex） ===")
maxlen = max(len(payload_real), len(payload_mine))
for i in range(maxlen):
    a = payload_real[i] if i < len(payload_real) else None
    b = payload_mine[i] if i < len(payload_mine) else None
    if a != b:
        print(f"offset {i:3d}: real={a:02x} mine={b} ")
print("(共", maxlen, "字节)")
