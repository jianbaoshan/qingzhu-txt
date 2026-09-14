# -*- coding: utf-8 -*-
"""反向解密 a_bogus：s4 自定义 base64 解码 + RC4 变体解密 + garble 3to4 还原 payload。"""
import base64

S4 = "Dkdpgh2ZmsQB80/MfvV36XI1R45-WUAlEixNLwoqYTOPuzKFjJnry79HbGcaStCe"

a_bogus = "QJ45kF7Lx2QnOp/bYKnatyKREyxArN8yqB4/RvxJHxz5yqUT-J3acfu6cozSsiQmGms5pq1HaEM/bEncpBUk3HnkompkSpwfeUVcnU8o2qw4GFJQLrjQCwvFFw0nUc4q-AVXiIhI2UtH6nVAwNQg/BlJS/ueQc8BPZO6kZzcE9s6Z0LAgZn3PQGkThib0G/t"


def s4_decode(s):
    # 标准 base64 逻辑，s4 表替换标准表
    std = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
    trans = str.maketrans(S4, std)
    padded = s + "=" * ((4 - len(s) % 4) % 4)
    return base64.b64decode(padded.translate(trans))


def rc4_variant_decrypt(key, data):
    # 反转 S-box + 非标准 KSA，PRGA 标准
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
    # 反向提取 4→3
    A, B, C, D, E, F = 145, 110, 66, 189, 44, 211
    out = bytearray()
    for i in range(0, len(data) - len(data) % 4, 4):
        a, b, c, d = data[i], data[i + 1], data[i + 2], data[i + 3]
        out.append((a & B) | (d & A))
        out.append((b & D) | (d & C))
        out.append((c & F) | (d & E))
    return bytes(out)


raw = s4_decode(a_bogus)
print("base64 decoded len:", len(raw))  # 应为 4 + rc4_out

# prefix = garble_2to4([3,82]) 前4字节；rc4_output = raw[4:]
rc4_out = raw[4:]
print("rc4_out len:", len(rc4_out))

dec = rc4_variant_decrypt(b"\xd3", rc4_out)
print("rc4 decrypted len:", len(dec))

# dec = version_garbled(8) + encrypted
version_garbled = dec[:8]
encrypted = dec[8:]
print("version_garbled:", list(version_garbled))
print("encrypted len:", len(encrypted))

payload = ungarble_3to4(encrypted)
print("payload len:", len(payload))
print("payload hex:", payload.hex())
print("payload bytes:", list(payload))
