"""HTTP 请求封装：UA 伪装、请求间隔、重试、超时处理。"""
import random
import time

import requests

from core.models import NetworkError, SiteBlockedError

UA_LIST = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
]


class HttpClient:
    """带反爬策略的 HTTP 客户端。"""

    def __init__(self, min_delay: float = 0.8, max_delay: float = 1.2, retries: int = 2):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.retries = retries
        self._last_request_time = 0.0
        self.session = requests.Session()

    def _random_ua(self) -> str:
        return random.choice(UA_LIST)

    def _respect_delay(self):
        """请求间隔控制，降低网站访问压力。"""
        elapsed = time.time() - self._last_request_time
        wait = random.uniform(self.min_delay, self.max_delay)
        if elapsed < wait:
            time.sleep(wait - elapsed)

    def get(self, url: str, params: dict | None = None, timeout: int = 20,
            encoding: str | None = None) -> requests.Response:
        """GET 请求，带重试。"""
        last_err: Exception | None = None
        for attempt in range(self.retries + 1):
            self._respect_delay()
            try:
                resp = self.session.get(
                    url, params=params, timeout=timeout,
                    headers={"User-Agent": self._random_ua(),
                             "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"},
                )
                if self._looks_like_challenge(resp):
                    raise SiteBlockedError("网站访问受限，请稍后重试")
                self._last_request_time = time.time()
                resp.raise_for_status()
                if encoding:
                    resp.encoding = encoding
                return resp
            except SiteBlockedError:
                raise
            except requests.RequestException as e:
                last_err = e
                self._last_request_time = time.time()
                time.sleep(1.5 * (attempt + 1))
        raise NetworkError(f"网络请求失败（已重试 {self.retries} 次）：{last_err}")

    def post(self, url: str, json_body: dict, timeout: int = 20,
             referer: str | None = None) -> requests.Response:
        """POST JSON 请求，带重试。"""
        last_err: Exception | None = None
        for attempt in range(self.retries + 1):
            self._respect_delay()
            try:
                headers = {"User-Agent": self._random_ua(),
                           "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                           "Content-Type": "application/json"}
                if referer:
                    headers["Referer"] = referer
                resp = self.session.post(url, json=json_body, headers=headers, timeout=timeout)
                if self._looks_like_challenge(resp):
                    raise SiteBlockedError("网站访问受限，请稍后重试")
                self._last_request_time = time.time()
                resp.raise_for_status()
                return resp
            except SiteBlockedError:
                raise
            except requests.RequestException as e:
                last_err = e
                self._last_request_time = time.time()
                time.sleep(1.5 * (attempt + 1))
        raise NetworkError(f"网络请求失败（已重试 {self.retries} 次）：{last_err}")

    @staticmethod
    def _looks_like_challenge(resp: requests.Response) -> bool:
        ct = resp.headers.get("Content-Type", "")
        if "html" not in ct:
            return False
        low = resp.text[:4000].lower()
        # Cloudflare / 反爬验证页面特征
        return ("challenge-platform" in low or "cf_chl" in low
                or "turnstile" in low or "just a moment" in low
                or "验证码" in low)
