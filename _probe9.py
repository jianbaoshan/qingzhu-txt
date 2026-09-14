# -*- coding: utf-8 -*-
"""定位 J 函数中 base64 blob 结尾，查看 J 剩余逻辑。"""
data = open("_entry_code.js", encoding="utf-8").read()
i = data.find('("', 4200)  # 找到 IIFE 调用处 (function(t){...})(" 的开引号
print("candidate open idx:", i)
i2 = data.find('"', 4112)  # base64 字符串开引号（在 J 内）
print("open idx:", i2)
# base64 中无引号，找到下一个引号即字符串结尾
j = data.find('"', i2 + 1)
print("close idx:", j)
print("--- after close (300 chars) ---")
print(data[j:j + 300])
