# -*- coding: utf-8 -*-
"""分析 sdk_glue.js 结构：找入口函数、动态加载、关键字符串。"""
import re

text = open("_sdk_glue.js", encoding="utf-8").read()

# 找函数定义（minified 的顶层）
print("=== 顶层 function 定义 ===")
for m in re.finditer(r"(?:function\s+(\w+)|(\w+)\s*=\s*function)\s*\(", text[:8000]):
    print("  ", m.group(1) or m.group(2))

# 找字符串常量
print("\n=== 常见关键字符串 ===")
for kw in ["a_bogus", "sign", "X-Bogus", "verifyFp", "fp", "msToken", "secsdk",
           "bdms", "stable", "strategy", "runtime", "sdk", "collect", "report"]:
    cnt = text.count(kw)
    if cnt:
        idx = text.find(kw)
        print(f"  {kw}: {cnt} 次, 首次上下文: ...{text[max(0,idx-60):idx+80]}...")

# 找 URL
print("\n=== URL ===")
seen = set()
for m in re.finditer(r"https?://[^\"'\s\\]+", text):
    u = m.group(0)
    if u not in seen:
        seen.add(u)
        print("  ", u[:200])
