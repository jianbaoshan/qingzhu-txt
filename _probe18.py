# -*- coding: utf-8 -*-
import urllib.parse

a = "mj4jk76Jdq%2F5cpFbYccHtGNRayfMrN8ypBvdRfqJexF5yZtTPX3acvY%2FJowu4DdDtms5pq1HaE0AbxVcqlXk3erkFmpkSw76esK9nU6oZHE8TTih3quzKEbEuiTY0S4YuAAvE2vRlsMKIdOW9qCsApCHo%2FWhWti%2FMZPSp9ion6b%3D"
print("raw len:", len(a), "decoded len:", len(urllib.parse.unquote(a)))
