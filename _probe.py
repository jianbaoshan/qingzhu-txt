import requests

cookies = {
    "gfkadpd": "361265,34425",
    "x-web-secsdk-uid": "01782dab-4ed0-4a0b-a977-75549220eb16",
    "s_v_web_id": "verify_mu0vpwkn_fTU5MUeX_YtKL_4iAv_8eC1_82b6PVeLCRL0",
    "__is_image_close": "0",
}
s = requests.Session()
s.cookies.update(cookies)
s.headers.update({
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"),
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.shidianguji.com/book/NA11023",
})

url = ("https://www.shidianguji.com/api/ancientlib/read/reader-book/get/"
       "?bookId=NA11023&version=0&needCheckVersion=false&isWebpSupported=true"
       "&verifyFp=verify_mu0vpwkn_fTU5MUeX_YtKL_4iAv_8eC1_82b6PVeLCRL0"
       "&fp=verify_mu0vpwkn_fTU5MUeX_YtKL_4iAv_8eC1_82b6PVeLCRL0"
       "&msToken=GiPRRd5QQbxsInX4olq9mg1HyHossuhiXr-WShJWgSHYBlwj3XzZ6qouLTxSKTYyMvvXwnLRLcJ3wIf7ABsC1Zoa9bYG8Pjp6vE2FgOfH4BXYfeTFTeFIb1lwHlTo72hVkp7IL0Ezz5Mzdy5OEssKCNh7q5ZD38A0K8M5l1FI8b_8bdDptjK"
       "&a_bogus=O64VkH6LO2%2FjCp%2FGmOrueea5CHg%2FNP8yhHiKWNfHCxLTyZebV7-3CpSLnoFx4xQYU8kVpF37GDz%2FYDVcZW7spHnkompvSg7blU5InX6LgqiXPl40LqDxezgzqXsCWRGqlA5AiAJIhUJ71nd-iqQL%2FpVCyKOFQQWh%2F1O6k2zSY9ahZ0yAg3n-PQbpTXTqSj%3D%3D")

r = s.get(url, timeout=20)
print("status:", r.status_code)
print(r.text[:500])
