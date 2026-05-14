import time
import hashlib
from typing import Dict, Any

class Substrato9UrlShortener:
    BASE62 = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

    def __init__(self, base_url: str = "http://ark.he/"):
        self.base_url = base_url
        self.url_map: Dict[str, str] = {}
        # short_id -> analytics dict
        self.analytics: Dict[str, Dict[str, Any]] = {}
        self._counter = 1000  # Starting ID for encoding

    def _encode_base62(self, num: int) -> str:
        if num == 0:
            return self.BASE62[0]
        res = []
        base = len(self.BASE62)
        while num > 0:
            rem = num % base
            res.append(self.BASE62[rem])
            num //= base
        return "".join(reversed(res))

    def shorten(self, long_url: str) -> str:
        # Instead of just counter, we could use a hash. We'll use a simple counter for uniqueness.
        short_id = self._encode_base62(self._counter)
        self._counter += 1

        self.url_map[short_id] = long_url
        self.analytics[short_id] = {"clicks": 0, "last_accessed": None, "created_at": time.time()}

        return f"{self.base_url}{short_id}"

    def get_url(self, short_id: str) -> str:
        if short_id in self.url_map:
            # Track analytics
            self.analytics[short_id]["clicks"] += 1
            self.analytics[short_id]["last_accessed"] = time.time()
            return self.url_map[short_id]
        return None

    def get_analytics(self, short_id: str) -> Dict[str, Any]:
        return self.analytics.get(short_id)

if __name__ == "__main__":
    shortener = Substrato9UrlShortener()

    long_url = "https://www.example.com/some/very/long/path/to/resource"
    short_url = shortener.shorten(long_url)
    print(f"Shortened URL: {short_url}")

    # Extract ID from URL for lookup
    short_id = short_url.split("/")[-1]

    print(f"Original URL: {shortener.get_url(short_id)}")
    print(f"Original URL again: {shortener.get_url(short_id)}")

    print(f"Analytics: {shortener.get_analytics(short_id)}")
