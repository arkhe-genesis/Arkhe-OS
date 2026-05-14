import time

class Substrato1RedisClone:
    def __init__(self):
        self.store = {}

    def set(self, key: str, value: str, ttl: int = None):
        """Sets a key-value pair with an optional TTL (in seconds)."""
        expires_at = time.time() + ttl if ttl is not None else None
        self.store[key] = {'value': value, 'expires_at': expires_at}

    def get(self, key: str) -> str:
        """Gets a value by key. Returns None if key doesn't exist or has expired."""
        if key in self.store:
            item = self.store[key]
            if item['expires_at'] is None or item['expires_at'] > time.time():
                return item['value']
            else:
                del self.store[key]  # Clean up expired key
        return None

    def delete(self, key: str):
        """Deletes a key-value pair."""
        if key in self.store:
            del self.store[key]

if __name__ == "__main__":
    redis_clone = Substrato1RedisClone()
    redis_clone.set("hello", "world")
    print(redis_clone.get("hello"))
    redis_clone.set("temp", "data", ttl=1)
    print(redis_clone.get("temp"))
    time.sleep(1.1)
    print(redis_clone.get("temp"))
